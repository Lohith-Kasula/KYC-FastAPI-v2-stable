# """
# AWS Rekognition - API Playground

#     Requirements:
#         1. AWS API Keys setup
#         2. pip install boto3
# """

# # Import necessary libraries
# from io import BytesIO
# import json
# from PIL import Image
# import boto3
# import os
# import random
# import time
# from tqdm import tqdm
# import base64
# import configparser

# # Load config variables
# config = configparser.ConfigParser()
# config.read("face_recognition.properties")


# def convert_to_bytes(src_image, target_image):
#     """Converts b64-image string to Bytes

#     Args:
#         src_image (str): base64-encoded string - Source image 
#         target_image (str): base64-encoded string - Target image

#     Returns:
#         src_imgBytes (byte) : Bytes object of source image 
#         target_imgBytes (byte) : Bytes object of target image 
#     """
#     src_imgBytes = base64.b64decode(src_image)
#     target_imgBytes = base64.b64decode(target_image)

#     return src_imgBytes, target_imgBytes


# def aws_compare_faces(source_img, target_img, extract_faces=None):
#     """AWS Rekognition - (Compare faces endpoint)

#     Args:
#         source_img (file): [description]
#         target_img ([type]): [description]

#     Returns:
#         [type]: [description]
#     """

#     # Create new Session with API keys
#     aws_access_key_id = config.get("AWSRekognition","ACCESS_KEY")
#     aws_secret_access_key = config.get("AWSRekognition","SECRET_KEY")
#     aws_region_name = config.get("AWSRekognition", "REGION") 
#     session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,region_name=aws_region_name) #profile_name='default'
    
#     # Convert source, target images to bytes
#     # pil_src_image = Image.open(source_img)
#     # pil_target_image = Image.open(target_img)

#     source_image_binary, target_image_binary = convert_to_bytes(source_img, target_img)
    
#     # Load AWS Rekognition client and call 'compare_faces' endpoint
#     s3_client = session.client('rekognition')

#     response = s3_client.compare_faces(
#         SourceImage={'Bytes': source_image_binary},
#         TargetImage = {'Bytes': target_image_binary}) 
  

    
#     # Dump response to JSON file
#     with open("aws_response_format.json","w") as infile:
#         json.dump(response, infile, indent=4)

#     # try:
        

#     if response['FaceMatches']:

#         if extract_faces:

#             face_b64_str = crop_faces(target_img,response['FaceMatches'][0]['Face'].get("BoundingBox"))

#             return True,response['FaceMatches'][0].get("Similarity"), face_b64_str

#         else:
#             # print(response['FaceMatches'][0].get("Confidence"))
#             return True,response['FaceMatches'][0].get("Similarity")

#     elif response['UnmatchedFaces']:

#         if extract_faces:
#             face_b64_str = crop_faces(target_img,response['UnmatchedFaces'][0].get("BoundingBox"))
            
#             return False, 100, face_b64_str
            
#         else:
#             return False, 100
            

        

#         # print("Saved response to json successfully")
        
#     # except Exception as e:
#     #     print(e)

#     return response


# def show_bbox(draw,coords,img_dimensions):
#     width, height= img_dimensions
#     left = width * coords['Left']
#     top = height * coords['Top']

#     draw.rectangle([left, top, left + (width * coords['Width']), top + (height * coords['Height'])])

# def crop_faces(target_image,coords):
    
#     target_image = Image.open(BytesIO(base64.b64decode(target_image)))

#      #old code 
#     #width, height= target_image.size
#     #left = width * coords['Left']
#     #top = height * coords['Top']

#     #new code
#     imgWidth, imgHeight= target_image.size
#     left = imgWidth * coords['Left']
#     top = imgHeight * coords['Top']
#     width = imgWidth * coords['Width']
#     height = imgHeight * coords['Height']

#     right = (left + width+40)
#     lower = (top + height+40)
#     # Crop Face bbox from target image - Eg: An Individual's face from Aadhar card image 
#     #target_image.crop([left, top, left + (width * coords['Width']), top + (height * coords['Height'])])
#     im_crop=target_image.crop((left-50,top-50,right,lower))
#     # Convert target image to Bytes
#     target_img_b4_buffer = BytesIO()
#     #target_image.save(target_img_b4_buffer, format=target_image.format)
#     im_crop.save(target_img_b4_buffer, format=target_image.format)

#     # Convert Bytes to Base64 encoded string
#     target_image_b64_str = base64.b64encode(target_img_b4_buffer.getvalue())

#     return target_image_b64_str


# def traverse_folders(root_dir, save_dir, start_index_root ,end_index_root, algo=None):
#     """

#     root_dir: Original image folder path
#     save_dir: path to dump results (.csv file)
#     algo : str 
#             Similarity or Dissimiliarity Algorithm

#     """

#     timeout_arr = list(range(0,6))

#     if algo == "similarity":
        
#         # root_dir = "../data/ATandT/"
#         # save_dir = "../data/Testing_set/v1"

#         final_res = {}

#         img_data = sorted(os.listdir(root_dir), key=len)[26:]

#         for subdirs in tqdm(img_data, desc="AWS Test Run #1"):
            
#             start_index = img_data.index(subdirs)
#             base_save_dir = os.path.join(root_dir,f"s{start_index+1}") 
            
#             res = sorted(os.listdir(base_save_dir),key=len)

#             subject_final_score = []

#             for idx in range(len(res)):
#                 for t_image in res:
#                     src_img = res[idx]
#                     src_img = os.path.join(base_save_dir, src_img)
#                     t_image = os.path.join(base_save_dir, t_image)

#                     # print(f"Source : {src_img} , Target : {t_image}")
                    
#                     aws_resp = aws_compare_faces(src_img, t_image)
#                     subject_final_score.append(aws_resp)

#                     time.sleep(random.choice(timeout_arr))

#             time.sleep(15)

#             final_res[f"s{start_index+1}"] = all(subject_final_score)

#         print(final_res)
        
#         with open(save_dir,"w") as infile:
#             json.dump(final_res, infile, indent=4)

#         return



#     if algo == "dissimilarity":


#         final_res = {}

#         if start_index_root == '':
#             img_data = sorted(os.listdir(root_dir), key=len)[:end_index_root]

#         if end_index_root == '':    
#             img_data = sorted(os.listdir(root_dir), key=len)[start_index_root:]

        
#         if start_index_root == "" and end_index_root == "":
#             img_data = sorted(os.listdir(root_dir), key=len)



#         for subdirs in tqdm(img_data, desc="AWS Test Run #2"):
            
#             start_index = img_data.index(subdirs)
#             base_save_dir = os.path.join(root_dir,f"s{start_index+1}") 
            
#             res = sorted(os.listdir(base_save_dir),key=len)
            
#             subject_final_score = []

#             for idx in range(len(res)):
#                 second_index = img_data.index(subdirs) + 1

#                 if start_index == len(img_data) -1 :

#                     with open(save_dir,"w") as infile:
#                         json.dump(final_res, infile, indent=4)


#                     return

#                 second_base_save_dir = os.path.join(root_dir,f"s{second_index+1}") 
                
#                 second_res = sorted(os.listdir(second_base_save_dir),key=len)

#                 for t_image in second_res:

#                     src_img = res[idx]
#                     src_img = os.path.join(base_save_dir, src_img)
#                     t_image = os.path.join(second_base_save_dir, t_image)

#                     # print(f"Source : {src_img} , Target : {t_image}")
                    
#                     aws_resp = aws_compare_faces(src_img, t_image)
#                     subject_final_score.append(aws_resp)

#                     time.sleep(random.choice(timeout_arr))

#             time.sleep(25)

#             final_res[f"s{start_index+1}"] = any(subject_final_score)

#         print(final_res)

#         with open(save_dir,"w") as infile:
#             json.dump(final_res, infile, indent=4)

#         return


#     return
    
"""
AWS Services - API Handler

    Requirements:
        1. AWS API Keys setup
        2. pip install boto3
"""

# Import necessary libraries
from io import BytesIO
import json
from PIL import Image
import boto3
import base64
import configparser
import re
from datetime import datetime
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List, Dict
from fuzzywuzzy import fuzz
from typing import Dict
# Load config variables
config = configparser.ConfigParser()
config.read("face_recognition.properties")

def convert_to_bytes(image):
    """Converts b64-image string to Bytes

    Args:
        image (str): base64-encoded string - Image

    Returns:
        imgBytes (byte) : Bytes object of image
    """
    imgBytes = base64.b64decode(image)
    return imgBytes

def aws_compare_faces(source_img, target_img, extract_faces=None):
    """AWS Rekognition - Compare Faces

    Args:
        source_img (str): Base64-encoded source image
        target_img (str): Base64-encoded target image

    Returns:
        (tuple): Comparison result, similarity score, and extracted face (if requested)
    """

    # Create new Session with API keys
    aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
    aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
    aws_region_name = config.get("AWSRekognition", "REGION")
    
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id, 
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region_name
    )

    # Convert source and target images to bytes
    source_image_binary = convert_to_bytes(source_img)
    target_image_binary = convert_to_bytes(target_img)
    
    # Load AWS Rekognition client and call 'compare_faces' endpoint
    rekognition_client = session.client('rekognition')

    response = rekognition_client.compare_faces(
        SourceImage={'Bytes': source_image_binary},
        TargetImage={'Bytes': target_image_binary}
    )

    # Write response to JSON file for inspection
    with open("aws_rekognition_response.json", "w") as infile:
        json.dump(response, infile, indent=4)

    if response['FaceMatches']:
        similarity = response['FaceMatches'][0].get("Similarity")

        if extract_faces:
            face_b64_str = crop_faces(target_img, response['FaceMatches'][0]['Face'].get("BoundingBox"))
            return True, similarity, face_b64_str
        else:
            return True, similarity

    elif response['UnmatchedFaces']:
        if extract_faces:
            face_b64_str = crop_faces(target_img, response['UnmatchedFaces'][0].get("BoundingBox"))
            return False, 100, face_b64_str
        else:
            return False, 100

    return response

def crop_faces(target_image, coords):
    """Crops face from the target image using bounding box coordinates

    Args:
        target_image (str): Base64-encoded target image
        coords (dict): Bounding box coordinates

    Returns:
        (str): Base64-encoded cropped face image
    """
    target_image = Image.open(BytesIO(base64.b64decode(target_image)))

    imgWidth, imgHeight = target_image.size
    left = imgWidth * coords['Left']
    top = imgHeight * coords['Top']
    width = imgWidth * coords['Width']
    height = imgHeight * coords['Height']

    right = (left + width + 40)
    lower = (top + height + 40)

    # Crop Face bbox from target image
    im_crop = target_image.crop((left - 50, top - 50, right, lower))

    # Convert target image to Bytes
    target_img_b4_buffer = BytesIO()
    im_crop.save(target_img_b4_buffer, format=target_image.format)

    # Convert Bytes to Base64 encoded string
    target_image_b64_str = base64.b64encode(target_img_b4_buffer.getvalue())

    return target_image_b64_str


# -----------------------------------------invoice------------------------
# AWS Textract configuration
# AWS Textract configuration
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")

textract_client = boto3.client(
    "textract",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)


def convert_to_bytes(image: str) -> bytes:
    """Converts a base64-encoded image string to bytes."""
    return base64.b64decode(image)
def aws_textract_document(document_img):
    """AWS Textract - Analyze Document for OCR

    Args:
        document_img (str): Base64 encoded image or PDF of the document

    Returns:
        response (dict): Parsed response from Textract containing extracted text
    """

    # Create new Session with API keys
    aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
    aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
    aws_region_name = config.get("AWSRekognition", "REGION")
    
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id, 
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region_name
    )

    # Convert document image to bytes
    document_image_binary = convert_to_bytes(document_img)
    
    # Load AWS Textract client and call 'analyze_document' endpoint
    textract_client = session.client('textract')

    response = textract_client.analyze_document(
        Document={'Bytes': document_image_binary},
        FeatureTypes=["TABLES", "FORMS"]
    )

    # Dump response to JSON file
    with open("aws_textract_response.json", "w") as infile:
        json.dump(response, infile, indent=4)

    return response
def extract_total_amount(full_text: str) -> str:
    """Extracts the numeric total amount from the invoice text."""
    # Prioritize extracting 'Invoice Value' first
    total_amount_patterns = [
        r"Invoice Value\s*[:?€]*\s*([\d,]+\.?\d*)",
        r"Total Amount After Tax\s*[%:?€]*\s*([\d,]+\.?\d*)",
        r"Grand Total\s*[%:?€]*\s*([\d,]+\.?\d*)",
        r"Total\s*[%:?€]*\s*([\d,]+\.?\d*)"
    ]

    for pattern in total_amount_patterns:
        match = re.findall(pattern, full_text, re.IGNORECASE)
        if match:
            return match[-1]  # Return the last match

    # Additional fallback: Check if the amount appears on the next line
    lines = full_text.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"Invoice Value|Total Amount After Tax|Total", line, re.IGNORECASE):
            # Try extracting a number from the next line
            if i + 1 < len(lines):
                next_line_match = re.search(r"([\d,]+\.?\d*)", lines[i + 1])
                if next_line_match:
                    return next_line_match.group(1)

    return "Not Found"

