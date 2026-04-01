import fitz
import os

def pdf_to_images(pdf_path, output_dir="./temp_images", dpi=300):
    """
    PDF 각 페이지를 고해상도 이미지로 변환하여 저장하고 경로 리스트를 반환합니다.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    doc = fitz.open(pdf_path)
    image_paths = []
    
    # DPI 설정 (기본 72에서 300으로 상향)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        
        img_path = os.path.join(output_dir, f"page_{page_num+1}.png")
        pix.save(img_path)
        image_paths.append(img_path)
        
    doc.close()
    return image_paths

# 기존의 sort_blocks_2column 등은 이제 필요 없으므로 유지하거나 제거 가능 (Vision 방식에서는 Gemini가 처리함)
