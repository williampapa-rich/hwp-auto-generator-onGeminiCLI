import sys
import json
from pdf_parser import extract_pdf_data
from llm_processor import process_text_to_json

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    
    print(f"1. Extracting data and images from {pdf_path}...")
    try:
        raw_text = extract_pdf_data(pdf_path, output_image_dir="./images")
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        sys.exit(1)
        
    print("2. Extracted text (Preview):")
    # 텍스트가 너무 길면 콘솔에 일부만 출력
    print(raw_text[:500] + "\n... (생략) ...\n")
    
    print("3. Sending text to LLM for structuring (This may take a few seconds)...")
    try:
        structured_data = process_text_to_json(raw_text)
    except Exception as e:
        print(f"Error during LLM processing: {e}")
        sys.exit(1)
        
    output_file = "result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
    print(f"4. Successfully saved structured data to {output_file}")
    print("Check the 'images' directory for extracted visual elements.")

if __name__ == "__main__":
    main()