def extract_invoice_details(image_bytes: bytes) -> Dict[str, str]:
    """Extracts invoice details using AWS Textract."""
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["TABLES", "FORMS"]
    )

    # Initialize result dictionary
    extracted_data = {
        "VendorGSTIN": "",
        "BillToGSTIN": "",
        "InvoiceNumber": "",
        "InvoiceDate": "",
        "DueDate": "",
        "Table": [],
        "SubTotalAmount": "",
        "TotalAmount": ""
    }

    key_map = {}
    value_map = {}
    block_map = {}
    table_blocks = []

    # Prepare block maps
    for block in response["Blocks"]:
        block_id = block["Id"]
        block_map[block_id] = block
        if block["BlockType"] == "KEY_VALUE_SET":
            if "KEY" in block["EntityTypes"]:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
        elif block["BlockType"] == "TABLE":
            table_blocks.append(block)

    # Helper functions for key-value extraction
    def get_kv_relationship(key_block):
        for relationship in key_block.get("Relationships", []):
            if relationship["Type"] == "VALUE":
                for value_id in relationship["Ids"]:
                    return block_map.get(value_id)
        return None

    def get_text_for_block(block):
        text = ""
        for relationship in block.get("Relationships", []):
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    child = block_map.get(child_id, {})
                    if child.get("BlockType") == "WORD":
                        text += child.get("Text", "") + " "
        return text.strip()

    def match_key_to_field(key):
        key_aliases = {
            "invoice number": "InvoiceNumber",
            "invoice date": "InvoiceDate",
            "due date": "DueDate",
            "gstin": "VendorGSTIN",
            "sub-total": "SubTotalAmount",
            "subtotal": "SubTotalAmount",
            "total amount": "TotalAmount",
            "total": "TotalAmount",
        }
        key_lower = key.lower()
        for alias, field_name in key_aliases.items():
            if alias in key_lower:
                return field_name
        return None

    # Extract key-value pairs
    for key_block in key_map.values():
        value_block = get_kv_relationship(key_block)
        key = get_text_for_block(key_block)
        value = get_text_for_block(value_block) if value_block else ""
        matched_field = match_key_to_field(key)

        if matched_field:
            if matched_field == "VendorGSTIN" and extracted_data["VendorGSTIN"]:
                extracted_data["BillToGSTIN"] = value
            else:
                extracted_data[matched_field] = value

    # Extract tables
    def extract_table_data():
        table_data = []

        for table in table_blocks:
            rows = []
            for relationship in table.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    for cell_id in relationship["Ids"]:
                        cell = block_map[cell_id]
                        if cell["BlockType"] == "CELL":
                            row_idx = cell["RowIndex"] - 1
                            col_idx = cell["ColumnIndex"] - 1
                            cell_text = get_text_for_block(cell)

                            # Ensure rows and columns are properly aligned
                            while len(rows) <= row_idx:
                                rows.append([])
                            while len(rows[row_idx]) <= col_idx:
                                rows[row_idx].append("")

                            rows[row_idx][col_idx] = cell_text

            # Filter and structure the table rows
        #     if rows:
        #         for row in rows[1:]:  # Skip header row
        #             if len(row) >= 6 and row[0] and row[5]:  # Description and Amount exist
        #                 table_data.append({
        #                     "Description": row[0],
        #                     "Tax": row[4],
        #                     "Rate": row[5]
        #                 })
        # return table_data

            # Filter and structure the table rows
            if rows:
                for row in rows[1:]:  # Skip header row
                    print("row",row)
                    if len(row) >= 6 and row[0] and row[5]:  # Description and Amount exist
                        
                        description_0 = ''.join([char for char in (row[0] or '') if char.isalpha()])
                        description_1 = ''.join([char for char in (row[1] or '') if char.isalpha()])
            
                        # Combine both descriptions
                        combined_description = f"{description_0} {description_1}".strip()

                        # Filter out meaningless words or check for empty descriptions
                        if combined_description and not re.search(r'(item|description|amount)', combined_description, re.IGNORECASE):

                            table_data.append({
                                "Description": combined_description,  
                                "Tax": row[4],
                                "Rate": row[5]
                            })
        print("table_data", table_data)
        return table_data
        

    extracted_data["Table"] = extract_table_data()

    # Gather full text for regex matching
    full_text = " ".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
    print(full_text)
    # Extract GSTINs
    gstin_matches = re.findall(r"GSTIN\s*[:\s]*([A-Z0-9]+)", full_text)
    if len(gstin_matches) >= 2:
        extracted_data["VendorGSTIN"] = gstin_matches[0]
        extracted_data["BillToGSTIN"] = gstin_matches[1]
    elif len(gstin_matches) == 1:
        extracted_data["VendorGSTIN"] = gstin_matches[0]

    # # Extract Invoice Number
    # invoice_number_match = re.search(
    #     r"(?:Invoice\s*number|Bill)\s*[:\s]+([A-Za-z0-9/]+)", 
    #     r"Testinvoice\d+",
    #     full_text, 
    #     re.IGNORECASE
    # )
    # if invoice_number_match:
    #     invoice_number = invoice_number_match.group(1).strip()
    #     # Validate the extracted invoice number
    #     if re.match(r"^[A-Za-z0-9/]+$", invoice_number):
    #         extracted_data["InvoiceNumber"] = invoice_number
    #     else:
    #         extracted_data["InvoiceNumber"] = "Invalid Match"
    # else:
    #     # Fallback to find standalone "INV/..." pattern
    #     fallback_invoice_match = re.search(r"INV/\d{4}/\d+", full_text)
    #     if fallback_invoice_match:
    #         extracted_data["InvoiceNumber"] = fallback_invoice_match.group(0)
    #     else:
    #         # Extract Invoice Number
    #         invoice_number_match = re.search(
    #             r"Invoice No\.\s*[:\s]*([A-Za-z0-9/ -]+)", full_text, re.IGNORECASE
    #         )
    #         if invoice_number_match:
    #             extracted_data["InvoiceNumber"] = re.sub(r"Invoice Date.*", "", invoice_number_match.group(1)).strip()
    #         else:
    #             extracted_data["InvoiceNumber"] = "Not Found"

    # # New Regex for capturing patterns like D271124-5625566
    # invoice_number_special_match = re.search(r"\b[D]\d{6}-\d{7}\b", full_text)
    # if invoice_number_special_match:
    #     extracted_data["InvoiceNumber"] = invoice_number_special_match.group(0)

    # # If "InvoiceNumber" is found, remove "Place Of Supply" if it follows the invoice number
    # if "InvoiceNumber" in extracted_data:
    #     invoice_number = extracted_data["InvoiceNumber"]
    #     # Remove "Place Of Supply" if it follows the invoice number
    #     updated_invoice_number = re.sub(r"(\b[A-Za-z0-9]{6,}-\d{7}\b)\s*Place\s*Of\s*Supply", r"\1", invoice_number)
    #     extracted_data["InvoiceNumber"] = updated_invoice_number

    # **Fixing Invoice Number Extraction**
    invoice_number_match = re.search(r"Testinvoice\d+", full_text, re.IGNORECASE)
    if invoice_number_match:
        extracted_data["InvoiceNumber"] = invoice_number_match.group(0)
    else:
        invoice_number_match = re.search(r"(?:Invoice\s*number|Bill)\s*[:\s]+([A-Za-z0-9/]+)", full_text, re.IGNORECASE)
        if invoice_number_match:
            extracted_data["InvoiceNumber"] = invoice_number_match.group(1).strip()
        else:
            fallback_invoice_match = re.search(r"INV/\d{4}/\d+", full_text, re.IGNORECASE)
            if fallback_invoice_match:
                extracted_data["InvoiceNumber"] = fallback_invoice_match.group(0)
            else:
                invoice_number_match = re.search(r"Invoice No\.\s*[:\s]*([A-Za-z0-9/ -]+)", full_text, re.IGNORECASE)
                if invoice_number_match:
                    extracted_data["InvoiceNumber"] = re.sub(r"Invoice Date.*", "", invoice_number_match.group(1)).strip()
                else:
                    extracted_data["InvoiceNumber"] = "Not Found"

    # Check for patterns like D271124-5625566
    invoice_number_special_match = re.search(r"\b[D]\d{6}-\d{7}\b", full_text)
    if invoice_number_special_match:
        extracted_data["InvoiceNumber"] = invoice_number_special_match.group(0)

    # If "Place Of Supply" follows invoice number, remove it
    if extracted_data["InvoiceNumber"]:
        extracted_data["InvoiceNumber"] = re.sub(
            r"(\b[A-Za-z0-9]{6,}-\d{7}\b)\s*Place\s*Of\s*Supply", 
            r"\1", 
            extracted_data["InvoiceNumber"]
        )
        
    # Extract Dates (Invoice Date and Due Date)
    date_matches = re.findall(r"(\d{2}/\d{2}/\d{4})", full_text)
    if len(date_matches) >= 2:
        extracted_data["InvoiceDate"] = date_matches[0]
        extracted_data["DueDate"] = date_matches[1]
    elif len(date_matches) == 1:
        extracted_data["InvoiceDate"] = date_matches[0]

    # Validate required fields
    required_fields = ["VendorGSTIN", "TotalAmount"]
    missing_fields = [field for field in required_fields if not extracted_data[field]]

    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        return {"Error": error_message}
    
    full_text = " ".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
    extracted_data["TotalAmount"] = extract_total_amount(full_text)

    return extracted_data


import boto3


def extract_gst_certificate_data(response):
    """
    Extracts GST certificate data from Textract response.

    Args:
        response (dict): Textract response.

    Returns:
        extracted_data (dict): Extracted key-value pairs and table data from GST certificate.
    """
    extracted_data = {
        "Registration Number": "",
        "Legal Name": "",
        "Trade Name": "",
        "Address": "",
        "Type of Registration": "",
        "Date of Liability": ""
    }

    key_map = {}
    value_map = {}
    block_map = {}
    table_blocks = []

    # Prepare the block map
    for block in response['Blocks']:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
        elif block['BlockType'] == 'TABLE':
            table_blocks.append(block)

    # Find the value block corresponding to a key block
    def get_kv_relationship(key_block):
        value_block = None
        if 'Relationships' in key_block:
            for relationship in key_block['Relationships']:
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        value_block = block_map[value_id]
        return value_block

    # Get text for the key or value block
    def get_text_for_block(block):
        text = ""
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        word = block_map[child_id]
                        if word['BlockType'] == 'WORD':
                            text += word['Text'] + " "
                        elif word['BlockType'] == 'SELECTION_ELEMENT' and word['SelectionStatus'] == 'SELECTED':
                            text += 'SELECTED '
        return text.strip()

    # Extract key-value pairs
    for key_block in key_map.values():
        value_block = get_kv_relationship(key_block)
        key = get_text_for_block(key_block).lower()
        value = get_text_for_block(value_block)

        if 'gstin' in key or 'registration number' in key:
            extracted_data['Registration Number'] = value
        elif 'legal name' in key:
            extracted_data['Legal Name'] = value
        elif 'trade name' in key:
            extracted_data['Trade Name'] = value
        elif 'address' in key:
            extracted_data['Address'] = value
        elif 'type of registration' in key:
            extracted_data['Type of Registration'] = value
        elif 'date of liability' in key:
            extracted_data['Date of Liability'] = value

    # Check if required fields are missing
    missing_fields = [field for field, value in extracted_data.items() if not value]
    if missing_fields:
        return {
            "error": "Could not process this image - required information not found.",
            "missing_fields": missing_fields
        }

    return extracted_data


# AWS session setup
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")

session = boto3.Session(
    aws_access_key_id=aws_access_key_id, 
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)
textract_client = session.client('textract')

# Function to extract text from image using AWS Textract
def extract_text_from_textract(image_bytes):
    response = textract_client.analyze_document(
        Document={'Bytes': image_bytes},
        FeatureTypes=['FORMS']  # We are using 'FORMS' to extract key-value pairs
    )
    return response

# # Load AWS credential
# aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
# aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
# aws_region_name = config.get("AWSRekognition", "REGION")

# # Initialize AWS Textract client
# textract_client = boto3.client(
#     "textract",
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     region_name=aws_region_name
# )

