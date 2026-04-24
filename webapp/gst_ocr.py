import pytesseract
from PIL import Image
import re
from fuzzywuzzy import fuzz
import io, base64

# Path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Niraj.g\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'  # Update this path to where Tesseract is installed


def extract_gst_details(text):
    gst_details = {
        "GSTIN": None,
        "Legal_Name": None,
        "Trade_Name": None,
        "Registration_Date": None
    }

    # Regular expressions to match GST details
    gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b'
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'

    lines = text.split('\n')
    
    for line in lines:
        if not gst_details["GSTIN"]:
            gstin_match = re.search(gstin_pattern, line)
            if gstin_match:
                gst_details["GSTIN"] = gstin_match.group(0)
        
        if not gst_details["Registration_Date"]:
            date_match = re.search(date_pattern, line)
            if date_match:
                gst_details["Registration_Date"] = date_match.group(0)
        
        if not gst_details["Legal_Name"] and 'Legal Name' in line:
            parts = line.split(':')
            if len(parts) > 1:
                gst_details["Legal_Name"] = parts[1].strip()
        
        if not gst_details["Trade_Name"] and 'Trade Name' in line:
            parts = line.split(':')
            if len(parts) > 1:
                gst_details["Trade_Name"] = parts[1].strip()
    
    return gst_details

def process_gst_certificate(image_path):
    image = Image.open(image_path)

    # Convert image to string
    ocr_text = pytesseract.image_to_string(image)

    # Extract GST details
    gst_details = extract_gst_details(ocr_text)
    
    return gst_details