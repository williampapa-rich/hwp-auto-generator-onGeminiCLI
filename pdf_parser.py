import fitz
import os

def sort_blocks_2column(page):
    page_rect = page.rect
    center_x = page_rect.width / 2
    
    headers = []
    left_col = []
    right_col = []
    
    blocks = page.get_text("blocks")
    
    for b in blocks:
        x0, y0, x1, y1, text, block_no, block_type = b
        block_width = x1 - x0
        block_center_x = (x0 + x1) / 2
        
        # 1. Header/Footer filtering (occupies >80% width)
        if block_width > page_rect.width * 0.8:
            headers.append(b)
        # 2. Left/Right Column classification
        elif block_center_x < center_x:
            left_col.append(b)
        else:
            right_col.append(b)
            
    # Sort by y-axis (top-to-bottom)
    headers.sort(key=lambda b: b[1])
    left_col.sort(key=lambda b: b[1])
    right_col.sort(key=lambda b: b[1])
    
    # Merge for reading order
    return headers + left_col + right_col

def extract_pdf_data(pdf_path, output_image_dir="./images"):
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)
        
    doc = fitz.open(pdf_path)
    extracted_text_blocks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Sort blocks
        sorted_blocks = sort_blocks_2column(page)
        
        for b in sorted_blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            
            if block_type == 0:
                # Text block
                extracted_text_blocks.append(f"[Page {page_num+1}] {text.strip()}")
            elif block_type == 1:
                # Image block
                # Crop and save image
                rect = fitz.Rect(x0, y0, x1, y1)
                pix = page.get_pixmap(clip=rect)
                img_path = os.path.join(output_image_dir, f"page{page_num+1}_img_{block_no}.png")
                pix.save(img_path)
                
                extracted_text_blocks.append(f"[Page {page_num+1}] [이미지 첨부됨: {img_path}]")
                
    return "\n\n".join(extracted_text_blocks)