def extract_udyam_details(image_bytes: bytes) -> Dict[str, str]:
    # Call Textract to analyze the document
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["TABLES"]
    )

    # Initialize result dictionary to store extracted fields
    result = {
        "Udyam_Registration_Number": "",
        "Name_of_Enterprise": "",
        "Type_of_Enterprise": "",
        "Major_Activity": "",
        "Date_of_Udyam_Registration": "",
        "Social_Category": "",
        "Date_of_Incorporation": "",
        "Date_of_Commencement": "",
        "Official_Address": {},
        "NIC_Codes": [],
        "Average_Confidence": 0.0
    }

    # Extract confidence scores for average calculation
    confidences = [block["Confidence"] for block in response["Blocks"] if "Confidence" in block]
    result["Average_Confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

    # Gather all detected text in one string for regex matching
    full_text = " ".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
    
    # Debugging: Print the full_text to understand how Textract captures the content
    print("Extracted Full Text:")
    print(full_text)

    # Define regex patterns for specific fields
    patterns = {
        "Udyam_Registration_Number": r"UDYAM REGISTRATION NUMBER\s+([A-Z0-9-]+)",
        # r"([A-Z0-9-]+)\s+UDYAM REGISTRATION NUMBER"
        "Name_of_Enterprise": r"NAME OF ENTERPRISE\s+([A-Z\s/.,&]+)(?=\s*SNo\.)",
        "Type_of_Enterprise": r"TYPE OF ENTERPRISE\s+\d+\s+\d{4}-\d{2}\s+(\w+)",
        "Major_Activity": r"MAJOR ACTIVITY\s*\[?([A-Za-z\s]+)\]?",
        "Date_of_Udyam_Registration": r"DATE OF UDYAM REGISTRATION\s+([0-9/]+)", 
        "Social_Category": r"SOCIAL CATEGORY OF\s+([A-Z]+)",
        "Date_of_Incorporation": r"DATE OF INCORPORATION\s*(?:/)?\s*([0-9/]+)",  # Allows slash or no slash
        "Date_of_Commencement": r"DATE OF COMMENCEMENT OF(?:\s+(?:PRODUCTION\/BUSINESS))?\s*(?:/)?\s*([0-9/]+)" ,
        "Official_Address": r"Flat\/Door\/?Block\s*(?:No\.)?\s*([^\n]+(?:\s+[A-Za-z\s,]+)+)"
    }
    match = re.search(patterns["Name_of_Enterprise"], full_text, re.IGNORECASE)
    if match:
        result["Name_of_Enterprise"] = match.group(1).strip()

    # If the old pattern doesn't match, try the new pattern
    if not result["Name_of_Enterprise"]:
        match = re.search(r"NAME OF ENTERPRISE\s+([A-Z\s/.,&]+)", full_text, re.IGNORECASE)  # New pattern
        if match:
            result["Name_of_Enterprise"] = match.group(1).strip()

    # Logic to extract other fields using the existing regex patterns
    for key, pattern in patterns.items():
        if key != "Name_of_Enterprise":  # Skip Name_of_Enterprise as it is handled separately
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()
    # Use regex to extract each field
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip() if key != "Official_Address" else extract_address_details(match.group(1).strip())

    # Logic for extracting "Type_of_Enterprise" based on keywords
    type_of_enterprise = None
    if "Micro" in full_text:
        type_of_enterprise = "Micro"
    elif "Small" in full_text:
        type_of_enterprise = "Small"
    elif "Medium" in full_text:
        type_of_enterprise = "Medium"
    result["Type_of_Enterprise"] = type_of_enterprise

    # Logic for extracting "Major_Activity" based on keywords
    major_activity = None
    before_pattern = r"(SERVICES|MANUFACTURING|TRADING)\s+MAJOR\s+ACTIVITY"
    match = re.search(before_pattern, full_text, re.IGNORECASE)
    if match:
        major_activity = match.group(1).title()

    # Pattern 2: Activity comes after "MAJOR ACTIVITY"
    if not major_activity:  # Only check if not already found
        after_pattern = r"MAJOR\s+ACTIVITY\s+(SERVICES|MANUFACTURING|TRADING)"
        match = re.search(after_pattern, full_text, re.IGNORECASE)
        if match:
            major_activity = match.group(1).title()

    result["Major_Activity"] = major_activity

    # Logic for extracting "Social_Category" based on keywords
    social_category_match = re.search(r"SOCIAL CATEGORY OF\s*(General|OBC|SC|ST)", full_text, re.IGNORECASE)
    social_category = social_category_match.group(1).strip() if social_category_match else None
    result["Social_Category"] = social_category

   #all value are getting empty then giving error
    if not result["Udyam_Registration_Number"]  :
        return {"message": "Could not process the  input file"}


    # Extract NIC codes from table data
    table_data = parse_textract_tables(response)
    result["NIC_Codes"] = parse_nic_codes(table_data)

    return result



def extract_address_details(full_address_text: str) -> Dict[str, str]:
    # Initialize a dictionary with keys for each address component
    address_details = {
        "Flat_No": None,
        "Name_of_Building": None,
        "Road_Street_Lane": None,
        "Village": None,
        "City": None,
        "State": None,
        "District": None,
        "Pin": None,
        "Mobile": None,
        "Email": None
    }
    
    # Define regex patterns for address components
    patterns = {
        "Flat_No": r"(Flat|Door|Block|FF|UNIT|No|UNIT NO|Block No.\.?)\s*(No\.?\s)?([A-Za-z0-9\-\/]+)",
        "Name_of_Building": r"(Building|Name of Premises|GROUND FLOOR|Premises/)\s*([A-Za-z0-9\s\-]+)",
        "Village": r"Village/Town\s+([A-Za-z0-9\s,]+)",  # Adjusted for unwanted parts
        "City": r"City\s+(.*?)\s+(State|District|Pin)",
        "State": r"State\s+(.*?)\s+(District|Pin)",
        "District": r"District\s+([A-Z\s]+?)[,.\s]+Pin",
        "Pin": r"Pin\s+(\d+)",
        "Mobile": r"Mobile\s+(\d+)",
        "Email": r"Email[:\s]+([\w.-]+@[\w.-]+\.\w+)"
    }

    # Handle Road/Street/Lane or Road/Street/Lase
    if "Road/Street/Lane" in full_address_text or "Road/Street/Lase" in full_address_text:
        # Check if the value comes before the key (e.g., "SOHNA Road/Street/Lane City")
        value_before_key_pattern = r"([A-Za-z0-9\s]+)\s+(Road\/Street\/Lane|Road\/Street\/Lase)\s+City"
        match = re.search(value_before_key_pattern, full_address_text, re.IGNORECASE)
        if match:
            # If value comes before key, extract the value
            address_details["Road_Street_Lane"] = match.group(1).strip()
        else:
            # Otherwise, use the original pattern (key before value)
            if "Road/Street/Lane" in full_address_text:
                patterns["Road_Street_Lane"] = r"Road\/Street\/Lane\s+(.*?)\s+City"
            elif "Road/Street/Lase" in full_address_text:
                patterns["Road_Street_Lane"] = r"Road\/Street\/Lase\s+(.*?)\s+City"

            # Apply the pattern and check if it matches
            match = re.search(patterns["Road_Street_Lane"], full_address_text, re.IGNORECASE)
            if match:
                address_details["Road_Street_Lane"] = match.group(1).strip()

    # Apply regex patterns and store matches in the dictionary
    for field, pattern in patterns.items():
        if field == "Road_Street_Lane" and address_details["Road_Street_Lane"]:
            continue  # Skip if already extracted
        match = re.search(pattern, full_address_text, flags=re.IGNORECASE)
        if match:
            if field == "Flat_No":
                # Use the full match for flat number
                address_details[field] = match.group(0).strip()
            elif field == "Village":
                # Use the first group for village name
                address_details[field] = match.group(1).strip()
            elif field == "Name_of_Building":
                # Use the second group for building name
                address_details[field] = match.group(2).strip()
            else:
                # Use the first group for all other fields
                address_details[field] = match.group(1).strip()

    # Post-process the extracted fields
    if address_details["Name_of_Building"]:
        # Remove duplicate words like "Village"
        address_details["Name_of_Building"] = " ".join(
            sorted(set(address_details["Name_of_Building"].split()), key=address_details["Name_of_Building"].split().index)
        )

    # Clean up the Road_Street_Lane field
    if address_details["Road_Street_Lane"]:
        # Remove unwanted parts like "Town Block SECTOR 49 ITECH PARK OFFICAL ADDRESS OF ENTERPRISE"
        address_details["Road_Street_Lane"] = re.sub(
            r"Town Block SECTOR \d+ ITECH PARK OFFICAL ADDRESS OF ENTERPRISE",
            "",
            address_details["Road_Street_Lane"],
            flags=re.IGNORECASE
        ).strip()

    # Clean up the Village field
    if address_details["Village"]:
        # Remove unwanted parts like "OFFICAL ADDRESS OF ENTERPRISE SOHNA Road"
        address_details["Village"] = re.sub(
            r"OFFICAL ADDRESS OF ENTERPRISE SOHNA Road",
            "",
            address_details["Village"],
            flags=re.IGNORECASE
        ).strip()

    for field in ["City", "State", "District"]:
        if address_details[field]:
            address_details[field] = re.sub(r"\b(State|District|Pin)\b", "", address_details[field], flags=re.IGNORECASE).strip()
            address_details[field] = " ".join(sorted(set(address_details[field].split()), key=address_details[field].split().index))

    if address_details["Village"]:
        address_details["Village"] = re.sub(r"(Block\s+\w+|Sector\s+\d+|OFFICAL ADDRESS OF ENTERPRISE Road|,)", "", address_details["Village"], flags=re.IGNORECASE).strip()

    return address_details

# def extract_address_details(address: str) -> Dict[str, str]:
#     """
#     Extract components from the Official Address string into structured fields.
#     """
#     patterns = {
#         "Flat_Door_Block_No": r"Flat/Door/Block No\.\s*([^\n]+)",
#         "Name_of_Premises_Building": r"Name of Premises/Building\s*([^\n]+)",
#         "Road_Street_Lane": r"Road/Street/Lane\s*([^\n]+)",
#         "City": r"City\s*([A-Za-z\s]+)",
#         "State": r"State\s*([A-Za-z\s]+)",
#         "District": r"District\s*([A-Za-z\s]+)",
#         "Pin": r"Pin\s*(\d+)",
#         "Mobile": r"Mobile\s*(\d+)",
#         "Email": r"Email:\s*([\w.-]+@[\w.-]+\.\w+)"
#     }

#     address_details = {}
#     for key, pattern in patterns.items():
#         match = re.search(pattern, address, re.IGNORECASE)
#         if match:
#             address_details[key] = match.group(1).strip()
#             print(f"Extracted {key}: {address_details[key]}")  # Debug print

#     # Cleanup for concatenated or misplaced values
#     for field in ["City", "State", "District"]:
#         if field in address_details:
#             # Remove redundant keywords and extra spaces
#             address_details[field] = re.sub(r"\b(State|District|Pin)\b", "", address_details[field], flags=re.IGNORECASE).strip()
#             # Remove duplicate words
#             address_details[field] = " ".join(sorted(set(address_details[field].split()), key=address_details[field].split().index))

#     print("Final Address Details:", address_details)  # Debug print for final output
#     return address_details

def parse_textract_tables(response) -> List[List[str]]:
    """
    Parse table data from AWS Textract response.
    """
    blocks = response['Blocks']
    table_data = []
    rows = {}

    # Extract text from each cell and organize into a table structure
    for block in blocks:
        if block["BlockType"] == "CELL":
            row_index = block["RowIndex"]
            column_index = block["ColumnIndex"]
            text = ""
            if "Relationships" in block:
                for relation in block["Relationships"]:
                    if relation["Type"] == "CHILD":
                        for id in relation["Ids"]:
                            child_block = next((b for b in blocks if b["Id"] == id), None)
                            if child_block and "Text" in child_block:
                                text += child_block["Text"] + " "

            # Organize cells by rows
            if row_index not in rows:
                rows[row_index] = {}
            rows[row_index][column_index] = text.strip()

    # Convert rows dictionary to a sorted list for easier parsing
    for row_index in sorted(rows.keys()):
        row = [rows[row_index].get(col_index, "") for col_index in sorted(rows[row_index].keys())]
        table_data.append(row)

    return table_data

def parse_nic_codes(table_data: List[List[str]]) -> List[Dict[str, str]]:
    """
    Extract NIC codes from the structured table data and separate numeric IDs and descriptions.
    """
    nic_codes = []

    for row in table_data:
        if len(row) >= 5:  # Ensure sufficient columns exist
            # Extract NIC text and numeric parts
            nic_2_text = row[1].strip()
            nic_4_text = row[2].strip()
            nic_5_text = row[3].strip()
            activity = row[4].strip()

            nic_2_id = re.match(r"^\d+", nic_2_text).group(0) if re.match(r"^\d+", nic_2_text) else ""
            nic_4_id = re.match(r"^\d+", nic_4_text).group(0) if re.match(r"^\d+", nic_4_text) else ""
            nic_5_id = re.match(r"^\d+", nic_5_text).group(0) if re.match(r"^\d+", nic_5_text) else ""

            if nic_2_id and nic_4_id and nic_5_id:  # Only add valid NIC codes
                nic_codes.append({
                    "NIC 2 ID": nic_2_id,
                    "NIC 4 ID": nic_4_id,
                    "NIC 5 ID": nic_5_id,
                    "NIC 2 Text": nic_2_text,
                    "NIC 4 Text": nic_4_text,
                    "NIC 5 Text": nic_5_text,
                    "activity": activity
                })

    return nic_codes
# def parse_nic_codes(table_data: List[List[str]]) -> List[Dict[str, str]]:
#     """
#     Parse NIC codes from table data by directly matching expected columns.
#     """
#     nic_codes = []

#     for row in table_data:
#         # Check if row contains valid NIC data, identified by a numeric SNo in the first column
#         if row and row[0].isdigit():
#             # Ensure the row has enough columns to contain NIC details
#             # if len(row) >= 5:
#                 # nic_codes.append({
#                 #     # "NIC 2 Digit": row[1].strip(),
#                 #     # "NIC 4 Digit": row[2].strip(),
#                 #     # "NIC 5 Digit": row[3].strip(),
#                 #     # "Activity": row[4].strip()
#                 # })
#             if len(row) >= 5:
#                 # Extract only numeric part from NIC codes
#                 nic_2_id = ''.join(filter(str.isdigit, row[1]))
#                 nic_4_id = ''.join(filter(str.isdigit, row[2]))
#                 nic_5_id = ''.join(filter(str.isdigit, row[3]))

#                 nic_codes.append({
#                     "NIC 2 ID": nic_2_id,
#                     "NIC 4 ID": nic_4_id,
#                     "NIC 5 ID": nic_5_id,
#                     "NIC 2 Text": row[1].strip(),
#                     "NIC 4 Text": row[2].strip(),
#                     "NIC 5 Text": row[3].strip(),
#                     "activity": row[4].strip() 
#                 })

#     return nic_codes
# ------------------------------------------------------------------------
#physical mandate 

# Load AWS credentials
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")

# Initialize AWS Textract client
textract_client = boto3.client(
    "textract",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)

# Define regex patterns
patterns = {
    "Date": r"\b\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4}\b",
    "Utility Code": r"\b(?:INACH|NACH|YESB|HDFC|ICIC)[A-Z\d]+\b",
    "Sponsor Bank Code": r"\b(?:YESB|HDFC|SBIN|ICIC|INDB)[A-Z\d]{6,7}\b",
    "Authorizer": r"authorize\s+([A-Za-z\s]+)(?=\sTo)",
    "Bank A/C Number":  r"\b\d{10,}\b",
    "Bank Name": r"(?:With Bank\s)([A-Za-z\s]+BANK)",
    "IFSC/MICR": r"IFSC/MICR\s+([A-Z]{4}\d{7})", 
    "Amount in Figures": r"(?:₹|Rs\.?)?\s?([\d,]+\.\d{1,2})",
    "Phone Number": r"\b(\d{10}|\d{6}\s+\d{4}|\d{5}\s+\d{5}|\d{4}\s+\d{6}|\d{3}\s+\d{3}\s+\d{4})\b",
    # Adjusted regex for Name without look-behind
    "Name":r"(?<=Phone no\.\s\d{10}\s)\d+\s+([A-Z\s]+)",
    "From": r"(?<=From\s)(\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4})",
    "To": r"(?<=To\s)(\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4})"
}


def extract_data_from_image(image_bytes: bytes) -> Dict[str, str]:
    response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
    textract_text = " ".join([item["Text"] for item in response["Blocks"] if item["BlockType"] == "LINE"])
    extracted_data = extract_fields_from_text(textract_text)
    extracted_data["Amount in Figures"] = format_amount(extracted_data.get("Amount in Figures", "0"))

    # Adjusted Name extraction logic
    if extracted_data.get("Name", "Not found") == "Not found":
        name_match = re.search(r"[A-Z\s]+$", textract_text)
        extracted_data["Name"] = name_match.group(1).strip() if name_match else "Not found"

    return extracted_data


def extract_fields_from_text(text: str) -> Dict[str, str]:
    extracted_data = {}
    print("text",text)
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if field == "Amount in Figures":
                extracted_data[field] = matches[0].replace(",", "").strip()
            elif field in ["From", "To"]:
                date_match = matches[0].replace(" ", "/").replace(".", "/")
                extracted_data[field] = format_date(date_match)
            elif field == "Date":
                date_match = matches[0]
                extracted_data[field] = format_date(date_match)

            else:
                extracted_data[field] = matches[0] if isinstance(matches[0], str) else matches[0][0]
        else:
            extracted_data[field] = fuzzy_extract_field(text, field, pattern)

    # Additional logic for specific fields
    if extracted_data.get("Name", "Not found") == "Not found":
        name_match = re.search(r"[A-Z\s]+$", text)
        extracted_data["Name"] = name_match.group(0).strip() if name_match else "Not found"
    # Extract Bank A/C Number
    if "Bank A/C Number" not in extracted_data or extracted_data["Bank A/C Number"] == "Not found":
        account_number_match = re.search(
            r"(?:Account|A/C|Acc\.?|aft)\s?(?:No\.?|Number)?:?\s?(\d{8,15})\b",
            text,
            re.IGNORECASE,
        )
        extracted_data["Bank A/C Number"] = (
            account_number_match.group(0).split()[-1].strip() if account_number_match else "Not found"
        )

    return extracted_data



def format_amount(amount: str) -> str:
    # Remove commas and ensure float conversion
    try:
        return f"₹ {float(amount.replace(',', '')):,.2f}" if amount and amount != "Not found" else "Not found"
    except ValueError:
        return "Not found"


def format_date(date_str: str) -> str:
    # Remove any unwanted characters or spaces
    date_str = date_str.replace(" ", "").replace("-", "").replace("/", "").replace(".", "")
    
    # Check if the date is in DDMMYYYY format
    if len(date_str) == 8 and date_str.isdigit():
        day, month, year = date_str[:2], date_str[2:4], date_str[4:]
        return f"{day}/{month}/{year}"
    
    # Handle other possible formats (e.g., DD/MM/YYYY or MM/DD/YYYY)
    parts = re.split(r"[/.]", date_str)
    if len(parts) == 3:
        day, month, year = parts
        year = "20" + year[-2:] if len(year) == 2 else year
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
    
    # Return "Not found" if the format is unrecognized
    return "Not found"


def fuzzy_extract_field(text: str, key_name: str, search_pattern: str, threshold=65) -> str:
    for line in text.splitlines():
        if fuzz.partial_ratio(key_name.lower(), line.lower()) >= threshold:
            match = re.search(search_pattern, line, re.IGNORECASE)
            if match:
                return match.group().strip()
    if key_name in ["Utility Code", "Sponsor Bank Code"]:
        generic_pattern = r"\b[A-Z\d]{8,12}\b"
        fallback_match = re.search(generic_pattern, text)
        return fallback_match.group() if fallback_match else "Not found"
    return "Not found"

# # Load AWS credentials
# aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
# aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
# aws_region_name = config.get("AWSRekognition", "REGION")

# # Initialize AWS Textract client
# textract_client = boto3.client(
#     "textract",
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     region_name=aws_region_name
# )

# # Define regex patterns
# patterns = {
#     "Date": r"\b\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4}\b",
#     "Utility Code": r"\b(?:INACH|NACH|YESB|HDFC|ICIC)[A-Z\d]+\b",
#     "Sponsor Bank Code": r"\b(?:YESB|HDFC|SBIN|ICIC|INDB)[A-Z\d]{6,7}\b",
#     "Authorizer": r"authorize\s+([A-Za-z\s]+)",
#     "Bank A/C Number": r"\b\d{10,}\b",  # Adjusted to match bank account numbers
#     "Bank Name": r"(?:With Bank\s)([A-Za-z\s]+BANK)",  # Adjusted for exact bank name match
#     "IFSC/MICR": r"\b[A-Z]{4}\d{7}\b",  # Generalized IFSC code regex
#     "Amount in Figures": r"(?:An amount of rupees|₹|Rs\.?)\s?(?:[A-Za-z\s]*Only\s)?([\d,]+(?:\.\d{1,2})?)",
#     "Phone Number": r"\b\d{10}\b",
#     "Email ID": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
#     "Name": r"(?<=Phone no\.\s\d{10}\s)\d+\s+([A-Z\s]+)",
#     "From": r"(?<=From\s)(\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4})",
#     "To": r"(?<=To\s)(\d{1,2}[\s/.\-]?\d{1,2}[\s/.\-]?\d{2,4})"
# }

# def extract_data_from_image(image_bytes: bytes) -> Dict[str, str]:
#     response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
#     textract_text = " ".join([item["Text"] for item in response["Blocks"] if item["BlockType"] == "LINE"])
#     print("textract_text",textract_text)
#     extracted_data = extract_fields_from_text(textract_text)
#     extracted_data["Amount in Figures"] = format_amount(extracted_data.get("Amount in Figures", "0"))
#     print("extracted_data", extracted_data)
#     # Additional check for Name if not correctly extracted
#     if extracted_data.get("Name", "Not found") == "Not found":
#         name_match = re.search(r"(?<=Phone no\.\s\d{10}\s)\d+\s+([A-Z\s]+)", textract_text)
#         extracted_data["Name"] = name_match.group(1).strip() if name_match else "Not found"

#     return extracted_data

# def extract_fields_from_text(text: str) -> Dict[str, str]:
#     extracted_data = {}
#     for field, pattern in patterns.items():
#         matches = re.findall(pattern, text, re.IGNORECASE)
#         if matches:
#             if field == "Amount in Figures":
#                 extracted_data[field] = matches[0].replace(",", "").strip()
#             elif field in ["From", "To"]:
#                 date_match = matches[0].replace(" ", "/").replace(".", "/")
#                 extracted_data[field] = format_date(date_match)
#             elif field == "Date":
#                 if " " in matches[0]:  # Check if the date has spaces (i.e., DD MM YYYY format)
#                     extracted_data[field] = matches[0].replace(" ", "/")  # Replace spaces with slashes
#                 else:
#                     extracted_data[field] = matches[0][:2] + "/" + matches[0][2:4] + "/" + matches[0][4:]  # Format as DD/MM/YYYY
#             else:
#                 extracted_data[field] = matches[0] if isinstance(matches[0], str) else matches[0][0]
#         else:
#             extracted_data[field] = fuzzy_extract_field(text, field, pattern)
#     return extracted_data

# def format_amount(amount: str) -> str:
#     return f"₹ {float(amount):,.2f}" if amount and amount != "Not found" else "Not found"

# def format_date(date_str: str) -> str:
#     date_str = date_str.replace(" ", "")
#     if len(date_str) == 8:
#         day, month, year = date_str[:2], date_str[2:4], date_str[4:]
#         return f"{day}/{month}/{year}"
#     parts = re.split(r"[/.]", date_str)
#     if len(parts) == 3:
#         day, month, year = parts
#         year = "20" + year[-2:] if len(year) == 2 else year
#         return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
#     return "Not found"

# def fuzzy_extract_field(text: str, key_name: str, search_pattern: str, threshold=65) -> str:
#     for line in text.splitlines():
#         if fuzz.partial_ratio(key_name.lower(), line.lower()) >= threshold:
#             match = re.search(search_pattern, line, re.IGNORECASE)
#             if match:
#                 return match.group().strip()
#     if key_name in ["Utility Code", "Sponsor Bank Code"]:
#     
#     generic_pattern = r"\b[A-Z\d]{8,12}\b"
#         fallback_match = re.search(generic_pattern, text)
#         return fallback_match.group() if fallback_match else "Not found"
#     return "Not found"
# --------------------------------------------------DL-------------------------------
def extract_table_data(response):
    """Extract structured table data from AWS Textract response."""
    
    block_map = {block["Id"]: block for block in response["Blocks"]}
    table_content = []

    for block in response["Blocks"]:
        if block["BlockType"] == "TABLE":
            cells = []
            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    for cell_id in relationship["Ids"]:
                        cell = block_map[cell_id]
                        cell_text = ""

                        # Extract text from cell
                        if "Text" in cell:
                            cell_text = cell["Text"]
                        else:
                            # Check for nested child text
                            for sub_rel in cell.get("Relationships", []):
                                if sub_rel["Type"] == "CHILD":
                                    for sub_id in sub_rel["Ids"]:
                                        text_block = block_map.get(sub_id, {})
                                        if "Text" in text_block:
                                            cell_text = text_block["Text"]
                                            
                        row_index = cell.get("RowIndex", 0)
                        col_index = cell.get("ColumnIndex", 0)
                        cells.append((row_index, col_index, cell_text))

            # Sort cells properly
            cells.sort(key=lambda x: (x[0], x[1]))

            # Convert sorted cell data into structured table format
            table = {}
            for row_index, col_index, text in cells:
                if row_index not in table:
                    table[row_index] = []
                table[row_index].append(text)

            # Append structured rows to table_content
            for row in table.values():
                table_content.append(row)

    print("\n=== Extracted Table Data ===")
    for row in table_content:
        print(row)  # Debug: Print extracted table content

    return table_content

def extract_vehicle_details_from_table(table_data):
    """Extracts vehicle details from structured table data."""
    
    vehicle_details = {
        "Class of Vehicle": [],
        "Issued By": [],
        "Date of Issue": [],
        "Vehicle Category": [] 
    }

    # Skip header row (first row)
    for row in table_data[1:]:  # Start from second row
        if len(row) >= 3 and any(row):  # Ensure the row has data
            class_of_vehicle = row[1] if row[1] else "Unknown"
            issued_by = row[2] if row[2] else "Unknown"
            date_of_issue = row[3] if row[3] else "Unknown"
            vehicle_category = row[4] if row[4] else "Unknown" 

            vehicle_details["Class of Vehicle"].append(class_of_vehicle)
            vehicle_details["Issued By"].append(issued_by)
            vehicle_details["Date of Issue"].append(date_of_issue)
            vehicle_details["Vehicle Category"].append(vehicle_category)

    return vehicle_details

def extract_vehicle_details_from_table_text(table_data):
    """Extracts vehicle details from structured table data."""
    
    vehicle_details = {
        "Class of Vehicle": [],
        "Issued By": [],
        "Date of Issue": [],
        "Vehicle Category": []
    }

    for row in table_data[1:]:  
        if len(row) >= 2:
            class_of_vehicle = row[0] if len(row) > 0 else "Unknown"
            date_of_issue = row[1] if len(row) > 1 else "Unknown"

            vehicle_details["Class of Vehicle"].append(class_of_vehicle)
            vehicle_details["Issued By"].append("Not Available")
            vehicle_details["Date of Issue"].append(date_of_issue)
            vehicle_details["Vehicle Category"].append("Not Available")

    return vehicle_details

def extract_license_details(image_path):
    """Extract details from a driving license image using AWS Textract."""

    # Read image file as bytes
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()


    # Call AWS Textract
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["TABLES", "FORMS"]
    )

    extracted_text = []

    # Extract text from response
    for block in response.get("Blocks", []):
        if block["BlockType"] == "LINE":
            extracted_text.append(block["Text"])

    extracted_text_str = " ".join(extracted_text)

    print("\n=== Extracted Text ===")
    print(extracted_text_str)

    # Extract Driving License Number
    dl_number_match = re.search(r'([A-Z]{2}\d{1,2}[\s-]?\d{4,12})', extracted_text_str)
    dl_number = dl_number_match.group().replace(" ", "") if dl_number_match else "Not Found"

    # Extract Name
    name_match = re.search(r'Name[:\s]+([A-Za-z\s]+)', extracted_text_str)
    if name_match:
        name = name_match.group(1).strip()
        name = re.sub(r'\b(Holder|Signature|S|Date of Birth)\b', '', name).strip()  # Remove "Holder", "Signature"
    else:
        name = "Not Found"

    # Extract Date of Birth
    dob_matches = re.findall(r'(?:Date\s*of\s*Birth|DOB)\s*[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})', extracted_text_str)
    dob = dob_matches if dob_matches else ["Not Found"]

    

    guardian_match = re.search(r'(Son|Daughter|Wife|S/D/W)\s*of[:\s]+([\w\s]+)?', extracted_text_str)
    if guardian_match:
        # Check if group(2) exists before accessing it
        guardian_name = guardian_match.group(2).strip() if guardian_match.group(2) else "Not Found"

        # Remove unwanted words from guardian name
        guardian_name = re.sub(r'\b(?:Date|A|Address|NO|AJP|Add|\d+|Wing|Flat|Road|Village|Near|PIN)\b', '', guardian_name, flags=re.IGNORECASE).strip()

        # guardian = f"{relationship_type} of {guardian_name}" if guardian_name != "Not Found" else relationship_type
        guardian = f"{guardian_name}" if guardian_name != "Not Found" else "Not Found"

    else:
        guardian = "Not Found"

    # Extract Issue & Validity Dates
    validity_dates = re.findall(r'(\d{2}[/-]\d{2}[/-]\d{4})', extracted_text_str)
    valid_from = validity_dates[0] if len(validity_dates) > 0 else "Not Found"
    valid_upto = validity_dates[1] if len(validity_dates) > 1 else "Not Found"

    address_pin_match = re.search(r'Add\s*[:\s]*(.+?)\s+PIN\s*[:\s]*(\d{6})?', extracted_text_str, re.IGNORECASE)

    if address_pin_match:
        address = address_pin_match.group(1).strip()  # Extract Address
        pin_code = address_pin_match.group(2).strip() if address_pin_match.group(2) else "Not Found"
        address = f"{address}, PIN: {pin_code}"  # Append PIN to the address
    else:
        # If no PIN found, check for the regular address pattern
        address_match = re.search(r'Address[:\s]+(.+)', extracted_text_str)
        if address_match:
            address = address_match.group(1).strip()
        else:
            address = "Not Found"

    # Extract Table Data
    table_data = extract_table_data(response)

    # Debug: Print structured table rows
    print("\n=== Extracted Table Data ===")
    for row in table_data:
        print(row)

    
    # Extract Vehicle Details from Table
    vehicle_details = extract_vehicle_details_from_table(table_data)

    # If vehicle details from table are empty, try extracting from text
    if not vehicle_details["Class of Vehicle"]:  
        vehicle_details = extract_vehicle_details_from_table_text(table_data)

    # print("\n=== Corrected Vehicle Details ===")
    # print(json.dumps(vehicle_details, indent=4))

    extracted_data = {
        "Driving License Number": dl_number,
        "Name": name,
        "Date of Birth": dob,
        "Son / Daughter / Wife of": guardian, 
        "Valid From": valid_from,
        "Valid Upto": valid_upto,
        "Address": address,
        # "Vehicle Details": vehicle_details
    }

    # print("\n=== Final Extracted Data ===")
    # print(json.dumps(extracted_data, indent=4))  # Print formatted JSON result

    return extracted_data
