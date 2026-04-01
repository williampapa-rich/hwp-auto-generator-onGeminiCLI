import sys
import json
import os
import argparse
from pdf_parser import pdf_to_images
from llm_processor import process_images_to_json, process_text_to_json
from ocr_processor import OCRProcessor

def main():
    parser = argparse.ArgumentParser(description="Nova.ai Exam Parser CLI")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--mode", choices=["vision", "ocr"], default="vision", 
                        help="Parsing mode: 'vision' (Gemini Multimodal) or 'ocr' (EasyOCR + Gemini)")
    
    args = parser.parse_args()
    pdf_path = args.pdf_path
    mode = args.mode
    temp_dir = "./temp_images"
    
    print(f"--- 모드: {mode.upper()} ---")
    print(f"1. PDF 이미지 변환 중... ({pdf_path})")
    try:
        image_paths = pdf_to_images(pdf_path, output_dir=temp_dir, dpi=300)
        print(f"   - {len(image_paths)} 페이지 변환 완료.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    try:
        if mode == "vision":
            print("2. Gemini Multimodal (Vision) 분석 중...")
            structured_data = process_images_to_json(image_paths)
        else:
            print("2. EasyOCR 텍스트 추출 중 (모델 다운로드 포함 첫 실행 시 지연 가능)...")
            ocr = OCRProcessor()
            raw_text = ocr.extract_text_from_images(image_paths)
            print("3. 추출된 텍스트 Gemini로 구조화 중...")
            structured_data = process_text_to_json(raw_text)
            
        output_file = "result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ 성공적으로 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
