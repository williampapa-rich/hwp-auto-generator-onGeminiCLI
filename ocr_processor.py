import easyocr
import os

class OCRProcessor:
    def __init__(self, lang=['ko', 'en']):
        print(f"Initializing EasyOCR with languages: {lang}...")
        # gpu=False (맥북 환경에 따라 True로 변경 가능하지만 기본적으로 CPU 사용)
        self.reader = easyocr.Reader(lang, gpu=False)

    def extract_text_from_images(self, image_paths):
        """
        여러 이미지 경로를 받아 텍스트를 추출하고 합쳐서 반환합니다.
        """
        full_text = []
        for idx, img_path in enumerate(image_paths):
            print(f"OCR processing: {img_path}")
            # detail=0 은 텍스트만 리스트로 반환
            result = self.reader.readtext(img_path, detail=0)
            page_text = f"\n--- Page {idx+1} OCR Start ---\n"
            page_text += "\n".join(result)
            page_text += f"\n--- Page {idx+1} OCR End ---\n"
            full_text.append(page_text)
            
        return "\n".join(full_text)