# -----------------------------------------------------mask----
import cv2
import numpy as np
import re
from PIL import Image, ImageDraw, ImageFont
from pytesseract import image_to_osd, image_to_data, Output
from scipy import ndimage
import boto3
import re
import os
from PIL import Image, ImageDraw, ImageFont

# AWS Credentials (Ensure correct configuration)
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")

# Initialize AWS Textract client
textract_client = boto3.client(
    "textract",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Uses AWS Textract to extract text from an image.

    :param image_bytes: The byte content of the uploaded image.
    :return: Extracted text from the image.
    """
    response = textract_client.detect_document_text(Document={"Bytes": image_bytes})

    extracted_text = ""
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            extracted_text += item["Text"] + "\n"
    print("extracted_text", extracted_text)
    return extracted_text

def extract_aadhaar_details(text: str) -> Dict[str, str]:
    """
    Extracts specific details from the Aadhaar text.

    :param text: Extracted text from the Aadhaar image.
    :return: A dictionary containing extracted Aadhaar details with capitalized keys.
    """
    details = {
        "Aadhaar_Number": None,
        "Name": None,
        "Dob": None,
        "Gender": None,
        "Address": None,
        "Accuracy":None,
    }

    # Extract Aadhaar number
    match_aadhaar = re.search(r"\b\d{4} \d{4} \d{4}\b", text)
    if match_aadhaar:
        details["Aadhaar_Number"] = match_aadhaar.group(0)

    # Extract Name (assume it appears near "DOB" or at the start after Govt of India)
    # lines = text.split("\n")
    # for i, line in enumerate(lines):
    #     if re.search(r"DOB|Date of Birth", line, re.IGNORECASE):
    #         if i > 0:
    #             details["Name"] = lines[i - 1].strip()
    #         break

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"Year of Birth|DOB|Date of Birth", line, re.IGNORECASE):
            # Try to find the name in a preceding line
            for j in range(i - 1, -1, -1):
                if re.search(r"[A-Za-z]{2,}", lines[j]):  
                    details["Name"] = lines[j].strip()
                    break

    # Extract Date of Birth
    # match_dob = re.search(r"(DOB|Date of Birth):\s*(\d{2}/\d{2}/\d{4})", text)
    # if match_dob:
    #     details["Dob"] = match_dob.group(2)

    # Extract Date of Birth or Year of Birth
    match_dob = re.search(r"(DOB|Date of Birth):\s*(\d{2}/\d{2}/\d{4})", text)
    if match_dob:
        details["Dob"] = match_dob.group(2)
    else:
        match_year_of_birth = re.search(r"(DOB|Date of Birth|Year of Birth) :?\s*(\d{4}|\d{2}/\d{2}/\d{4})", text)
        if match_year_of_birth:
            details["Dob"] = match_year_of_birth.group(2)


    # Extract Gender
    match_gender = re.search(r"\b(Male|Female|Other)\b", text, re.IGNORECASE)
    if match_gender:
        details["Gender"] = match_gender.group(0).capitalize()

    # Extract Address (find "Address" keyword or a block of text below UID)
    address_lines = []
    address_start = False
    for line in lines:
        if "Address" in line or address_start:
            address_start = True
            # Stop collecting address if unrelated text is detected
            if re.search(r"\b\d{4} \d{4} \d{4}\b|help@|www\.|UIDAI|^-\s*$", line, re.IGNORECASE):
                break
            if line.strip():
                address_lines.append(line.strip())
    if address_lines:
        details["Address"] = " ".join(address_lines)

    print("details", details)

    return details


# def mask_aadhaar_number(image: Image, aadhaar_number: str) -> Image:
#     """
#     Mask the Aadhaar number on the image by drawing a black rectangle where the Aadhaar number is.
#     :param image: The original PIL image object.
#     :param aadhaar_number: The Aadhaar number to mask.
#     :return: The image with the masked Aadhaar number (as PIL object).
#     """
#     # Convert PIL image to OpenCV format (numpy array)
#     open_cv_image = np.array(image)
    
#     # Convert RGB to BGR (OpenCV uses BGR)
#     open_cv_image = open_cv_image[:, :, ::-1].copy()

#     # Masking logic (draw rectangle and text)
#     draw = ImageDraw.Draw(image)
    
#     x, y = 100, 200  # Specify coordinates where the Aadhaar number is located
#     width, height = 300, 30  # Define the area for masking

#     # Masking the number with a black rectangle
#     draw.rectangle([x, y, x + width, y + height], fill="black")

#     # Optionally, you can draw text over the rectangle (like '**** **** 1234') if you want
#     font = ImageFont.load_default()
#     masked_text = "xxxx xxxx " + aadhaar_number[-4:]
#     draw.text((x + 5, y + 5), masked_text, font=font, fill="white")
    
#     # Convert the PIL image back to OpenCV format (numpy array)
#     open_cv_image = np.array(image)

#     return open_cv_image


def rotate(image, center=None, scale=1.0):
    angle = int(re.search(r'(?<=Rotate: )\d+', image_to_osd(image)).group(0))
    (h, w) = image.shape[:2]
    if center is None:
        center = (w / 2, h / 2)
    rotated = ndimage.rotate(image, float(angle) * -1)
    return rotated

def preprocessing(image):
    w, h = image.shape[:2]
    if w < h:
        image = rotate(image)
    resized_image = cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
    grey_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    blur_image = cv2.medianBlur(grey_image, 3)
    thres_image = cv2.adaptiveThreshold(blur_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                        cv2.THRESH_BINARY, 13, 7)
    return thres_image, resized_image

def mask_aadhaar_number(image: Image, aadhaar_number: str) -> Image:
    """
    Mask the Aadhaar number in the image by hiding the first 8 digits and leaving the last 4 digits visible.
    The first 8 digits are replaced with a white rectangle, and the last 4 digits are displayed in white text.
    
    :param image: The original PIL image object.
    :param aadhaar_number: The Aadhaar number to mask.
    :return: The image with the masked Aadhaar number (as PIL object).
    """
    # Convert PIL image to OpenCV format
    open_cv_image = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    # Apply preprocessing
    thres_image, resized_image = preprocessing(open_cv_image)

    # OCR to detect Aadhaar number
    d = image_to_data(thres_image, output_type=Output.DICT)
    number_pattern = r"(?<!\d)\d{4}(?!\d)"
    n_boxes = len(d['text'])
    final_image = resized_image.copy()
    masked_text_position = None

    # Locate Aadhaar number and mask it
    for i in range(n_boxes):
        if int(d['conf'][i]) > 20:  # Confidence threshold
            if re.match(number_pattern, d['text'][i]):
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                if d['text'][i] != aadhaar_number[-4:]:  # Mask all except last 4 digits
                    # Mask with white rectangle
                    cv2.rectangle(final_image, (x, y), (x + w, y + h), (255, 255, 255), -1)
                else:
                    masked_text_position = (x, y, w, h)

    # Draw the last 4 digits in white text over their original position
    if masked_text_position:
        (x, y, w, h) = masked_text_position
        font = ImageFont.truetype("arial.ttf", 20)  # Use appropriate font and size
        draw = ImageDraw.Draw(image)
        draw.text((x, y), aadhaar_number[-4:], font=font, fill="white")

    # Convert back to PIL Image
    final_pil_image = Image.fromarray(cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB))
    return final_pil_image
