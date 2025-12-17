import csv
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import time
import json
import os
import google.generativeai as genai

# Configuration
CSV_FILE = '/Users/kumaraswami.muthuswami/Downloads/professional-cloud-architect.csv'
OUTPUT_PDF = 'professional-cloud-architect-questions-ai.pdf'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

# AI Configuration
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. AI features will be disabled.")
else:
    genai.configure(api_key=API_KEY)

def safe_text(text):
    if not text: return ""
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Professional Cloud Architect Q&A (AI Enhanced)', 0, 1, 'C')
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
        self.ln(5)

    def chapter_ai_insight(self, ai_text):
        if not ai_text: return
        self.set_text_color(0, 0, 128) # Navy Blue
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, 'Gemini Insight:', 0, 1)
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50) # Dark Gray
        self.multi_cell(0, 6, safe_text(ai_text))
        self.set_text_color(0, 0, 0) # Reset to black
        self.ln(10)

def get_ai_answer(question, options):
    if not API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
You are a Google Cloud Certified Professional Cloud Architect expert.
Please analyze the following question and options:

Question: {question}

Options:
{chr(10).join(options)}

Provide the correct answer letter(s) and a concise technical explanation of why it is correct and why the others are incorrect.
Format as:
**Correct Answer:** [Letter]
**Explanation:** [Explanation]
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return f"AI Generation Failed: {e}"

def fetch_question_data(url):
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}: Status {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Question
        question_body = soup.select_one('.question-body .card-text')
        if not question_body:
            print(f"Could not find question body for {url}")
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

        # Extract Answer
        # Method 1: Suggested Answer
        suggested_answer_span = soup.select_one('.correct-answer')
        answer = suggested_answer_span.get_text(strip=True) if suggested_answer_span else "N/A"
        
        # Method 2: Community Vote
        vote_notes = ""
        tally_script = soup.select_one('.voted-answers-tally script')
        if tally_script:
            try:
                vote_data = json.loads(tally_script.string)
                for vote in vote_data:
                    if vote.get('is_most_voted'):
                        vote_notes = f"Community Voted: {vote.get('voted_answers')} ({vote.get('vote_count')} votes)"
            except Exception as e:
                print(f"Error parsing votes: {e}")

        return {
            'question': question_text,
            'options': options,
            'answer': answer,
            'notes': vote_notes
        }

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    count = 0
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            for row in reader:
                if len(row) < 3:
                    continue
                
                link = row[2]
                if not link.startswith('http'):
                    continue

                count += 1
                print(f"Processing Q{count}...")
                
                data = fetch_question_data(link)
                
                if data:
                    # Fetch AI Insight
                    print("  Asking Gemini...")
                    ai_insight = get_ai_answer(data['question'], data['options'])
                    
                    pdf.chapter_title(count, "Question")
                    pdf.chapter_body(data['question'])
                    pdf.chapter_options(data['options'])
                    pdf.chapter_answer(data['answer'], data['notes'])
                    pdf.chapter_ai_insight(ai_insight)
                
                # Sleep to be polite to the server and API limits
                time.sleep(2) 
    except KeyboardInterrupt:
        print("\nInterrupted! Saving partial PDF...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        pdf.output(OUTPUT_PDF)
        print(f"PDF generated: {OUTPUT_PDF}")

if __name__ == '__main__':
    main()
