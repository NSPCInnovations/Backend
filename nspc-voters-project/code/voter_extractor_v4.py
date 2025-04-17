import os
import cv2
import numpy as np
import pandas as pd
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re
import time

class VoterExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.debug_folder = "debug_images"
        os.makedirs(self.debug_folder, exist_ok=True)

    def process_voter_box(self, image, box, box_num):
        """Process a single voter box using simple approach"""
        x, y, w, h = box
        box_folder = os.path.join(self.debug_folder, f"box_{box_num}")
        os.makedirs(box_folder, exist_ok=True)
        
        # Extract and save original box
        box_image = image[y:y+h, x:x+w]
        cv2.imwrite(os.path.join(box_folder, "original_box.png"), box_image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(box_image, cv2.COLOR_BGR2GRAY)
        
        # Simple binary threshold
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Resize for better OCR
        resized = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(os.path.join(box_folder, "resized.png"), resized)
        
        # Extract age region (bottom 30% of image, but before 'Available' text)
        height = resized.shape[0]
        age_region = resized[int(height*0.6):int(height*0.85), :]  # Adjusted region
        cv2.imwrite(os.path.join(box_folder, "age_region.png"), age_region)
        
        # Get text with different PSM modes
        text_11 = pytesseract.image_to_string(resized, config='--oem 3 --psm 11')
        text_6 = pytesseract.image_to_string(resized, config='--oem 3 --psm 6')
        text_7 = pytesseract.image_to_string(age_region, config='--oem 3 --psm 7')
        
        # Save debug text
        with open(os.path.join(box_folder, "text_psm11.txt"), 'w') as f:
            f.write(text_11)
        with open(os.path.join(box_folder, "text_psm6.txt"), 'w') as f:
            f.write(text_6)
        with open(os.path.join(box_folder, "text_psm7.txt"), 'w') as f:
            f.write(text_7)
        
        # Parse information
        info = {
            'box_num': box_num,
            'voter_id': '',
            'name': '',
            'relation_type': '',
            'relative_name': '',
            'house_number': '',
            'age': '',
            'gender': ''
        }
        
        # Enhanced voter ID patterns
        voter_id_patterns = [
            r'([A-Z]{2,3}\s*\d{7,8})',  # With possible space
            r'([A-Z]{2,3}[A-Z0-9]\d{6,7})',  # With extra character
            r"[A-Z]{3}\d[^\w\s]\d{5}", #special characters handling
            r'([A-Z]{2,3}\d{7,8})'  # Standard format
        ]
        
        # Try to find voter ID in both PSM 11 and PSM 6
        for text in [text_11, text_6]:
            for pattern in voter_id_patterns:
                voter_id_match = re.search(pattern, text)
                if voter_id_match:
                    # Clean up the voter ID (remove spaces and normalize)
                    voter_id = voter_id_match.group(1).replace(" ", "")
                    # If it has an extra character after the prefix, handle it
                    if len(voter_id) > 10:
                        voter_id = voter_id[:3] + voter_id[4:]
                    info['voter_id'] = voter_id
                    break
            if info['voter_id']:
                break
        
        # Extract name (try both PSM 11 and PSM 6)
        for text in [text_6, text_11]:
            name_match = re.search(r'Name\s*:\s*([^\n]+)', text)
            if name_match:
                info['name'] = name_match.group(1).strip()
                break
        
        # Extract relation (try both PSM 6 and PSM 11)
        relation_patterns = [
            (r"Husband'?s?\s*Name\s*:\s*([^\n]+)", "Husband"),
            (r"Father'?s?\s*Name\s*:\s*([^\n]+)", "Father"),
            (r"Mother'?s?\s*Name\s*:\s*([^\n]+)", "Mother"),
            (r"Others?\s*:?\s*([^\n]+)", "Other")  # Added pattern for "Others"
        ]
        
        for text in [text_6, text_11]:
            for pattern, rel_type in relation_patterns:
                match = re.search(pattern, text)
                if match:
                    relative_name = match.group(1).strip()
                    # Clean up the relative name
                    relative_name = relative_name.replace('Photo', '').strip()
                    if relative_name:  # Only set if we have a name
                        info['relation_type'] = rel_type
                        info['relative_name'] = relative_name
                        break
            if info['relative_name']:
                break
        
        # Extract house number (try both PSM 6 and PSM 11)
        for text in [text_11, text_6]:  # Try PSM 11 first as it seems to handle multi-line better
            # First try to find the house number and all text until Age/Gender/Available
            house_match = re.search(r'House\s*Number\s*:\s*(.*?)(?=\s*(?:Age|Gender|Available))', text, re.DOTALL)
            if house_match:
                # Get all lines after "House Number:"
                house_text = house_match.group(1)
                
                # Clean up the text:
                # 1. Split into lines
                # 2. Remove 'Photo' and empty lines
                # 3. Join everything with spaces
                house_lines = [
                    line.strip()
                    for line in house_text.split('\n')
                    if line.strip() and 'Photo' not in line
                ]
                
                # Join all parts and clean up
                house_number = ' '.join(house_lines)
                
                # Additional cleanup
                house_number = (house_number
                              .replace('Flat Photo', 'Flat')  # Remove Photo if it's part of Flat
                              .replace('  ', ' ')  # Remove double spaces
                              .strip())
                
                # Only use if we have a meaningful address (more than just numbers/dots)
                if house_number and len(house_number) > 2 and not house_number.endswith('.'):
                    info['house_number'] = house_number
                    break
        
        # If we didn't get a good house number, try the simpler pattern
        if not info['house_number']:
            for text in [text_11, text_6]:
                house_match = re.search(r'House\s*Number\s*:\s*([^\n]+?)(?=\s*(?:Age|Gender|Photo|$))', text)
                if house_match:
                    house_number = house_match.group(1).strip()
                    if house_number and len(house_number) > 2 and not house_number.endswith('.'):
                        info['house_number'] = house_number
                        break
        
        # Extract age and gender (try PSM 7 first, then others)
        for text in [text_7, text_6, text_11]:
            # Try exact pattern first with very flexible matching
            age_gender_match = re.search(r'Age\s*[>:]?\s*(\d+).*?(?:Gender|Gander)\s*[>:]?\s*([MmFf][^\s\n]*)', text)
            if not age_gender_match:
                # Try separate patterns with more flexible matching
                age_match = re.search(r'Age\s*[>:]?\s*(\d+)', text)
                # Very flexible gender pattern
                gender_match = re.search(r'(?:Gender|Gander)\s*[>:]?\s*([MmFf][^\s\n]*)', text)
                
                if age_match:
                    age = age_match.group(1)
                    if age.isdigit() and 18 <= int(age) <= 120:
                        info['age'] = age
                
                if gender_match:
                    # Normalize gender text
                    gender = gender_match.group(1).strip().upper()
                    if gender.startswith('M'):
                        info['gender'] = 'Male'
                    elif gender.startswith('F'):
                        info['gender'] = 'Female'
                
                if info['age'] and info['gender']:
                    break
            else:
                age = age_gender_match.group(1)
                if age.isdigit() and 18 <= int(age) <= 120:
                    info['age'] = age
                    # Normalize gender text
                    gender = age_gender_match.group(2).strip().upper()
                    if gender.startswith('M'):
                        info['gender'] = 'Male'
                    elif gender.startswith('F'):
                        info['gender'] = 'Female'
                    break
        
        # If still no age/gender, try one more time with very flexible pattern
        if not info['age'] or not info['gender']:
            # Try all possible regions and PSM modes
            regions = [
                (resized, '--oem 3 --psm 6'),
                (resized, '--oem 3 --psm 11'),
                (age_region, '--oem 3 --psm 7'),
                (age_region, '--oem 3 --psm 6')
            ]
            
            for region, config in regions:
                text = pytesseract.image_to_string(region, config=config)
                
                # Try to find age if still missing
                if not info['age']:
                    age_match = re.search(r'\b(\d{2})\b', text)
                    if age_match:
                        age = age_match.group(1)
                        if age.isdigit() and 18 <= int(age) <= 120:
                            info['age'] = age
                
                # Try to find gender if still missing with very flexible pattern
                if not info['gender']:
                    # Look for any word containing 'male' or starting with M/F
                    gender_patterns = [
                        r'(?:Gender|Gander)\s*[>:]?\s*([MmFf][^\s\n]*)',  # Try to match full gender field first
                        r'\b(M[ae]le)\b',  # Match Male with variations
                        r'\b(F[ae]male)\b',  # Match Female with variations
                        r'\b([MmFf][^\s\n]*)\b'  # Last resort - any word starting with M/F
                    ]
                    
                    for pattern in gender_patterns:
                        gender_match = re.search(pattern, text, re.IGNORECASE)
                        if gender_match:
                            # Always use group 1 since all patterns now have capturing groups
                            gender = gender_match.group(1).strip().upper()
                            if gender.startswith('M') or 'MALE' in gender:
                                info['gender'] = 'Male'
                                break
                            elif gender.startswith('F') or 'FEMALE' in gender:
                                info['gender'] = 'Female'
                                break
                
                if info['age'] and info['gender']:
                    break
        
        return info

    def process_page(self, page_num=0):
        """Process a single page"""
        # Convert PDF to image
        pages = convert_from_path(self.pdf_path, dpi=300, poppler_path= "C:\\Users\\chsat\\Documents\\poppler-24.08.0\\Library\\bin")
        page = pages[page_num]
        
        # Convert to OpenCV format
        image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        
        # Detect boxes
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        voter_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 400 and h > 150 and 1.5 < w/h < 4:
                voter_boxes.append((x, y, w, h))
        
        # Sort boxes top to bottom
        # voter_boxes.sort(key=lambda x: x[1])
        
        # Process each box
        results = []
        for i, box in enumerate(voter_boxes, 1):
            info = self.process_voter_box(image, box, i)
            # Add page number to the info
            info['page_num'] = page_num + 1
            results.append(info)
        
        return pd.DataFrame(results)

    def process_all_pages(self):
        """Process all pages in the PDF"""
        # Convert PDF to images first to get total pages
        pages = convert_from_path(self.pdf_path, dpi=300, poppler_path= "C:\\Users\\chsat\\Documents\\poppler-24.08.0\\Library\\bin")
        total_pages = len(pages)
        
        # Process each page
        all_results = []
        for page_num in range(total_pages):
            start_time = time.time()
            print(f"\nProcessing page {page_num + 1} of {total_pages}...")
            df = self.process_page(page_num)
            
            # Save individual page results
            output_file = f"voter_data_page_{page_num + 1}.csv"
            df.to_csv(output_file, index=False)
            end_time = time.time()
            print(f"Saved {output_file}", f"Time Taken {end_time - start_time }")
            
            all_results.append(df)
        
        # Combine all results
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Save combined results
        combined_df.to_csv("voter_data_all.csv", index=False)
        print("\nSaved combined results to voter_data_all.csv")
        
        return combined_df

def main():
    pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" 
    extractor = VoterExtractor("D:\\Projects\\nspc-voters-project\\input\\Anakapalli\\Narsipatnam\\booth_79.pdf")
    
    # Process all pages
    df = extractor.process_all_pages()
    
    print("\nExtraction complete! First few records from combined data:")
    print(df.head())
    print(f"\nTotal records processed: {len(df)}")

if __name__ == "__main__":
    main() 