# ------------------------------------------passport-------------------------------
import boto3
import re
from datetime import datetime

# def process_indian_passport_with_textract(image_bytes):
#     try:
#         # Initialize Textract client
#         textract_client = boto3.client(
#             "textract",
#             aws_access_key_id=aws_access_key_id,
#             aws_secret_access_key=aws_secret_access_key,
#             region_name=aws_region_name
#         )
        
#         # Call Textract
#         response = textract_client.analyze_document(
#             Document={'Bytes': image_bytes},
#             FeatureTypes=["FORMS", "TABLES"]
#         )
        
#         # Initialize result dictionary
#         result = {
#             "status": "success",
#             "data": {
#                 "Passport No.": "",
#                 "Surname": "",
#                 "Given Names": "",
#                 "Nationality": "",
#                 "Date of Issue": "",
#                 "Place of Birth": "",
#                 "Type": "",
#                 "Date of Expiry": "",
#                 "Date of Birth": "",
#                 "Sex": "",
#                 "Country Code": "IND",
#                 "MRZ": ""
#             }
#         }
        
#         # Process the response
#         blocks = response['Blocks']
        
#         # First pass: Extract all text lines and key-value pairs
#         extracted_text = []
#         full_text = ""
#         key_value_pairs = {}
        
#         for block in blocks:
#             if block['BlockType'] == 'LINE':
#                 line_text = block.get('Text', '').strip()
#                 extracted_text.append(line_text)
#                 full_text += line_text + "\n"
                
#                 if line_text.startswith('P<IND') or re.match(r'^[A-Z0-9<]{30,}$', line_text):
#                     result['data']['MRZ'] += line_text + "\n"
            
#             if block['BlockType'] == 'KEY_VALUE_SET':
#                 if 'EntityTypes' in block and 'KEY' in block['EntityTypes']:
#                     key_id = block['Id']
#                     key_text = ""
#                     value_id = None
                    
#                     if 'Relationships' in block:
#                         for relationship in block['Relationships']:
#                             if relationship['Type'] == 'VALUE':
#                                 value_id = relationship['Ids'][0] if relationship['Ids'] else None
#                             elif relationship['Type'] == 'CHILD':
#                                 for child_id in relationship['Ids']:
#                                     for child_block in blocks:
#                                         if child_block['Id'] == child_id and child_block['BlockType'] == 'WORD':
#                                             key_text += child_block.get('Text', '') + " "
                    
#                     key_text = key_text.strip().lower()
                    
#                     if key_text and value_id:
#                         key_value_pairs[key_id] = {
#                             'key': key_text,
#                             'value_id': value_id
#                         }

#         # Print the full extracted text
#         print("===== Full Extracted Text from Textract =====")
#         print(full_text)
#         print("=============================================")

#         # Second pass: Get the values for each key
#         for key_id, info in key_value_pairs.items():
#             value_id = info['value_id']
#             value_text = ""
            
#             for block in blocks:
#                 if block['Id'] == value_id and 'Relationships' in block:
#                     for relationship in block['Relationships']:
#                         if relationship['Type'] == 'CHILD':
#                             for child_id in relationship['Ids']:
#                                 for child_block in blocks:
#                                     if child_block['Id'] == child_id and child_block['BlockType'] == 'WORD':
#                                         value_text += child_block.get('Text', '') + " "
            
#             key_value_pairs[key_id]['value'] = value_text.strip()
        
