import csv
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import time
import json
import os

# Configuration
CSV_FILE = 'professional-cloud-architect.csv'
OUTPUT_PDF = 'professional-cloud-architect-questions.pdf'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

def safe_text(text):
    if not text: return ""
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Professional Cloud Architect Q&A', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 12)
        self.multi_cell(0, 10, safe_text(f'Question {num}: {label}'))
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, safe_text(body))
        self.ln()

    def chapter_options(self, options):
        self.set_font('Courier', '', 10)
        for opt in options:
            self.multi_cell(0, 5, safe_text(opt))
        self.ln()

    def chapter_answer(self, answer, notes=''):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, safe_text(f'Answer: {answer}'))
        self.ln()
        if notes:
            self.set_font('Arial', 'I', 10)
            self.multi_cell(0, 6, safe_text(f'Notes: {notes}'))
            self.ln()
        self.ln(10)

def fetch_question_data(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            print(f"Fetching {url}...")
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"Failed to retrieve {url}: Status {response.status_code}")
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Question
            question_body = soup.select_one('.question-body .card-text')
            if not question_body:
                print(f"Could not find question body for {url}")
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return None
            
            question_text = question_body.get_text(separator='\n', strip=True)
            
            # Extract Options
            options = []
            option_items = soup.select('.question-choices-container ul li')
            for item in option_items:
                # Clean up the text, finding the letter and the answer text
                letter_span = item.select_one('.multi-choice-letter')
                if letter_span:
                    letter = letter_span.get_text(strip=True)
                    # Remove the letter span to get the rest of the text
                    letter_span.decompose()
                    text = item.get_text(strip=True)
                    options.append(f"{letter} {text}")
                else:
                    options.append(item.get_text(strip=True))

            # Extract Answer and Community Votes
            suggested_answer = None
            community_answer = None
            vote_count = 0
            
            # Get suggested answer
            suggested_answer_span = soup.select_one('.correct-answer')
            if suggested_answer_span:
                suggested_answer = suggested_answer_span.get_text(strip=True)
            
            # Get community votes
            tally_script = soup.select_one('.voted-answers-tally script')
            if tally_script:
                try:
                    vote_data = json.loads(tally_script.string)
                    for vote in vote_data:
                        if vote.get('is_most_voted'):
                            community_answer = vote.get('voted_answers')
                            vote_count = vote.get('vote_count')
                            break
                except Exception as e:
                    print(f"Error parsing votes: {e}")

            # Use community answer if available and has votes, otherwise use suggested answer
            final_answer = community_answer if community_answer and vote_count > 0 else suggested_answer
            if not final_answer:
                final_answer = "N/A"

            # Create notes with both answers if they differ
            notes = []
            if suggested_answer and suggested_answer != "N/A":
                notes.append(f"Suggested Answer: {suggested_answer}")
            if community_answer and vote_count > 0:
                notes.append(f"Community Voted: {community_answer} ({vote_count} votes)")
            
            # Store both the answer and whether it's a multi-answer question
            is_multi_answer = len(final_answer) > 1 if final_answer != "N/A" else False

            return {
                'question': question_text,
                'options': options,
                'answer': final_answer,
                'is_multi_answer': is_multi_answer,
                'notes': ' | '.join(notes)
            }

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            return None
        
        finally:
            time.sleep(delay)  # Always wait between requests

def main():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Store questions for JSON
    questions = []
    count = 0
    error_count = 0
    max_errors = 5  # Maximum consecutive errors before stopping
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if it starts with 'Topic'
            header = next(reader, None)
            
            for row in reader:
                if len(row) < 3:
                    continue
                
                link = row[2]
                if not link.startswith('http'):
                    continue

                count += 1
                print(f"\nProcessing question {count}...")
                
                data = fetch_question_data(link)
                
                if data:
                    # Add to PDF
                    pdf.chapter_title(count, "Question")
                    pdf.chapter_body(data['question'])
                    pdf.chapter_options(data['options'])
                    pdf.chapter_answer(data['answer'], data['notes'])
                    
                    # Add to questions list for JSON
                    questions.append(data)
                    error_count = 0  # Reset error count on success
                else:
                    error_count += 1
                    print(f"Failed to fetch question {count}. Error count: {error_count}")
                    if error_count >= max_errors:
                        print(f"\nStopping after {max_errors} consecutive errors")
                        break
                
                # Save progress every 10 questions
                if count % 10 == 0:
                    print(f"\nSaving progress... {count} questions processed")
                    # Save JSON
                    with open('questions.json', 'w', encoding='utf-8') as f:
                        json.dump(questions, f, indent=2, ensure_ascii=False)
                    print("Progress saved")
                
    except KeyboardInterrupt:
        print("\nInterrupted! Saving partial progress...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Save PDF
        pdf.output(OUTPUT_PDF)
        print(f"PDF generated: {OUTPUT_PDF}")
        
        # Save JSON
        with open('questions.json', 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"JSON file generated: questions.json with {len(questions)} questions")

if __name__ == '__main__':
    main()
