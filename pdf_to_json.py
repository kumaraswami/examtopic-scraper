import json
import re
import PyPDF2

def clean_text(text):
    # Remove any special characters and normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_questions_from_text(text):
    questions = []
    
    # Clean up the text first
    text = clean_text(text)
    print("Cleaned text sample:", text[:500])
    
    # Split text into question blocks using a more robust pattern
    question_blocks = re.split(r'Question\s+\d+:', text)[1:]  # Skip the first split as it's the header
    print(f"Found {len(question_blocks)} potential question blocks")
    
    for i, block in enumerate(question_blocks, 1):
        try:
            print(f"\nProcessing block {i}:")
            print(block[:200] + "...") # Print first 200 chars for debugging
            
            # Extract question text
            question_text = re.match(r'.*?(?=[A-F]\.)', block, re.DOTALL)
            if not question_text:
                print(f"Could not match question text in block {i}")
                continue
                
            question_text = clean_text(question_text.group(0))
            print(f"Found question text: {question_text[:100]}...")
            
            # Extract options
            options = []
            option_matches = re.finditer(r'([A-F]\..*?)(?=[A-F]\.|Answer:|$)', block, re.DOTALL)
            for match in option_matches:
                option = clean_text(match.group(1))
                options.append(option)
                print(f"Found option: {option[:50]}...")
            
            # Extract answer
            answer_match = re.search(r'Answer:\s*([A-F])', block)
            answer = answer_match.group(1) if answer_match else ''
            print(f"Found answer: {answer}")
            
            # Extract notes
            notes_match = re.search(r'Notes:\s*(.*?)(?=Question|$)', block, re.DOTALL)
            notes = clean_text(notes_match.group(1)) if notes_match else ''
            print(f"Found notes: {notes[:100]}...")
            
            questions.append({
                'question': question_text,
                'options': options,
                'answer': answer,
                'notes': notes
            })
            
        except Exception as e:
            print(f"Error processing question block {i}: {e}")
            continue
    
    return questions

def main():
    input_file = 'professional-cloud-architect-questions.pdf'
    output_json = 'questions.json'
    
    try:
        # Read the PDF content using PyPDF2
        print(f"Reading {input_file}...")
        with open(input_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        print("Extracting questions...")
        questions = extract_questions_from_text(text)
        
        # Save to JSON
        print(f"Saving {len(questions)} questions to {output_json}...")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully converted {len(questions)} questions to {output_json}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