#         indian_passport_mapping = {
#             'surname': 'Surname',
#             'given name': 'Given Names',
#             'name': 'Given Names',
#             'nationality': 'Nationality',
#             'date of issue': 'Date of Issue',
#             'place of issue': 'Place of Issue',
#             'place of birth': 'Place of Birth',
#             'type': 'Type',
#             'date of expiry': 'Date of Expiry',
#             'date of birth': 'Date of Birth',
#             'sex': 'Sex',
#             'gender': 'Sex',
#             'passport no': 'Passport No.',
#             'passport number': 'Passport No.',
#             'file number': 'Passport No.'
#         }
        
#         for key_id, info in key_value_pairs.items():
#             key = info['key']
#             value = info['value']
            
#             for map_key, result_key in indian_passport_mapping.items():
#                 if map_key in key:
#                     # Remove spaces from passport number specifically
#                     if result_key == 'Passport No.':
#                         result['data'][result_key] = value.replace(" ", "")
#                     else:
#                         result['data'][result_key] = value
#                     break
        
#         for line in extracted_text:
#             if re.search(r'[A-Z]\d{8}', line) and not result['data']['Passport No.']:
#                 passport_match = re.search(r'[A-Z]\d{7,8}', line)
#                 if passport_match:
#                     result['data']['Passport No.'] = passport_match.group(0).replace(" ", "")

            
#             if "Surname" in line and not result['data']['Surname']:
#                 parts = line.split("Surname")
#                 if len(parts) > 1:
#                     result['data']['Surname'] = parts[1].strip()
            
#             if "Given Names" in line and not result['data']['Given Names']:
#                 parts = line.split("Given Names")
#                 if len(parts) > 1:
#                     result['data']['Given Names'] = parts[1].strip()
        
#         if result['data']['MRZ']:
#             mrz_lines = result['data']['MRZ'].strip().split('\n')
            
#             if len(mrz_lines) > 0:
#                 if len(mrz_lines[0]) > 5:
#                     mrz_name_part = mrz_lines[0][5:]
#                     name_parts = mrz_name_part.split('<<')
                    
#                     if len(name_parts) >= 2 and not result['data']['Surname']:
#                         result['data']['Surname'] = name_parts[0].replace('<', ' ').strip()
                    
#                     if len(name_parts) >= 2 and not result['data']['Given Names']:
#                         result['data']['Given Names'] = name_parts[1].replace('<', ' ').strip()
                
#                 if len(mrz_lines) > 1 and len(mrz_lines[1]) > 20:
#                     if not result['data']['Passport No.'] and len(mrz_lines[1]) > 9:
#                         # Remove all spaces and '<' characters from passport number
#                         result['data']['Passport No.'] = mrz_lines[1][0:9].replace('<', '').replace(' ', '')
                    
#                     if not result['data']['Date of Birth'] and len(mrz_lines[1]) > 19:
#                         dob_raw = mrz_lines[1][13:19]
#                         try:
#                             year = int(dob_raw[0:2])
#                             month = int(dob_raw[2:4])
#                             day = int(dob_raw[4:6])
#                             year_prefix = '20' if year < 25 else '19'
#                             result['data']['Date of Birth'] = f"{day:02d}/{month:02d}/{year_prefix}{year:02d}"
#                         except:
#                             pass
                    
#                     if not result['data']['Sex'] and len(mrz_lines[1]) > 20:
#                         result['data']['Sex'] = mrz_lines[1][20]
                    
#                     if not result['data']['Date of Expiry'] and len(mrz_lines[1]) > 27:
#                         doe_raw = mrz_lines[1][21:27]
#                         try:
#                             year = int(doe_raw[0:2])
#                             month = int(doe_raw[2:4])
#                             day = int(doe_raw[4:6])
#                             year_prefix = '20' if year < 25 else '19'
#                             result['data']['Date of Expiry'] = f"{day:02d}/{month:02d}/{year_prefix}{year:02d}"
#                         except:
#                             pass
        
#         if not result['data']['Type'] and len(extracted_text) > 0:
#             for line in extracted_text:
#                 if "Type" in line and "P" in line:
#                     result['data']['Type'] = "P"
        
#         # Clean up all fields and ensure passport number has no spaces
#         for key in result['data']:
#             if isinstance(result['data'][key], str):
#                 result['data'][key] = result['data'][key].strip()
#                 # Additional cleanup for passport number to ensure no spaces
#                 if key == 'Passport No.' and result['data'][key]:
#                     result['data'][key] = result['data'][key].replace(' ', '')
        
#         if not result['data']['Nationality']:
#             nationality_match = re.search(r'\bINDIAN\b', full_text, re.IGNORECASE)
#             if nationality_match:
#                 result['data']['Nationality'] = 'INDIAN'

#         # Fallback: Extract Date of Issue (look for valid date near Date of Expiry)
#         if not result['data']['Date of Issue']:
#             all_dates = re.findall(r'\d{2}/\d{2}/\d{4}', full_text)
#             if len(all_dates) >= 2:
#                 # Textract usually lists Date of Issue before Date of Expiry
#                 result['data']['Date of Issue'] = all_dates[0]
#         return result

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
import boto3
import re

def process_indian_passport_with_textract(image_bytes):
    try:
        # Initialize Textract client
        textract_client = boto3.client(
            "textract",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region_name
        )
        
        # Call Textract
        response = textract_client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=["FORMS", "TABLES"]
        )
        
        # Initialize result dictionary
        result = {
            "status": "success",
            "data": {
                "Passport No.": "",
                "Surname": "",
                "Given Names": "",
                "Nationality": "",
                "Date of Issue": "",
                "Place of Birth": "",
                "Type": "",
                "Date of Expiry": "",
                "Date of Birth": "",
                "Sex": "",
                "Country Code": "IND",
                "MRZ": ""
            }
        }
        
        # Process the response
        blocks = response['Blocks']
        
        extracted_text = []
        full_text = ""
        key_value_pairs = {}
        
        for block in blocks:
            if block['BlockType'] == 'LINE':
                line_text = block.get('Text', '').strip()
                extracted_text.append(line_text)
                full_text += line_text + "\n"
                if line_text.startswith('P<IND') or re.match(r'^[A-Z0-9<]{30,}$', line_text):
                    result['data']['MRZ'] += line_text + "\n"
            
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'EntityTypes' in block and 'KEY' in block['EntityTypes']:
                    key_id = block['Id']
                    key_text = ""
                    value_id = None
                    
                    if 'Relationships' in block:
                        for relationship in block['Relationships']:
                            if relationship['Type'] == 'VALUE':
                                value_id = relationship['Ids'][0] if relationship['Ids'] else None
                            elif relationship['Type'] == 'CHILD':
                                for child_id in relationship['Ids']:
                                    for child_block in blocks:
                                        if child_block['Id'] == child_id and child_block['BlockType'] == 'WORD':
                                            key_text += child_block.get('Text', '') + " "
                    
                    key_text = key_text.strip().lower()
                    
                    if key_text and value_id:
                        key_value_pairs[key_id] = {
                            'key': key_text,
                            'value_id': value_id
                        }

        print("===== Full Extracted Text from Textract =====")
        print(full_text)
        print("=============================================")

        for key_id, info in key_value_pairs.items():
            value_id = info['value_id']
            value_text = ""
            for block in blocks:
                if block['Id'] == value_id and 'Relationships' in block:
                    for relationship in block['Relationships']:
                        if relationship['Type'] == 'CHILD':
                            for child_id in relationship['Ids']:
                                for child_block in blocks:
                                    if child_block['Id'] == child_id and child_block['BlockType'] == 'WORD':
                                        value_text += child_block.get('Text', '') + " "
            key_value_pairs[key_id]['value'] = value_text.strip()
        
        indian_passport_mapping = {
            'surname': 'Surname',
            'given name': 'Given Names',
            'name': 'Given Names',
            'nationality': 'Nationality',
            'date of issue': 'Date of Issue',
            'place of issue': 'Place of Issue',
            'place of birth': 'Place of Birth',
            'type': 'Type',
            'date of expiry': 'Date of Expiry',
            'date of birth': 'Date of Birth',
            'sex': 'Sex',
            'gender': 'Sex',
            'passport no': 'Passport No.',
            'passport number': 'Passport No.',
            'file number': 'Passport No.'
        }
        
        for key_id, info in key_value_pairs.items():
            key = info['key']
            value = info['value']
            for map_key, result_key in indian_passport_mapping.items():
                if map_key in key:
                    if result_key == 'Passport No.':
                        result['data'][result_key] = value.replace(" ", "")
                    else:
                        result['data'][result_key] = value
                    break
        
        for line in extracted_text:
            if re.search(r'[A-Z]\d{8}', line) and not result['data']['Passport No.']:
                passport_match = re.search(r'[A-Z]\d{7,8}', line)
                if passport_match:
                    result['data']['Passport No.'] = passport_match.group(0).replace(" ", "")
            
            if "Surname" in line and not result['data']['Surname']:
                parts = line.split("Surname")
                if len(parts) > 1:
                    result['data']['Surname'] = parts[1].strip()
            
            if "Given Names" in line and not result['data']['Given Names']:
                parts = line.split("Given Names")
                if len(parts) > 1:
                    result['data']['Given Names'] = parts[1].strip()
        
        if result['data']['MRZ']:
            mrz_lines = result['data']['MRZ'].strip().split('\n')
            if len(mrz_lines) > 0:
                if len(mrz_lines[0]) > 5:
                    mrz_name_part = mrz_lines[0][5:]
                    name_parts = mrz_name_part.split('<<')
                    if len(name_parts) >= 2 and not result['data']['Surname']:
                        result['data']['Surname'] = name_parts[0].replace('<', ' ').strip()
                    if len(name_parts) >= 2 and not result['data']['Given Names']:
                        result['data']['Given Names'] = name_parts[1].replace('<', ' ').strip()
                
                if len(mrz_lines) > 1 and len(mrz_lines[1]) > 20:
                    if not result['data']['Passport No.'] and len(mrz_lines[1]) > 9:
                        result['data']['Passport No.'] = mrz_lines[1][0:9].replace('<', '').replace(' ', '')
                    
                    if not result['data']['Date of Birth'] and len(mrz_lines[1]) > 19:
                        dob_raw = mrz_lines[1][13:19]
                        try:
                            year = int(dob_raw[0:2])
                            month = int(dob_raw[2:4])
                            day = int(dob_raw[4:6])
                            year_prefix = '20' if year < 25 else '19'
                            result['data']['Date of Birth'] = f"{day:02d}/{month:02d}/{year_prefix}{year:02d}"
                        except:
                            pass
                    
                    if not result['data']['Sex'] and len(mrz_lines[1]) > 20:
                        result['data']['Sex'] = mrz_lines[1][20]
                    
                    if not result['data']['Date of Expiry'] and len(mrz_lines[1]) > 27:
                        doe_raw = mrz_lines[1][21:27]
                        try:
                            year = int(doe_raw[0:2])
                            month = int(doe_raw[2:4])
                            day = int(doe_raw[4:6])
                            year_prefix = '20' if year < 25 else '19'
                            result['data']['Date of Expiry'] = f"{day:02d}/{month:02d}/{year_prefix}{year:02d}"
                        except:
                            pass
        
        if not result['data']['Type'] and len(extracted_text) > 0:
            for line in extracted_text:
                if "Type" in line and "P" in line:
                    result['data']['Type'] = "P"
        
        # Clean up all fields and ensure passport number has no spaces and fix starting '0' issue
        for key in result['data']:
            if isinstance(result['data'][key], str):
                result['data'][key] = result['data'][key].strip()

                if key == 'Passport No.' and result['data'][key]:
                    passport_no = result['data'][key].replace(' ', '')
                    # Remove '0' immediately after first alphabet (e.g. K01234567 -> K1234567)
                    passport_no = re.sub(r'^([A-Z])0', r'\1', passport_no)
                    result['data'][key] = passport_no
        
        if not result['data']['Nationality']:
            nationality_match = re.search(r'\bINDIAN\b', full_text, re.IGNORECASE)
            if nationality_match:
                result['data']['Nationality'] = 'INDIAN'

        if not result['data']['Date of Issue']:
            all_dates = re.findall(r'\d{2}/\d{2}/\d{4}', full_text)
            if len(all_dates) >= 2:
                result['data']['Date of Issue'] = all_dates[0]
        if not result['data']['Passport No.']:
            return {
                "status": "error",
                "message": "Passport number not found"
            }
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    # ------------------------------------------------voter id 
import io
import os
import boto3
from typing import Dict
from PIL import Image, ImageOps
from fuzzywuzzy import fuzz, process
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")

# Initialize AWS Textract client
textract_client = boto3.client(
    "textract",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)



def preprocess_image(image: Image.Image) -> Image.Image:
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    return image


def clean_text(text: str) -> str:
    text = text.strip().replace(":", "").replace(".", "")
    return re.sub(r"[^A-Za-z\s]", "", text).strip()


def extract_text_from_image_textract(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
    return "\n".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])


