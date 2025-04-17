from pdf2image import convert_from_path
import pytesseract
import os

import re
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" 
pdf_path = "D:\\Projects\\nspc-voters-project\\input\\Anakapalli\\Narsipatnam\\booth_79.pdf"  # Update with your file path


def ocr_extract_text(pdf_path):
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=300, poppler_path= "C:\\Users\\chsat\\Documents\\poppler-24.08.0\\Library\\bin")
    # print(pages)
    extracted_pages_text = []
    
    for i, page_img in enumerate(pages[2:3]):
        text = pytesseract.image_to_string(page_img)
        extracted_pages_text.append(text)
        
        # Optional: Save each page image for verification
        page_img.save(f"page_{i+1}.png", "PNG")
    
    return extracted_pages_text

def save_ocr_output(ocr_text_list, output_dir="ocr_text_output"):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for i, page_text in enumerate(ocr_text_list, start=1):
        with open(os.path.join(output_dir, f"page_{i}.txt"), "w", encoding="utf-8") as f:
            f.write(page_text)
    
    print(f"Saved {len(ocr_text_list)} pages of OCR output in folder: {output_dir}")






ocr_pages_text = ocr_extract_text(pdf_path)
save_ocr_output(ocr_pages_text)

# Load text
with open("ocr_text_output\\page_1.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Phase 1: Split into blocks by 'Name' occurrences
blocks = re.split(r"\n\s*(?:Name\s*[:=+\s]+)", text, flags=re.IGNORECASE)[1:]  # skip the first split part

# Extract all voter codes beforehand
codes = re.findall(r"\b([A-Z0-9]{10})\b", text)

data = []

for block in blocks:
    block = block.strip()

    # Phase 2: extract fields from each block
    name = block.split('\n')[0].strip()  # first line after "Name" is the name
    house_match = re.search(r"House Number\s*[:=]\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
    house = house_match.group(1).replace("\n", " ").strip() if house_match else ""

    # Relative name: try all options
    relative_match = re.search(
        r"(Husbands Name|Fathers Name|Mothers Name|Others)[:=]\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
    relative = relative_match.group(2).strip() if relative_match else ""

    age_match = re.search(r"Age\s*[:=+\s]*?(\d+)", block, re.IGNORECASE)
    age = age_match.group(1) if age_match else ""

    gender_match = re.search(r"Gender\s*[:=+\s]*?(Male|Female)", block, re.IGNORECASE)
    gender = gender_match.group(1) if gender_match else ""

    # Find the nearest voter code after this block in the full text
    block_pos = text.find(block)
    nearest_code = None
    for code in codes:
        code_pos = text.find(code, block_pos)
        if code_pos > block_pos:
            nearest_code = code
            break

    data.append({
        "Name": name,
        "House Number": house,
        "Relative Name": relative,
        "Age": age,
        "Gender": gender,
        "VoterID": nearest_code if nearest_code else ""
    })

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("D:\\Projects\\nspc-voters-project\\parsed_voters_robust.csv", index=False)
print(f"Extracted {len(df)} records.")