def fuzzy_match_field(text_lines, keyword, threshold=80):
    match = process.extractOne(keyword, text_lines, scorer=fuzz.token_set_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return None


def extract_value_from_line(line: str, keyword: str) -> str:
    """Extract value after keyword from line."""
    parts = line.split(":")
    if len(parts) > 1:
        return clean_text(parts[1])
    return clean_text(re.sub(re.escape(keyword), "", line, flags=re.IGNORECASE))


def get_value_after_keyword(text_lines, keyword, threshold=80):
    for i, line in enumerate(text_lines):
        if fuzz.token_set_ratio(line.lower(), keyword.lower()) >= threshold:
            if i + 1 < len(text_lines):
                return clean_text(text_lines[i + 1])
    return None

def extract_name_from_lines(lines):
    for i, line in enumerate(lines):
        lower = line.lower()

        # Match if line contains both "elector" and "name", or just starts with "name"
        if ("elector" in lower and "name" in lower) or lower.strip().startswith("name"):
            # Case 1: Name present after colon on the same line
            if ":" in line:
                return clean_text(line.split(":", 1)[1])

            # Case 2: Name is in one of the next two lines
            for offset in range(1, 3):
                if i + offset < len(lines):
                    next_line = lines[i + offset].strip()
                    if next_line and not next_line.startswith(":"):
                        return clean_text(next_line)
    
    return None



def extract_father_name_from_lines(lines):
    for i, line in enumerate(lines):
        if "father" in line.lower() or "husband" in line.lower():
            if ":" in line:
                return clean_text(line.split(":", 1)[1])
            if i + 1 < len(lines):
                return clean_text(lines[i + 1])
    return None


def extract_gender_from_lines(lines):
    for i, line in enumerate(lines):
        lower = line.lower()
        if "sex" in lower or "male" in lower or "female" in lower:
            combined = " ".join(lines[i:i+2]).lower()
            if "female" in combined:
                return "Female"
            elif "male" in combined:
                return "Male"
    return None


def extract_voter_id_details(image: Image.Image) -> Dict[str, str]:
    image = preprocess_image(image)
    text = extract_text_from_image_textract(image)

    text_lines = text.splitlines()
    print("\n".join(f"{i}: {line}" for i, line in enumerate(text_lines)))  # Optional debugging

    details = {
        "Name": extract_name_from_lines(text_lines),
        "father_name": extract_father_name_from_lines(text_lines),
        "Voter ID Number": None,
        "gender": extract_gender_from_lines(text_lines),
        "DOB": None,
    }

    # Extract Voter ID
    id_match = re.search(r"[A-Z]{3}/?\d{6,}", text)
    if id_match:
        details["Voter ID Number"] = id_match.group(0)

    # Extract DOB
    dob_match = re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", text)
    if dob_match:
        details["DOB"] = dob_match.group(0)

    return details

    # ---------------------------------------------------------property valuation ---------------------------------------------------------

# aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
# aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
# aws_region_name = config.get("AWSRekognition", "REGION")

# # Create boto3 session for Textract
# session = boto3.Session(
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     region_name=aws_region_name
# )
# textract_client = session.client('textract')


# def extract_property_valuation_details(image_bytes: bytes) -> Dict[str, str]:
#     # Analyze document with Textract
#     response = textract_client.analyze_document(
#         Document={"Bytes": image_bytes},
#         FeatureTypes=["FORMS"]
#     )

#     # Extract all text lines from Textract response
#     lines = [
#         block["Text"]
#         for block in response["Blocks"]
#         if block["BlockType"] == "LINE" and "Text" in block
#     ]

#     # Join lines into one full text
#     full_text = " ".join(lines)
#     print("---- FULL TEXT ----")
#     print(full_text)

#     # Initialize result dictionary
#     result = {
#         "Valuer_Name": "",
#         "Report_Date": "",
#         "Visit_Date": "",
#         "Name_Of_Applicant": "",
#         "Name_Of_Property_Owner": "",
#         "Property_Address_As_Per_Site": "",
#         "Legal_Address_Of_Property": "",
#         "Property_Type": "",
#         "Total_Building_Value_RS": "",
#         "Total_Value_Of_Property_Actual_RS": ""
#     }

#     # Define regex patterns for fields
#     patterns = {
#         "Valuer_Name": r"Valuer\s+Name\s*[:\-]?\s*(.*?)(?=\s+Report\s+Date|\s+Visit\s+Date|$)",
#         "Report_Date": r"Report\s+Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
#         "Visit_Date": r"Visit\s+Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
#         "Name_Of_Applicant": r"Name\s+Of\s+Applicant\s*[:\-]?\s*([A-Z0-9\s]+)",
#         "Name_Of_Property_Owner": r"Name\s+of\s+Property\s+Owner\s*[:\-]?\s*([A-Z\s]+)",
#         "Property_Address_As_Per_Site": r"Property\s+Address\s+as\s+per\s+site\s*[:\-]?\s*(.+?)(?=\s+4\)\.\s+Legal\s+Address|Legal\s+Address)",
#         "Legal_Address_Of_Property": r"Legal\s+Address\s+of\s+Property\s*[:\-]?\s*(.+?)(?=\s+5\)\.\s+Contact\s+Number|Contact\s+Number)",
#         "Property_Type": r"Property\s+Usage\s*\(Actual\)\s*[:\-]?\s*([A-Z]+)",
#         "Total_Building_Value_RS": r"Total\s+Building\s+Value.*?Rs[\.]?\s*([\d,]+)",
#         "Total_Value_Of_Property_Actual_RS": r"Total\s+Value\s+Of\s+Property\s+As\s+Per\s+Actual.*?Rs[\.]?\s*([\d,]+)"
#     }

#     # Fallback method for value extraction
#     def find_value_by_keyword(text: str, keyword: str) -> str:
#         try:
#             pattern = re.compile(re.escape(keyword) + r".{0,100}?Rs[\.]?\s*([\d,]+)(?:/-)?", re.IGNORECASE)
#             match = pattern.search(text)
#             if match:
#                 return match.group(1).strip()
#         except Exception as e:
#             print(f"Error extracting {keyword}: {e}")
#         return ""

#     # Try to extract values using regex or fallback
#     for key, pattern in patterns.items():
#         match = re.search(pattern, full_text, re.IGNORECASE)
#         if match:
#             result[key] = match.group(1).strip()
#             print(f">> [MATCHED via regex] {key}: {result[key]}")
#         else:
#             if key == "Total_Building_Value_RS":
#                 result[key] = find_value_by_keyword(full_text, "Total Building Value")
#                 if result[key]:
#                     print(f">> [MATCHED via fallback] {key}: {result[key]}")
#             elif key == "Total_Value_Of_Property_Actual_RS":
#                 result[key] = find_value_by_keyword(full_text, "Total Value Of Property As Per Actual")
#                 if result[key]:
#                     print(f">> [MATCHED via fallback] {key}: {result[key]}")
#             else:
#                 print(f">> [NO MATCH] {key} using pattern: {pattern}")

#     if not any(result.values()):
#         return {"message": "Could not process the input file or details not found"}


#     return result
    # Final check
    # if not result["Name_Of_Applicant"] and not result["Valuer_Name"]:
    #     return {"message": "Could not process the input file or details not found"}

    # return result
import boto3
import re
from typing import Dict
from fastapi import HTTPException
aws_access_key_id = config.get("AWSRekognition", "ACCESS_KEY")
aws_secret_access_key = config.get("AWSRekognition", "SECRET_KEY")
aws_region_name = config.get("AWSRekognition", "REGION")


# Initialize AWS clients
# session = boto3.Session(
#     aws_access_key_id=AWS_CONFIG["aws_access_key_id"],
#     aws_secret_access_key=AWS_CONFIG["aws_secret_access_key"],
#     region_name=AWS_CONFIG["aws_region_name"]
# )
textract_client = session.client('textract')

def extract_property_valuation(image_bytes: bytes) -> Dict[str, str]:
    """Extract property valuation details from document image."""
    try:
        response = textract_client.analyze_document(
            Document={"Bytes": image_bytes},
            FeatureTypes=["FORMS"]
        )

        lines = [
            block.get("Text", "")
            for block in response.get("Blocks", [])
            if block.get("BlockType") == "LINE"
        ]

        full_text = " ".join(lines)

        result = {
            "Valuer_Name": "",
            "Report_Date": "",
            "Date_of_Inspection": "",
            "Name_of_Customer": "",
            "Name_of_Property_Holder": "",
            "Legal_Address": "",
            "Nature_of_Property": "",
            "Fair_Market_Value": "",
            "Remarks": ""
        }

        patterns = {
            "Valuer_Name": r"(SENTHIL\s+KUMAR\s+ASSOCIATES|MSL\s+Valuations\s+and\s+Advisory\s+Services|BHIRUD\s+AND\s+ASSOCIATES|Er\.\s+[A-Za-z\s\.]+|M\/S\.\s+[A-Za-z\s\.\&\,]+)",
            "Report_Date": r"Ref\.?\s*No\.?\s*.*?Date\s+(\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4})",
            "Date_of_Inspection": r"(?:9|10)\s+Date\s+of\s+inspection\s*[:\-]?\s*(.*?)\s+(?:10|11)\s+Person",
            "Name_of_Customer": r"Name\s+of\s+the\s+Customer\s*[:\-]?\s*(.*?)\s+(?:\d+\s+Documents|COPY\s+OF)",
            "Name_of_Property_Holder": r"Name\s+of\s+the\s+Property\s+holder\s*[:\-]?\s*(.*?)\s+(?:T\.S\.Ward|GALA\s+NO\.|Property\s+Address)",
            "Legal_Address": r"Legal\s+Address\s+of\s+Property\s*(.*?)(?:\s+Property\s+Address\s+as\s+per\s+documents\s+submitted\s+Legal\s+Address\s+of\s+Property\s*\(.*?\)|\s+6[a-z]?\s+Property\s+address\s+as\s+per\s+site\s+visit|\s+7\s+PIN\s+Code|\s+\d+\s+Distance\s+from|\s+Name\s+of\s+the\s+Occupant|$)",
            "Nature_of_Property": r"Nature\s+of\s+Property\s*\(.*?\)\s*(?:[:\-]?\s*(.*?)\s+Propety\s+Usage|\s*(.*?)\s+Property\s+Usage)",
            "Fair_Market_Value": r"Fair\s+market\s+value\s+of\s+property\s*(.*?)\s+(?:14\s+Fair|15\s+Fair|16\s+Fair)",
            "Remarks": r"(?:2\s+Volatility\s+of\s+property\s+prices\s*\(.*?\)\s*(.*?)(?:\s+4\s+1\.\s+Details)|3\s+Volatility\s+of\s+property\s+prices\s*\(.*?\)\s*(.*?)(?:\s+1\.\s+Details\s+in\s+case)|3\s+Volatility\s+of\s+property\s+prices\s*\(.*?\)\s*(.*?)(?:4\s+REMARKS)|3\s+Volatility\s+of\s+property\s+prices\s*\(.*?\)\s*(.*?)(?:1\.\s+Details\s+in\s+case)|(1\)\s.*?)(?=1\.\s+Details\s+in\s+case))"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                for group in match.groups():
                    if group:
                        result[key] = group.strip()
                        break

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

# --------------------------------------------------------legal-------------------------------------------

# AWS Textract setup
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region_name
)
textract_client = session.client('textract')


def extract_legal_scrutiny_fields(image_bytes: bytes) -> Dict[str, str]:
    # Textract API call to analyze document using FORMS mode
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["FORMS"]
    )

    # Extract lines of text
    lines = [
        block["Text"]
        for block in response["Blocks"]
        if block["BlockType"] == "LINE" and "Text" in block
    ]

    # Combine all lines into one text block
    full_text = " ".join(lines)
    print("----- FULL TEXT -----")
    print(full_text)

    # Define regex patterns to extract required fields
    patterns = {
        # "Name_of_Applicant": r"Name of the Applicant\s*:\s*(.*?)\s*(Name of the Co|Property stands|$)",
        # "Name_of_Co_Applicants": r"Name of the Co[- ]?applicants\s*[:\-]?\s*(.*?)\s*(Property stands|$)",
        # "Property_Stands_In_Name_Of": r"Property\s*stands\s*in\s*the\s*(.*?)\s*name\s*of",
        # "SARFAESI_Enforcement": r"The Property can be enforced by SARFAESI Act\s*[:\-]?\s*(.*?)\s*(Part|$)",
        # "Final_Opinion": r"FINAL\s*OPINION\s*[:\-]?\s*(.+?)(?= Part| CERTIFICATE| In View| Yours|$)",

        # Requested additional fields
        "Borrower_Name": r"1\s+Name of the Borrower\(s\)\s+(.*?)\s+2\(a\)",
        "Owner_Name": r"2\(a\)\s+Name of the Current.*?\s+(M\/s\..+?)(?=2\(b\)|\n)",
        "SARFAESI_Enforceable": r"21\s+Whether the property is\s+(Yes|No)\s+enforceable under the provisions of Securitization",
        "Title_Certification": r"(?i)Title Certification\s*\(Certificate of title\).*?UGRO\s+CAPITAL\s+LTD\.",
        "Is_Title_Clear_Marketable": r"26\s*\(a\)\s*Whether title.*?free of encumbrance.*?\s+(Yes|No)",
        "Status": r"(?i)Status\s*[:\-]?\s*(Positive|Negative|Clear|Pending)"
    }

    # Initialize result dictionary
    result = {
        # "Name_of_Applicant": "",
        # "Name_of_Co_Applicants": "",
        # "Property_Stands_In_Name_Of": "",
        # "Type_of_Deed_Ascertaining_Title": "",
        # "Registered_Deeds": "",
        # "SARFAESI_Enforcement": "",
        # "Final_Opinion": "",
        "Borrower_Name": "",
        "Owner_Name": "",
        "SARFAESI_Enforceable": "",
        "Title_Certification": "",
        "Is_Title_Clear_Marketable": "",
        "Status": ""
    }

    # Extract deed/registration details separately
    deed_match = re.search(
        r"Type of Deed Ascertaining Title\s+Registered deeds\s+(SRO Office)\s+([\w\s]+?)(?=\s+Part|\s*$)",
        full_text,
        re.IGNORECASE
    )
    if deed_match:
        result["Type_of_Deed_Ascertaining_Title"] = deed_match.group(1).strip()
        result["Registered_Deeds"] = deed_match.group(2).strip()

    # Apply regex to extract field values
    for key, pattern in patterns.items():
        if key in result and not result[key]:
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = match.group(1).strip()

    return result
# ---------------------------------------------CERSAI DOCUMENT----------------------------------------
import re
from typing import Dict

# def extract_cersai_fields(image_bytes: bytes) -> Dict[str, str]:
#     response = textract_client.analyze_document(
#         Document={"Bytes": image_bytes},
#         FeatureTypes=["FORMS"]
#     )

    
#     lines = [
#         block["Text"]
#         for block in response["Blocks"]
#         if block["BlockType"] == "LINE" and "Text" in block
#     ]
#     full_text = " ".join(lines)
#     print(full_text)

    
#     result = {
#         "Asset_ID": re.search(r"Asset ID\s+(\d+)", full_text),
#         "Transaction_ID": re.search(r"Transaction ID\s+(\d+)", full_text),
#         "Security_Interest_ID": re.search(r"Security Interest ID\s+(\d+)", full_text),
#         "Type_of_Security_Interest": re.search(
#             r"Type Of Security Interest\s+(.*?)(?=\s+Type Of Finance|\s+Details Of Charge|\s+Entity Identification Number|$)",
#             full_text, re.IGNORECASE),
#         "Type_of_Charge": re.search(
#             r"Details Of Charge\s+(.*?)(?=\s+Entity Identification Number|$)",
#             full_text, re.IGNORECASE),
#         "Total_Secured_Amount": re.search(r"Total Secured Amount\s+([\d.]+)", full_text),
#         "Asset_Category": re.search(r"Asset Category\s+([A-Za-z]+)", full_text),
#         "Type_of_Asset": re.search(r"Type Of Asset\s+([A-Za-z]+)", full_text),
#         "Area": re.search(r"Area\s+([\d.]+)", full_text),
#         "Area_Unit": re.search(r"Area Unit\s+([A-Za-z ]+)", full_text),
#         "Property_Address": {
#             "Name_of_Society": re.search(r"Name of the Project / Scheme / Society / Zone\s+(.*?)\s+Street", full_text),
#             "Locality": re.search(r"Locality / Sector\s+(.*?)\s+City", full_text),
#             # "City": re.search(r"City / Town / Village\s+(.*?)\s+Page No", full_text, re.IGNORECASE),
#             "City": re.search(r"City / Town / Village\s+(.*?)(?=\s+District|\s+Page No|$)", full_text, re.IGNORECASE),

#             "District": None,
#             "State": None,
#             "Pincode": None
#         },
#         "Charge_Holder_Details": re.search(
#             r"Charge Holder Name\s+Office\s*/\s*Ward\s*/\s*Branch Name\s+(.*?)\s+(Original View|Page No)",
#             full_text
#         )
#     }

    
#     if "Borrower(s) Details" in full_text:
#         borrower_pattern = re.findall(
#             r"\d+\s+(Sole Proprietorship|Partnership Firm|Individual|Company)\s+([A-Z ]+?)\s+(NA|[A-Z]+)\s+(Yes|No)",
#             full_text,
#             re.IGNORECASE
#         )
#         result["Borrower_Details"] = [
#             {
#                 "Type": m[0].strip(),
#                 "Name": m[1].strip(),
#                 "Father_Mother_Name": m[2].strip(),
#                 "Is_Asset_Owner": m[3].strip()
#             }
#             for m in borrower_pattern
#         ]
#     else:
#         result["Borrower_Details"] = []

    
#     asset_owner_block_match = re.search(
#         r"Asset Owner\(s\) Details\s+(.*?)\s+Holder Details",
#         full_text,
#         re.IGNORECASE | re.DOTALL
#     )
#     if asset_owner_block_match:
#         asset_owner_block = asset_owner_block_match.group(1)
#         owner_matches = re.findall(
#             r"\d+\s+(Individual|Sole Proprietorship|Company|Firm)\s+([A-Z ]{3,})\s+([A-Z]+)",
#             asset_owner_block,
#             re.IGNORECASE
#         )
#         result["Asset_Owner_Details"] = [
#             {
#                 "Type": m[0].strip(),
#                 "Name": m[1].strip(),
#                 "Father_Mother_Name": m[2].strip()
#             }
#             for m in owner_matches
#         ]
#     else:
#         result["Asset_Owner_Details"] = []

    
#     clean_result = {}
#     for key, val in result.items():
#         if isinstance(val, re.Match):
#             clean_result[key] = val.group(1).strip()
#         elif isinstance(val, list) and val and isinstance(val[0], dict):
#             clean_result[key] = val
#         elif isinstance(val, list):
#             clean_result[key] = [v.strip() for v in val if v.strip()]
#         elif isinstance(val, dict):
#             clean_result[key] = {}
#             for sub_key, sub_val in val.items():
#                 if isinstance(sub_val, re.Match):
#                     clean_result[key][sub_key] = sub_val.group(1).strip()
#                 else:
#                     clean_result[key][sub_key] = ""
#         else:
#             clean_result[key] = ""

    
#     state_match = re.search(r"State\s*/\s*UT\s+([A-Za-z]+)(?=\s+Pin Code)", full_text, re.IGNORECASE)
#     pincode_match = re.search(r"Pin Code\s*/\s*Post Code\s+(\d{6})(?=\s|$)", full_text, re.IGNORECASE)
#     district_match = re.search(r"District\s+([A-Za-z]+)(?=\s|Page|$)", full_text, re.IGNORECASE)

#     if state_match:
#         clean_result["Property_Address"]["State"] = state_match.group(1).strip()
#     if pincode_match:
#         clean_result["Property_Address"]["Pincode"] = pincode_match.group(1).strip()
#     if district_match:
#         clean_result["Property_Address"]["District"] = district_match.group(1).strip()
#     return clean_result

def extract_cersai_fields(image_bytes: bytes) -> Dict[str, str]:
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["FORMS"]
    )

    lines = [
        block["Text"]
        for block in response["Blocks"]
        if block["BlockType"] == "LINE" and "Text" in block
    ]
    full_text = " ".join(lines)
    print("Full OCR text:\n", full_text)

    result = {
        "Asset_ID": re.search(r"Asset ID\s+(\d+)", full_text),
        "Transaction_ID": re.search(r"Transaction ID\s+(\d+)", full_text),
        "Security_Interest_ID": re.search(r"Security Interest ID\s+(\d+)", full_text),
        "Type_of_Security_Interest": re.search(
            r"Type Of Security Interest\s+(.*?)(?=\s+Type Of Finance|\s+Details Of Charge|\s+Entity Identification Number|$)",
            full_text, re.IGNORECASE),
        "Type_of_Charge": re.search(
            r"Details Of Charge\s+(.*?)(?=\s+Entity Identification Number|$)",
            full_text, re.IGNORECASE),
        "Total_Secured_Amount": re.search(r"Total Secured Amount\s+([\d.]+)", full_text),
        "Asset_Category": re.search(r"Asset Category\s+([A-Za-z]+)", full_text),
        "Type_of_Asset": re.search(r"Type Of Asset\s+([A-Za-z]+)", full_text),
        "Area": re.search(r"Area\s+([\d.]+)", full_text),
        "Area_Unit": re.search(r"Area Unit\s+([A-Za-z ]+)", full_text),
        "Property_Address": {
            "Name_of_Society": re.search(r"Name of the Project / Scheme / Society / Zone\s+(.*?)\s+Street", full_text),
            "Locality": re.search(r"Locality / Sector\s+(.*?)\s+City", full_text),
            "City": re.search(r"City / Town / Village\s+(.*?)(?=\s+District|\s+Page No|$)", full_text, re.IGNORECASE),
            "District": None,
            "State": None,
            "Pincode": None
        },
        # "Charge_Holder_Details": re.search(
        #     r"Charge Holder Name\s+Office\s*/\sWard\s/\sBranch Name\s+(.?)\s+(Original View|Page No)",
        #     full_text
        # )
        "Charge_Holder_Details": re.search(
            r"Charge Holder Name\s+Office\s*/\sWard\s*/\s*Branch Name\s+(.*?)(?=\s+(?:Page No|Original View|Borrower\(s\)|$))",
            full_text,
            re.IGNORECASE
        )
    }

    if "Borrower(s) Details" in full_text:
        borrower_pattern = re.findall(
            r"\d+\s+(Sole Proprietorship|Partnership Firm|Individual|Company)\s+([A-Z ]+?)\s+(NA|[A-Z]+)\s+(Yes|No)",
            full_text,
            re.IGNORECASE
        )
        result["Borrower_Details"] = [
            {
                "Type": m[0].strip(),
                "Name": m[1].strip(),
                "Father_Mother_Name": m[2].strip(),
                "Is_Asset_Owner": m[3].strip()
            }
            for m in borrower_pattern
        ]
    else:
        result["Borrower_Details"] = []

    asset_owner_block_match = re.search(
        r"Asset Owner\(s\) Details\s+(.*?)\s+Holder Details",
        full_text,
        re.IGNORECASE | re.DOTALL
    )
    if asset_owner_block_match:
        asset_owner_block = asset_owner_block_match.group(1)
        owner_matches = re.findall(
            r"\d+\s+(Individual|Sole Proprietorship|Company|Firm)\s+([A-Z ]{3,})\s+([A-Z]+)",
            asset_owner_block,
            re.IGNORECASE
        )
        result["Asset_Owner_Details"] = [
            {
                "Type": m[0].strip(),
                "Name": m[1].strip(),
                "Father_Mother_Name": m[2].strip()
            }
            for m in owner_matches
        ]
    else:
        result["Asset_Owner_Details"] = []

    clean_result = {}
    for key, val in result.items():
        if isinstance(val, re.Match):
            clean_result[key] = val.group(1).strip()
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            clean_result[key] = val
        elif isinstance(val, list):
            clean_result[key] = [v.strip() for v in val if v.strip()]
        elif isinstance(val, dict):
            clean_result[key] = {}
            for sub_key, sub_val in val.items():
                if isinstance(sub_val, re.Match):
                    clean_result[key][sub_key] = sub_val.group(1).strip()
                else:
                    clean_result[key][sub_key] = ""
        else:
            clean_result[key] = ""

    district_match = re.search(r"District\s*[:\-]?\s*([A-Za-z ]+?)(?=\s+State|$)", full_text, re.IGNORECASE)
    state_match = re.search(r"State\s*/\sUT\s[:\-]?\s*([A-Za-z ]+?)(?=\s+Pin Code|$)", full_text, re.IGNORECASE)
    pincode_match = re.search(r"Pin Code\s*/\sPost Code\s[:\-]?\s*(\d{6})(?=\s|$)", full_text, re.IGNORECASE)

    # print("District:", district_match.group(1) if district_match else "Not found")
    # print("State:", state_match.group(1) if state_match else "Not found")
    # print("Pincode:", pincode_match.group(1) if pincode_match else "Not found")
    if state_match:
        clean_result["Property_Address"]["State"] = state_match.group(1).strip()
    if pincode_match:
        clean_result["Property_Address"]["Pincode"] = pincode_match.group(1).strip()
    if district_match:
        clean_result["Property_Address"]["District"] = district_match.group(1).strip()

    return clean_result


def extract_modt_fields(image_bytes: bytes) -> Dict[str, str]:
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["FORMS"]
    )

    lines = [block["Text"] for block in response["Blocks"]
             if block["BlockType"] == "LINE" and "Text" in block]
    
    full_text = " ".join(lines)
    print("MODT Full OCR text:\n", full_text)

    # Robust regex matches
    deposit_date_match = re.search(
        r'on this the (\d{1,2}(?:st|nd|rd|th)?\s+day of\s+[A-Z]+\s+\d{4})',
        full_text, re.IGNORECASE
    )

    # Better name handling: captures Mr. Name S/o Father's name...
    borrower_names = re.findall(r'Mr\.?\s*([\w.\s]+?)\s*S/o', full_text)

    # Aadhar
    aadhar_nos = re.findall(r'Aadhar No\s*[:\-]?\s*(\d{4}\s\d{4}\s\d{4})', full_text)

    # Address extraction generalized for Tirupur or full line
    borrower_address_match = re.search(
        r'residing at\s+([A-Za-z0-9/\-,\s]+TIRUPUR[\- ]?\d{3,6})',
        full_text, re.IGNORECASE
    )

    # Depositee & CIN
    depositee_match = re.search(r'in favour of\s+([A-Z\s&]+),\s+a Company', full_text)
    cin_match = re.search(r'CIN\s*([A-Z0-9]+)', full_text)

    # Loan amount improved for large numbers
    loan_match = re.search(r'sum of Rs\.?\s*([\d,]+)', full_text)

    # Property plot extraction broader
    property_plots = re.findall(
        r'Plot No\.?\s*\d+.*?Tirupur.*?(?:Location|Boundaries)',
        full_text, re.IGNORECASE | re.DOTALL
    )

    # Area Extraction
    property_areas = re.findall(
        r'Total Extent\s*([0-9,]+\s*Sq\.?Ft)', full_text, re.IGNORECASE
    )

    # Clean dictionary
    cleaned = {
        "Deposit_Date": (
            deposit_date_match.group(1).replace("day of", "").strip()
            if deposit_date_match else ""
        ),
        "Borrower_Name": ", ".join([name.strip() for name in borrower_names]),
        "Aadhar_No": ", ".join(aadhar_nos),
        "Borrower_Address": (
            borrower_address_match.group(1).replace("\n", " ").strip()
            if borrower_address_match else ""
        ),
        "Depositee": (
            depositee_match.group(1).strip()
            if depositee_match else ""
        ),
        "Depositee_CIN": (
            cin_match.group(1)
            if cin_match else ""
        ),
        "Loan_Amount": (
            loan_match.group(1)
            if loan_match else ""
        ),
        "Property_Address": "; ".join(
            [p.replace("\n", " ").strip() for p in property_plots]
        ),
        "Property_Area": ", ".join(property_areas)
    }

    return cleaned