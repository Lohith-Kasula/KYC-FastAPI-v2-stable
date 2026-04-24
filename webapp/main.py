# import all nessasary librabry 

import statistics
import aws_api_handler
from datetime import date
from deepface import DeepFace
import uvicorn
import pdf_2_image
import azure_ocr
import pan_ocr.pan_response_ocr as pan_processing
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from flask.json import JSONEncoder
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import base64
from PIL import Image,ImageEnhance, ImageDraw, ImageFont
import cv2 as cv
import configparser
from collections import Counter
import io
from io import BytesIO
import numpy as np
from typing import Optional,Tuple
from urllib.parse import urlencode
from fuzzywuzzy import fuzz
import logging
import io
import dbcaller_face_app
import traceback
from typing import Optional
import statistics
import resize_image
from typing import Union
from itertools import combinations
import re
import io
import gst_ocr
import sys
sys.path.append("..")
# from aws_api_handler import aws_textract_document

from aadhar_ocr import kyc_aadhar_classifier,scripts 
from  aadhar_ocr import aadhar_response_processing as adhaar_processing
import address_extractor
from aadhar_ocr import scripts
import uuid
import os
import tomli
from fastapi.responses import JSONResponse
import pytesseract
from pydantic import BaseModel
from aws_api_handler import extract_data_from_image  
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Niraj.g\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
import logging
import os
from logging.handlers import TimedRotatingFileHandler
# Logger setup
logger = logging.getLogger("uvicorn")

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "app.log")

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8"
)

file_handler.setFormatter(formatter)

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

# Attach to uvicorn loggers
logging.getLogger("uvicorn").addHandler(file_handler)
logging.getLogger("uvicorn.error").addHandler(file_handler)
logging.getLogger("uvicorn.access").addHandler(file_handler)
#import custom_analyze
config = configparser.ConfigParser()
config.read("face_recognition.properties")
resizing_threshold = 300

config_file_path = "../pyproject.toml"

with open(config_file_path,mode='rb') as fp:
    config = tomli.load(fp)

def compare_images(src_image:str, targ_image:str, extract_faces=None):
    logger.info("Compare_images is called")
    
    if extract_faces:
        aws_result, aws_conf, aws_extracted_faces_b64_str = aws_api_handler.aws_compare_faces(src_image , targ_image, extract_faces=True)
        logger.info("returning the comparision result from the if part of compare_images function")
        return {"AWSRekognition":{"result":aws_result, "confidence_score":aws_conf, "id_image_b64_str":aws_extracted_faces_b64_str}}

    else:
        aws_result, aws_conf = aws_api_handler.aws_compare_faces(src_image , targ_image)
        logger.info("returning the comparision result from the else part of compare_images function")
        return {"AWSRekognition":{"result":aws_result, "confidence_score":aws_conf}}
    
def convert_base64_to_pcng(image):
    logger.debug("convert_base64_to_png is called\n")
    png_recovered = base64.b64decode(image)
    image = Image.open(io.BytesIO(png_recovered))
    png_picture = cv.cvtColor(np.array(image), cv.COLOR_BGR2RGB)
    
    logger.debug("base64 image is converted to png\n")
    log_contents = log_capture_string.getvalue().split('\n')
    log_contents = list(filter(None, log_contents))
    log_contents = log_contents[-1]  
    return png_picture


def detect_face_from_id(img_b64):
    logger.debug("detect_face_from_id is called\n")
    log_contents = log_capture_string.getvalue().split('\n')
    log_contents = list(filter(None, log_contents))
    log_contents = log_contents[-1]
    """
    Input: img [PIL.image]
    Output: Base64-encoded string of detected face in image
    """
    img = convert_base64_to_pcng(img_b64)
    backends = ["opencv","ssd","dlib","mtcnn","retinaface"]
    
    try:
        # Trying with 'ssd' as backend
        result = DeepFace.detectFace(img_path=img, detector_backend=backends[1])

    except ValueError as e:
        logger.error("A ValueError is occured\n")
        log_contents = log_capture_string.getvalue().split('\n')
        log_contents = list(filter(None, log_contents))
        log_contents = log_contents[-1]
        #print("log_contents: ",log_contents)
        #dbcaller_face_app.DBcaller.update_logs(log_contents.split('::')[0],log_contents.split('::')[1],log_contents.split('::')[2])
        
        if fuzz.ratio(str(e).split(".")[0],'face could not be detected') > 90 :

            try:
                logger.debug("Trying alternative method for face detection\n")
                log_contents = log_capture_string.getvalue().split('\n')
                log_contents = list(filter(None, log_contents))
                log_contents = log_contents[-1]
                
                # Trying with 'mtcnn' as backend
                result = DeepFace.detectFace(img_path=img, detector_backend=backends[3])

            except Exception as e:
                logger.error("face detection exception is occured\n")
                log_contents = log_capture_string.getvalue().split('\n')
                log_contents = list(filter(None, log_contents))
                log_contents = log_contents[-1]
                
                return f"Error in face detection (alternative method) : {str(e)}"

    logger.debug("converting the detected face into the base64 image\n")
    log_contents = log_capture_string.getvalue().split('\n')
    log_contents = list(filter(None, log_contents))
    log_contents = log_contents[-1]
    
    detected_face_image = Image.fromarray(np.uint8((result*255)), "RGB")
    detected_face_image_buffer = BytesIO()
    detected_face_image.save(detected_face_image_buffer, format="PNG")
    detected_face_b64_str = base64.b64encode(detected_face_image_buffer.getvalue())   
    return detected_face_b64_str


def base64_check(b64_str: str):
    # Format of Data URI - data:[<mediatype>][;base64],<data>
    # Eg: If text is 'Hello world' , b64 data uri is 'data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=='
    if "data" in b64_str:
        print("\n data uri detected \n")
        b64_substring = b64_str.split(",")[1].strip()
        return b64_substring
    else:
        return b64_str
#" JSON Encoder used to make sure datetime format is ISO format"
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
    
app = FastAPI(docs_url="/vkyc-swagger", redoc_url=None)
templates = Jinja2Templates(directory="templates")

app.add_middleware(
        CORSMiddleware,
        allow_origins = ['*'],
        allow_credentials = True,
        allow_methods = ['*'],
        allow_headers = ['*'],
        )
app.json_encoder = CustomJSONEncoder


@app.get("/")
def home_page():
    return RedirectResponse(url="/vkyc-swagger")


# ----------------------------------------------verify_all_images------------------------------------------------------------------------

@app.post('/verify_all_images')
def verify_all_images(request:Request,image_1:UploadFile = File(...),
    image_2:UploadFile = File(...),
    image_3:Optional[UploadFile] = File(None),
    image_4:Optional[UploadFile] = File(None)):
    
    #Constants
    images_list = [image_1.file.read(),image_2.file.read()]
    # print("images_list: ",images_list)
    image_content_type = [image_1.content_type,image_2.content_type]
    unmatched_image = []
    matched_image_bool = []
    number_of_image_upload = 2
    total_number_of_matched = 0
    total_number_of_unmatched = 0
    #code to count the number of images uploaded 
    if image_3 != None:
        number_of_image_upload += 1
        #images_list = [image_1,image_2,image_3]
        images_list.append(image_3.file.read())
        image_content_type.append(image_3.content_type)
        # print("images_list image_3: ",images_list)
    if image_4 != None:
        number_of_image_upload +=1
        # images_list = [image_1,image_2,image_3,image_4]
        images_list.append(image_4.file.read())
        image_content_type.append(image_4.content_type)
        # print("images_list image_4: ",images_list)

    #code to generate the combination of src and target images to compare
    if number_of_image_upload == 2:
        comb_index_number = [0,1]
    elif number_of_image_upload == 3:
        comb_index_number = [0,1,2]
    else:
        comb_index_number = [0,1, 2, 3]
    print("number of image upload: ",number_of_image_upload,'comb_index_number',comb_index_number)
    comb = combinations(comb_index_number, 2)
    # for j in list(comb):
    #     print("j",j)


    for i in list(comb):
        print("inside for loop: ",i)
        #getting the images as per the combination of indexes
        img_1 = images_list[i[0]]
        img_2 = images_list[i[1]]
        print("img_1",len(img_1))
        print("img_2",len(img_2))

        #Checking the types for pdfs uploads
        # img_1_type = img_1.content_type
        # img_2_type = img_2.content_type
        img_1_type = image_content_type[i[0]]
        img_2_type = image_content_type[i[1]]
        print("img_1_type",img_1_type)
        print("img_2_type",img_2_type)

        #Converting pdfs to images
        if img_1_type == 'application/pdf':
            # src_image = pdf_2_image.pdf_2_image_converter(img_1.file.read())
            src_image = pdf_2_image.pdf_2_image_converter(img_1)
            #print("src_image: ",src_image)
        else:
            src_image = img_1
        if img_2_type == 'application/pdf':
            # trg_image = pdf_2_image.pdf_2_image_converter(img_2.file.read())
            trg_image = pdf_2_image.pdf_2_image_converter(img_2)
            #print("trg_image",trg_image)
        else:
            trg_image = img_2

        # src_image = img_1.file.read()
        # trg_image = img_2.file.read()
        # src_image = img_1
        # trg_image = img_2
        # print("else src_image: ",len(src_image))
        # print("else trg_image: ",len(trg_image))
        print("else src_image: ",len(src_image))
        print("else trg_image: ",len(trg_image))
        
        #Converting the images to bytes
        src_image = base64.b64encode(src_image).decode("ascii")
        trg_image = base64.b64encode(trg_image).decode("ascii")
        print("src_image decode: ",len(src_image))
        print("trg_image decode: ",len(trg_image))

        #comparing the two images and storing the results into the list
        image_compare_result = compare_images(src_image,trg_image,True)
        print("Done with comparing")
        matched_image_bool.append(image_compare_result["AWSRekognition"]['result'])
        print("Saved the result in the matched_image_bool")

        #Storing the unmatched images in the unmatched_image list
        if not image_compare_result["AWSRekognition"]['result']:
            unmatched_image.append(image_compare_result["AWSRekognition"]["id_image_b64_str"])
            print("saved the unmatched inmage in the unmached_image list")
    
    #making the final decisions of True if all the uploaded image matches and false if anyone is unmatched
    if all(matched_image_bool):
        all_matched = True
        print("all images matched")
    else:
        all_matched=False
        print("all images didn't matched")

    try:
        total_number_of_matched =  dict(Counter(matched_image_bool))[True]
    except:
        pass
    try:
        total_number_of_unmatched = dict(Counter(matched_image_bool))[False]
    except:
        pass


    #preparing the final response to be send
    try:
        final_result = {"Matched":all_matched,"Total_number_of_image_uploaded":number_of_image_upload,"Total_number_of_image_matched":total_number_of_matched,
        "Total_number_of_image_unmatched":total_number_of_unmatched,"unmatched_image":unmatched_image}
    except:
        final_result = {"Matched":all_matched,"Total_number_of_image_uploaded":number_of_image_upload,"Total_number_of_image_matched":total_number_of_matched,
        "Total_number_of_image_unmatched":total_number_of_unmatched,"unmatched_image":unmatched_image}

    print("Final result is ready and sent")

    return final_result
# -------------------------------------------------verify all image --------------------------------------------------------------------
@app.post('/verify')
async def verify_images(request: Request, pan_id: UploadFile = File(...),
                        adhaar_front: UploadFile = File(...),
                        web_image: UploadFile = File(...)):
    '''
    Desc: Endpoint for 4 PIIs

    I/P: 
        pan_id:  PAN Card image
        adhaar_front:  Aadhar card image (Scan/Image)
        web_image: Webcam Image 

    Mandatory checks:

        Check 1 : Aadhar image (UIDAI) v/s Aadhar Card/ID 
        Check 2 : Aadhar image (UIDAI) v/s Webcam image
        Check 3:  PAN image v/s Webcam image
  
    Returns: {"verified": [bool] True/False } (if False: {"verified": [bool] True/False , "confidence": [str] "90%" } )
                {
                    'Aadhar_UIDAI,Aadhar_card':{ "verified": true/false/null, "confidence": score/null},
                    "Aadhar_UIDAI,Webcam_image" = {"verified": true/false/null, "confidence": score/null},
                    "PAN_card_image,Webcam_image" = {"verified": true/false/null, "confidence": score/null},
                    "Aadhar_UIDAI,PAN_card" = {"verified":true/false/null, "confidence": score/null}
                }
                
                Condition: 
                
                if "Aadhar_uidai, Aadhar_card" => False
                    {
                        ...
                        ...
                        "Aadhar_uidai,PAN_card": {"verified": true/false/null, "confidence": score/null}
                    }
    '''
    client_host = request.client.host
    logger.info(f"Client host: {client_host}")
    logger.info("Verify is called and the images are uploaded")

    pan_id_format = pan_id.content_type   
    adhaar_front_format = adhaar_front.content_type   
    web_image_format = web_image.content_type

    async def process_file(upload_file, content_type):
        file_bytes = await upload_file.read()
        if content_type == 'application/pdf':
            file_bytes = pdf_2_image.pdf_2_image_converter(file_bytes)
        return base64.b64encode(file_bytes).decode("ascii")

    pan_id_encoded = await process_file(pan_id, pan_id_format)
    adhaar_front_encoded = await process_file(adhaar_front, adhaar_front_format)
    web_image_encoded = await process_file(web_image, web_image_format)

    final_result = {}

    # Check 1: Aadhar Front vs. Web Image
    check_1_result = compare_images(adhaar_front_encoded, web_image_encoded, extract_faces=True)
    final_result['Aadhar_image,Webcam_image'] = {
        "verified": check_1_result["AWSRekognition"]['result'],
        "confidence": check_1_result["AWSRekognition"].get("confidence_score", 0) if check_1_result["AWSRekognition"]['result'] else 0,
        "id_image_b64_str": check_1_result["AWSRekognition"].get("id_image_b64_str", "Not Available"),
        "message": "Match" if check_1_result["AWSRekognition"]['result'] else "Aadhar front and Webcam images do not match"
    }

    # Check 2: PAN ID vs. Web Image
    check_2_result = compare_images(pan_id_encoded, web_image_encoded)
    final_result['PAN_card_image,Webcam_image'] = {
        "verified": check_2_result["AWSRekognition"]['result'],
        "confidence": check_2_result["AWSRekognition"].get("confidence_score", 0) if check_2_result["AWSRekognition"]['result'] else 0,
        "message": "Match" if check_2_result["AWSRekognition"]['result'] else "PAN card and Webcam images do not match"
    }

    # Check 3: Aadhar Front vs. PAN ID
    check_3_result = compare_images(adhaar_front_encoded, pan_id_encoded)
    final_result['Aadhar_image,PAN_card_image'] = {
        "verified": check_3_result["AWSRekognition"]['result'],
        "confidence": check_3_result["AWSRekognition"].get("confidence_score", 0) if check_3_result["AWSRekognition"]['result'] else 0,
        "id_image_b64_str": check_3_result["AWSRekognition"].get("id_image_b64_str", " "),
        "message": "Match" if check_3_result["AWSRekognition"]['result'] else "Aadhar front and PAN card images do not match"
    }

    logger.info(final_result)
    return jsonable_encoder(final_result)

# ---------------------------------------------panSignaturercrop----------------------------------------------------------------------------
import os
import json
import imutils
import torch
import torchvision
from torch.utils.data import DataLoader, random_split
# from torchvision.transforms import functional as F
# from torchvision.models.detection import FasterRCNN
# from torchvision.models.detection.rpn import AnchorGenerator
# from torchvision import transforms
from torch.utils.data import Dataset
from torchvision.transforms import ToTensor

from PIL import Image
import random
import numpy as np

import cv2
from PIL import ImageDraw

import tensorflow as tf
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
import keras.utils as image

# For reproducibility
random.seed(42)
torch.manual_seed(42)
np.random.seed(42)

# app = FastAPI()

# logger = logging.getLogger(__name__)

# resizing_threshold = 300

import tomli
import imutils
# 1.. Create Custom Dataset Class
class CustomObjectDetectionDataset(Dataset):
    def __init__(self, root_images, root_annotations, transforms=None):
        self.root_images = root_images
        self.root_annotations = root_annotations
        self.transforms = transforms

        self.imgs = list(sorted(os.listdir(root_images)))
        self.annotations = list(sorted(os.listdir(root_annotations)))

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img_name = os.path.join(self.root_images, self.imgs[idx])
        img = Image.open(img_name).convert("RGB")

        annotation_name = os.path.join(self.root_annotations, self.annotations[idx])
        with open(annotation_name) as f:
            target = json.load(f)

        shapes = target["shapes"]
        boxes = []
        for shape in shapes:
            # Extract the points of the polygon
            points = shape["points"]

            # Calculate minimum and maximum coordinates for the bounding box
            x_coords = [point[0] for point in points]
            y_coords = [point[1] for point in points]
            xmin = min(x_coords)
            ymin = min(y_coords)
            xmax = max(x_coords)
            ymax = max(y_coords)

            # Append the bounding box to the list
            boxes.append([xmin, ymin, xmax, ymax])

        # Convert boxes into a Torch tensor
        boxes = torch.as_tensor(boxes, dtype=torch.float32)

        labels = torch.ones((len(boxes)), dtype=torch.int64)
        image_id = torch.tensor([idx])

        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = image_id

        to_tensor = ToTensor()
        img = to_tensor(img)

        return img, target

# 2. Create Aadhar front-side croppper model class
class Pansignaturecrop:
    def __init__(self, type_of_crop=None, root_images_fp=None, root_annotations=None, num_epochs=None, lr=None, batch_size=None, model_path=None, state_dict=None):
        """Initialize Cropper Model class

        Args:
            root_images_fp (str, optional): Path to Root images (for training) . Defaults to None.
            root_annotations (str, optional): Path to Root annotations (for training). Defaults to None.
            num_epochs (int, optional): Number of epoch (for training). Defaults to None.
            lr (float, optional): Learning rate for model (during training). Defaults to None.
            batch_size (int, optional): Batch size to use for DataLoaders (during training). Defaults to None.
        """
        self.root_images = root_images_fp
        self.root_annotations = root_annotations
        self.lr = lr
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.model_path = model_path
        self.state_dict = state_dict
        self.type_of_crop = type_of_crop

        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        
        return
    
    def load_model(self, mode):
        """Load PyTorch model - For Train/test

        Args:
            mode (str): Train/Test
            model_path (str, optional): Path to Model class file (when mode='test'). Defaults to None.
            state_dict_path (str, optional): Path to Model State dict (when mode='test'). Defaults to None.

        Returns:
            model: Returns PyTorch model
        """
        if mode == "train":
            # Load a pre-trained version of Faster R-CNN
            model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)

            # Replace the classifier with a new one, that has num_classes which is user-defined
            num_classes = 2  # 1 class (your object) + 1 background

            # Get the number of input features for the classifier
            in_features = model.roi_heads.box_predictor.cls_score.in_features

            # Replace the pre-trained head with a new one
            model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(in_features, num_classes)

            # Transfer model to device
            model.to(self.device)

            return model

        elif mode == "test":
            # # Get the model save path - for model Class - eg: faster_rcnn_resnet_50.pt
            # self.model_path = self.model_path

            # # Get the model state dict - faster_rcnn_state_dict.pt
            # self.state_dict = self.state_dict_path

            # Load model class
            model = torch.load(self.model_path, map_location=self.device)
            
            # Load state dict for model
            model.load_state_dict(torch.load(self.state_dict, map_location=self.device)['model_state_dict'])
            
            # Transfer model to device
            model.to(self.device)

            return model

        else:
            return "Please specify parameter for load model - train/test" 
   
    def train(self):
        """Train (finetune) PyTorch model 

        Steps:
            1. Create Train, Val Datasets (using CustomObjectDetectionDataset class)
            2. Load PyTorch model (for training), along with optimizers and lr scheduler
            3. Begin Training loop (based on number of epochs specified)

        """
        # Initialize the dataset 
        root_images = self.root_images
        root_annotations = self.root_annotations

        train_dataset = CustomObjectDetectionDataset(root_images, root_annotations)
        val_dataset = CustomObjectDetectionDataset(root_images, root_annotations)

        # Define data loaders
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True, collate_fn=collate_fn)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False, collate_fn=collate_fn)

        # Set Params and start training of model
        model = self.load_model(mode='train')

        # Initialize optimizer
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=self.lr, momentum=0.9, weight_decay=0.0005)

        # Learning rate scheduler
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

        # Training loop
        num_epochs = self.num_epochs

        for epoch in range(num_epochs):
            
            for i, batch in enumerate(train_loader):
                model.train()
                try:
                    imgs, annotations = batch

                except Exception as e:
                    print(f"Error in unpacking batch {i}: {e}")
                    continue

                imgs = [img.to(self.device) for img in imgs]
                annotations = [{k: v.to(self.device) for k, v in t.items()} for t in annotations]
                loss_dict = model(imgs, annotations)
                losses = sum(loss for loss in loss_dict.values())


                optimizer.zero_grad()
                losses.backward()
                optimizer.step()

            # Update learning rate
            lr_scheduler.step()
            print(f"Epoch #{epoch} Loss: {losses.item()}")


        return
    

    def predict(self, test_img):
        """Predict on test images, using PyTorch model

        Args:
            test_img (str): Path to test image

        Returns:
            PIL.Image: Returns predicted Aadhar front cropped image, if present from Test image
        """
        self.test_img = test_img

        # Put the model in evaluation mode
        model = self.load_model(mode='test')

        model.eval()        

        # Load a sample image
        test_image = Image.open(self.test_img).convert("RGB")

        # Apply the same transformations as you did for the training images
        transform = get_transform(train=False)

        # Convert PIL Image to PyTorch tensor
        to_tensor = ToTensor()
        test_image = to_tensor(test_image)

        # Move the image to the device
        test_image = test_image.to(self.device)

        # Add a batch dimension
        test_image = test_image.unsqueeze(0)  # This will add a new dimension at the beginning, simulating a batch

        # Forward pass
        with torch.no_grad():
            prediction = model(test_image)

        # The prediction will be a list of dictionaries
        boxes = prediction[0]['boxes'].cpu().numpy()
        labels = prediction[0]['labels'].cpu().numpy()
        scores = prediction[0]['scores'].cpu().numpy()


        # Convert the PyTorch tensor image to a NumPy array
        test_image_np = test_image.cpu().numpy().squeeze().transpose(1, 2, 0)


        # Extract bounding boxes, labels, and scores
        boxes = prediction[0]['boxes'].cpu().numpy()
        labels = prediction[0]['labels'].cpu().numpy()
        scores = prediction[0]['scores'].cpu().numpy()


        # Filter out low scoring boxes (e.g., with a threshold of 0.5)
        threshold = 0.9
        filtered_indices = scores > threshold
        filtered_boxes = boxes[filtered_indices]
        filtered_labels = labels[filtered_indices]
        
        
        test_image_orig = Image.open(self.test_img).convert("RGB")

        test_image = ImageDraw.Draw(test_image_orig)

        # Plot boxes on the image
        for box, label in zip(filtered_boxes[:1], filtered_labels):
            x1, y1, x2, y2 = box
            height, width = test_image_orig.size[::-1]
            test_image_orig = test_image_orig.crop((x1,y1,x2,y2))

        return test_image_orig

# Function to show bbox in image
def show_bbox(test_image, model):
    
    model.eval()
    # Add a batch dimension
    test_image = test_image.unsqueeze(0)  # This will add a new dimension at the beginning, simulating a batch

    # Forward pass
    with torch.no_grad():
        prediction = model(test_image)

    # The prediction will be a list of dictionaries
    boxes = prediction[0]['boxes'].cpu().numpy()
    labels = prediction[0]['labels'].cpu().numpy()
    scores = prediction[0]['scores'].cpu().numpy()

    # You can then use `boxes`, `labels`, and `scores` to visualize the prediction on the original image.
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    # Convert the PyTorch tensor image to a NumPy array
    test_image_np = test_image.cpu().numpy().squeeze().transpose(1, 2, 0)

    # Create a new figure and axis to plot on
    fig, ax = plt.subplots(1)

    # Display the image
    ax.imshow(test_image_np)

    # Extract bounding boxes, labels, and scores
    boxes = prediction[0]['boxes'].cpu().numpy()
    labels = prediction[0]['labels'].cpu().numpy()
    scores = prediction[0]['scores'].cpu().numpy()

    # Filter out low scoring boxes (e.g., with a threshold of 0.5)
    threshold = 0.6
    filtered_indices = scores > threshold
    filtered_boxes = boxes[filtered_indices]
    filtered_labels = labels[filtered_indices]

    # Plot boxes on the image
    for box, label in zip(filtered_boxes, filtered_labels):
        x1, y1, x2, y2 = box
        rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        plt.text(x1, y1-5, f'Label: {label}', color='red')

    # Show the plot
    plt.show()
    
    return

# Function to evaluate Trained model on Valiation data
def evaluate_trained_model(model, val_loader, device):
    # Put the model in evaluation mode
    model.eval()

    # Initialize lists to store true and predicted labels
    true_labels = []
    pred_labels = []

    # Loop over each batch from the validation set
    for imgs, annotations in val_loader:
        imgs = [img.to(device) for img in imgs]
        annotations = [{k: v.to(device) for k, v in t.items()} for t in annotations]

        # Forward pass
        with torch.no_grad():
            prediction = model(imgs)
            
        # Get the true and predicted labels
        true_labels.extend([ann['labels'].cpu().numpy() for ann in annotations])
        pred_labels.extend([pred['labels'].cpu().numpy() for pred in prediction])

    # You can then calculate performance metrics like accuracy, precision, and recall based on `true_labels` and `pred_labels`.

    return true_labels, pred_labels

# Function to Transform train data to Tensors
def get_transform(train):
    transforms = []
    transforms.append(torchvision.transforms.ToTensor())
    if train:
        # Maybe add more transformations in the future
        pass
    return torchvision.transforms.Compose(transforms)

# Function to collate batches into tuple - for training
def collate_fn(batch):
    batch = list(filter(lambda x: x is not None, batch))
    
    return tuple(zip(*batch))
from skimage.metrics import structural_similarity as ssim

resizing_threshold = 300  # Example threshold

def save_file(file, name, req_id):
    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.file.read()
    path = f"../completed_requests/{req_id}/{name}"
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path
def resize_image(image, resolution):
    return image.resize(resolution)


def compare_ssim(path1, path2):
    # Read the images
    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)
    
    # Check if images were loaded successfully
    if img1 is None or img2 is None:
        raise ValueError("One or both images could not be loaded.")
    
    # Convert images to grayscale
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Resize images for comparison
    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))
    
    # Calculate SSIM
    similarity_value = "{:.2f}".format(ssim(img1, img2) * 100)
    print("Similarity value is ", float(similarity_value), "type=", type(similarity_value))
    
    return float(similarity_value)

# ------------------------------------------------------aadhar-ocr -----------------------------------------------------------------------
import resize_image
class IncompleteResponse(Exception):
    def __init__(self, message):
        super().__init__(message)

def clean_confidence(value):
    if isinstance(value, str):
        value = value.replace('%', '').strip()
        try:
            return float(value) / 100
        except:
            return None
    elif isinstance(value, (int, float)):
        return float(value)
    return None
@app.post("/aadhar-ocr")
async def aadhar_ocr(
    request: Request,
    adhaar_file: UploadFile = File(...),
    Name_as_in_Aadhar: str = "",
    DOB_as_in_Aadhar: str = "",
    Gender_as_in_Aadhar: str = "",
    Aadhar_no_as_in_Aadhar: str = "",
    Address_as_in_Aadhar: str = "",
    lead_id: str = "",
    client_name: str = ""

):

    import statistics
    import base64
    import io
    import os
    import uuid
    import re
    from fastapi.encoders import jsonable_encoder
    from PIL import Image

    def safe_lower(value):
        return value.lower().strip() if isinstance(value, str) else ""

    def clean_numeric(value):
        return re.sub(r"\D", "", value) if isinstance(value, str) else ""
    

    # -------------------- READ FILE --------------------
    adhaar_file_bytes = await adhaar_file.read()

    logger.info(f"Client IP: {request.client.host}")

    adhaar_front = None
    adhaar_back = None

    req_id = str(uuid.uuid4())
    req_id = lead_id + '-' + client_name + '-' + req_id
    save_dir = f"../completed_requests/{req_id}"
    os.makedirs(save_dir, exist_ok=True)

    # -------------------- DETECT FILE TYPE --------------------
    content_type = adhaar_file.content_type

    if adhaar_file_bytes[:5] == b"%PDF-":
        content_type = "application/pdf"
    elif adhaar_file_bytes[:4] == b"\x89PNG":
        content_type = "image/png"
    elif adhaar_file_bytes[:3] == b"\xff\xd8\xff":
        content_type = "image/jpeg"

    logger.info(f"Detected Content Type: {content_type}")

    # -------------------- PDF → IMAGE --------------------
    if content_type == "application/pdf":
        adhaar_file_bytes = pdf_2_image.pdf_2_image_converter(adhaar_file_bytes)
    elif content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        return {"message": "Invalid File format (Only Images/PDFs supported)"}

    # -------------------- OPEN IMAGE --------------------
    try:
        image = Image.open(io.BytesIO(adhaar_file_bytes))
        width, height = image.size

        if width < resizing_threshold or height < resizing_threshold:
            logger.info("Resizing small image")
            resized_bytes = resize_image.resize(image, (256, 256))
            image = Image.open(io.BytesIO(resized_bytes))

        elif width > 2000 and height > 2000:
            logger.info("Resizing large image")
            resized_bytes = resize_image.resize(image, (1024, 1024))
            image = Image.open(io.BytesIO(resized_bytes))

    except Exception as e:
        logger.exception("Image processing failed")
        return jsonable_encoder({"message": "Invalid image/PDF file"})

    img_save_path = f"{save_dir}/aadhaar.png"
    image.save(img_save_path)

    # -------------------- SKEW CORRECTION --------------------
    try:
        skew_corrected = scripts.skew_detection(img_save_path, debug=False)
        cv.imwrite(img_save_path, skew_corrected)
    except Exception:
        logger.warning("Skew correction failed — continuing")

    # -------------------- DOC TYPE CLASSIFICATION --------------------
    doctype = kyc_aadhar_classifier.predict_doc_type(img_save_path, debug=False)
    logger.info(f"DocType: {doctype}")

    if doctype and "label" in doctype:

        label = doctype["label"]

        if label in ['pan', 'unknown', None, '']:
            exp_msg = "Please upload Aadhar document in the Aadhar section."
            return jsonable_encoder({"message": exp_msg})

        if label == "aadhar_front":
            adhaar_front = image

        elif label == "aadhar_back":
            adhaar_back = image

        elif label in ["aadhar_scanned", "aadhar_print"]:

            # FRONT CROP
            front_cropper = scripts.AadharCropperModel(
                type_of_crop="front",
                model_path=config['PyTorch']['AadharCropperFront']['model_save_path'],
                state_dict=config['PyTorch']['AadharCropperFront']['state_dict_path']
            )

            front_crop = front_cropper.predict(img_save_path)
            if front_crop:
                adhaar_front = front_crop
                front_crop.save(f"{save_dir}/aadhar_front_cropped.png")

            # BACK CROP
            back_cropper = scripts.AadharCropperModel(
                type_of_crop="back",
                model_path=config['PyTorch']['AadharCropperBack']['model_save_path'],
                state_dict=config['PyTorch']['AadharCropperBack']['state_dict_path']
            )

            back_crop = back_cropper.predict(img_save_path)
            if back_crop:
                adhaar_back = back_crop
                back_crop.save(f"{save_dir}/aadhar_back_cropped.png")

        elif label == "aadhar_back_print":
            back_cropper = scripts.AadharCropperModel(
                type_of_crop="back",
                model_path=config['PyTorch']['AadharCropperBack']['model_save_path'],
                state_dict=config['PyTorch']['AadharCropperBack']['state_dict_path']
            )

            back_crop = back_cropper.predict(img_save_path)
            if back_crop:
                adhaar_back = back_crop
                back_crop.save(f"{save_dir}/aadhar_back_cropped.png")

        
        elif label == "aadhar_front_print":
            # FRONT CROP
            front_cropper = scripts.AadharCropperModel(
                type_of_crop="front",
                model_path=config['PyTorch']['AadharCropperFront']['model_save_path'],
                state_dict=config['PyTorch']['AadharCropperFront']['state_dict_path']
            )

            front_crop = front_cropper.predict(img_save_path)
            if front_crop:
                adhaar_front = front_crop
                front_crop.save(f"{save_dir}/aadhar_front_cropped.png")

        elif label == "pan":
            logger.info('Uploaded PAN instead of Aadhar card')

    # -------------------- CONVERT IMAGE → BASE64 --------------------
    def image_to_b64(img):
        if img is None:
            return None
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    adhaar_front_b64 = image_to_b64(adhaar_front)
    adhaar_back_b64 = image_to_b64(adhaar_back)

    # -------------------- OCR CALL --------------------
    try:
        aadhar_ocr_response = adhaar_processing.ocr_call(
            adhaar_front_b64,
            adhaar_back_b64
        )
    except Exception:
        logger.exception("OCR call failed")
        return jsonable_encoder({"message": "OCR processing failed"})

    # -------------------- RESPONSE STRUCTURE --------------------
    final_json_response = {
        'lead_id': lead_id,
        'client_name' : client_name,
        "Name": "",
        "DOB": "",
        "Gender": "",
        "Aadhaar_Number": "",
        "Address": "",
        "Bounding_Box_Front": {},
        "Bounding_Box_Back": {},
        "Accuracy_Front": "N/A",
        "Accuracy_Back": "N/A",
        "Accuracy_Overall": "N/A",
        "Pincode": "",
        "City": "",
        "State": "",
        "Fields_Missing":[],
        "Message" : "N/A"
    }

    front_details = aadhar_ocr_response.get("front_details", {})
    back_details = aadhar_ocr_response.get("back_details", {})

    # -------------------- EXTRACT FRONT --------------------
    if adhaar_front is not None:

        final_json_response["Name"] = front_details.get("Name", "")
        final_json_response["DOB"] = front_details.get("Year_of_birth/DOB", "")
        final_json_response["Gender"] = front_details.get("Gender", "")
        final_json_response["Aadhaar_Number"] = front_details.get("Adhaar_Number", "")
        final_json_response["Bounding_Box_Front"] = front_details.get("Bounding_Box", {})

        front_acc = front_details.get("Accuracy")

        if front_acc:
            final_json_response["Accuracy_Front"] = f"{front_acc}%"

    # -------------------- EXTRACT BACK --------------------
    print(f'adhaar_back : {adhaar_back}')
    if adhaar_back is not None:
        print(f'%%%%%%%%%%%%%%%%% back_details: {back_details}')
        if back_details is not None:
            final_json_response["Address"] = back_details.get("Address", "")
            final_json_response["Bounding_Box_Back"] = back_details.get("Bounding_Box", {})
        else:
            logger.info('Aadhar Back Data not Fetched')

        back_acc = back_details.get("Accuracy")
        if back_acc:
            final_json_response["Accuracy_Back"] = f"{back_acc}%"

        if not final_json_response["Aadhaar_Number"]:
            final_json_response["Aadhaar_Number"] = back_details.get("Adhaar_Number", "")

    # -------------------- CLEANUP --------------------
    final_json_response["Name"] = re.sub(r"[^a-zA-Z\s]", "", final_json_response["Name"])
    final_json_response["DOB"] = re.sub(r"[^0-9/]", "", final_json_response["DOB"])
    final_json_response["Aadhaar_Number"] = clean_numeric(final_json_response["Aadhaar_Number"])

    if safe_lower(final_json_response["Gender"]) not in ["male", "female"]:
        final_json_response["Gender"] = ""

    
    fields_extracted = {}
    req_fields = ["Name", "DOB", "Aadhaar_Number", "Gender"]

    if final_json_response["Name"] != "":
        fields_extracted["Name"] = final_json_response["Name"]
    if final_json_response["DOB"] != '':
        fields_extracted["DOB"] = final_json_response["DOB"]
    if final_json_response["Aadhaar_Number"] != '':
        fields_extracted["Aadhaar_Number"] = final_json_response["Aadhaar_Number"]
    if final_json_response["Gender"] != "":
        fields_extracted["Gender"] = final_json_response["Gender"]

    exp_msg = ''
    miss_field_msg = ''
    print(f'fields_extracted: {fields_extracted}')
    missing_fields = [f for f in req_fields if f not in list(fields_extracted.keys())]

    if len(missing_fields) >= 3:
        exp_msg = "Could not process the document. Please ensure the document is \
            clearly visible, placed close to the camera, and captured without excessive lighting."
    elif len(missing_fields) >= 1 and len(missing_fields) < 3:
        miss_field_msg = ', '.join(missing_fields)
        exp_msg = f"Partial details detected,  Fields {miss_field_msg} could not be read." 

    if exp_msg:
        return jsonable_encoder({"message": exp_msg})

    # -------------------- ADDRESS PROCESSING --------------------
    addr = final_json_response.get("Address") or ""
    if addr:
        final_json_response["Pincode"] = address_extractor.get_pincode(addr)
        final_json_response["City"], final_json_response["State"] = \
            address_extractor.extract_location(addr.title())
        final_json_response["Address"] = addr.title()

    # -------------------- OVERALL ACCURACY --------------------
    acc_values = []

    try:
        if front_details.get("Accuracy"):
            acc_values.append(float(front_details["Accuracy"]))
        if back_details.get("Accuracy"):
            acc_values.append(float(back_details["Accuracy"]))

        if acc_values:
            overall = round(statistics.mean(acc_values), 2)
            final_json_response["Accuracy_Overall"] = f"{overall}%"

    except Exception:
        logger.warning("Accuracy calculation failed")

    if (back_details is not None) or (front_details is not None):
        logger.info("Final Aadhaar OCR Response")
        logger.info(final_json_response)
    else:
        logger.info('Aadhar Back Data not Fetched')

    return jsonable_encoder(final_json_response)

#--------------------------------------------------------pan-ocr ------------------------------------------------------------------------
class WrongFile(Exception):
    def __init__(self, message):
        super().__init__(message)

def resize(image, resolution=(300, 300)):
    return image.resize(resolution)
resizing_threshold = 600

@app.post("/pan-ocr")
def pan_ocr(
    request: Request,
    pan_image: UploadFile = File(...), 
    Name_as_in_PAN: str = "",
    Fathers_Name_as_in_PAN: str = "",
    DOB_as_in_PAN: str = "",
    PAN_no_as_inPAN: str = "",
    Entity_type_as_in_PAN: str = "",
    lead_id: str = "",
    client_name: str = ""

):
    logger.info(request.client.host)
    logger.debug("pan-ocr1 API called and image uploaded")

    req_id = str(uuid.uuid4())
    req_id = lead_id + '-' + client_name + '-' + req_id
    os.makedirs(f"../completed_requests/{req_id}", exist_ok=True)

    message = "Could not process the input file"

    if pan_image:
        uploaded_filename_pan_image = pan_image.filename
        pan_image_format = pan_image.content_type
        logger.info("PAN image name: " + uploaded_filename_pan_image)
        pan_image = pan_image.file.read()

    try:
        # File type detection
        if isinstance(pan_image, bytes):
            if pan_image[:5] == b'%PDF-':
                pan_image_format = "application/pdf"
            elif pan_image[:5] == b'\x89PNG\r':
                pan_image_format = "image/png"
            elif b'\xff\xd8\xff' in pan_image[:5]:
                pan_image_format = "image/jpeg"
            else:
                return JSONResponse(content={"message": "Unsupported file type"}, status_code=400)

        # Convert to PIL Image
        if pan_image_format == 'application/pdf':
            pan_image = pdf_2_image.pdf_2_image_converter(pan_image)
            image = Image.open(io.BytesIO(pan_image))
        else:
            image = Image.open(io.BytesIO(pan_image))

        width, height = image.size
        if width < resizing_threshold or height < resizing_threshold:
            image = resize(image, (300, 300))
        elif width > 2000 and height > 2000:
            image = resize(image, (1024, 1024))

        img_save_path = f"../completed_requests/{req_id}/pan.png"
        image.save(img_save_path)

        # Skew correction
        result = scripts.skew_detection(img_save_path, debug=False)
        cv.imwrite(img_save_path, result)
        image = Image.open(img_save_path)
        

        # PAN doc classifier
        doctype_classifier_result =  kyc_aadhar_classifier.predict_doc_type(img_save_path, debug=False)


        if doctype_classifier_result['label'] !='pan':
            message = "Please upload PAN document in the PAN section."
            raise WrongFile(message)


        if doctype_classifier_result and 'label' in doctype_classifier_result:
            if doctype_classifier_result['label'] in ['aadhar_print','aadhar_scanned',"pan"]:
                pan_cropper = scripts.AadharCropperModel(
                    model_path=config['PyTorch']['panCropperFront']['model_save_path'],
                    state_dict=config['PyTorch']['panCropperFront']['state_dict_path']
                )
                cropped_img = pan_cropper.predict(img_save_path)
                if cropped_img:
                    cropped_img.save(f"../completed_requests/{req_id}/pan_cropped.png", format='png')
                    image = cropped_img

        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        pan_image = base64.b64encode(buffered.getvalue()).decode("ascii")

    except Exception as e:
        logger.error(message, exc_info=True)
        return JSONResponse(content={"message": message}, status_code=400)
        # return JSONResponse(content={"message": "Could not process the input file"}, status_code=400)

    final_json_response = {
        'lead_id': lead_id,
        'client_name' : client_name,
        'Name': '',
        "Father's_Name": '',
        'DOB': '',
        'PAN_Number': '',
        'Entity_type': '',
        'Accuracy': ''
    }

    pan_details = {
        "First_Name": Name_as_in_PAN,
        "Fathers_Name": Fathers_Name_as_in_PAN,
        "DOB": DOB_as_in_PAN,
        "PAN_Number": PAN_no_as_inPAN,
        "Entity_Type": Entity_type_as_in_PAN
    }

    try:
        azure_response = azure_ocr.azure_call(pan_image)
        pan_ocr_response = pan_processing.map_kv_pairs(azure_response)

        if any(list(pan_details.values())):
            conf_counter = {k: False for k in pan_details}

            final_json_response['Name'] = pan_ocr_response.get("First_Name", "")
            final_json_response["Father's_Name"] = pan_ocr_response.get("Fathers_Name", "")
            final_json_response['DOB'] = pan_ocr_response.get("DOB", "")
            final_json_response["PAN_Number"] = pan_ocr_response.get("PAN_Number", "").strip()
            final_json_response["Entity_type"] = pan_ocr_response.get("Entity_Type", "")

            if fuzz.ratio(pan_details["First_Name"].lower(), pan_ocr_response.get("First_Name", "").lower()) > 95:
                conf_counter["First_Name"] = True
            if fuzz.ratio(pan_details["Fathers_Name"].lower(), pan_ocr_response.get("Fathers_Name", "").lower()) > 95:
                conf_counter["Fathers_Name"] = True
            if pan_details["DOB"].lower() == pan_ocr_response.get("DOB", "").lower():
                conf_counter["DOB"] = True
            if pan_details["PAN_Number"].lower().strip() == pan_ocr_response.get("PAN_Number", "").lower().strip():
                conf_counter["PAN_Number"] = True
            if fuzz.ratio(pan_details["Entity_Type"].lower(), pan_ocr_response.get("Entity_Type", "").lower()) > 95:
                conf_counter["Entity_Type"] = True

            return jsonable_encoder(final_json_response)

        else:
            if pan_ocr_response.get("Is_company"):
                final_json_response = {
                    'Name': pan_ocr_response.get("Company_Name", ""),
                    'DOI': pan_ocr_response.get("DOI", ""),
                    'PAN_Number': pan_ocr_response.get("PAN_Number", "").strip(),
                    'Entity_type': pan_ocr_response.get("Entity_Type", ""),
                    'Bounding_Box': pan_ocr_response.get("Bounding_Box", ""),
                    'Accuracy': str(round(pan_ocr_response.get("Accuracy", 0))) + '%'
                }
            else:
                final_json_response = {
                    'Name': pan_ocr_response.get("First_Name", ""),
                    "Father's_Name": pan_ocr_response.get("Fathers_Name", ""),
                    'DOB': pan_ocr_response.get("DOB", ""),
                    'PAN_Number': pan_ocr_response.get("PAN_Number", "").strip(),
                    'Entity_type': pan_ocr_response.get("Entity_Type", ""),
                    'Bounding_Box': pan_ocr_response.get("Bounding_Box", ""),
                    'Accuracy': str(round(pan_ocr_response.get("Accuracy", 0))) + '%'
                }

            return jsonable_encoder(final_json_response)

    except Exception as e:
        logger.error("Exception in PAN OCR processing", exc_info=True)
        return JSONResponse(content={"message": "Could not process the input file"}, status_code=400)
        
    
  #--------------------------------------------------ocr ------------------------------------------------------------------------------

@app.post('/ocr')
def ocr_api(
    request: Request,
    Name_as_in_Aadhar: str = "",
    DOB_as_in_Aadhar: str = "",
    Gender_as_in_Aadhar: str = "",
    Aadhar_no_as_in_Aadhar: str = "",
    Address_as_in_Aadhar: str = "",
    Name_as_in_PAN: str = "",
    Fathers_Name_as_in_PAN: str = "",
    DOB_as_in_PAN: str = "",
    PAN_no_as_inPAN: str = "",
    Entity_type_as_in_PAN: str = "",
    pan_id: bytes = File(...),
    adhaar_front: bytes = File(...),
    # aadhar_back: bytes = File(...),
  ):
  
    logger.debug("ocr api is called\n")
    log_contents = log_capture_string.getvalue().split('\n')
    log_contents = list(filter(None, log_contents))
    log_contents = log_contents[-1]
    #print("log_contents: ",log_contents)
    #dbcaller_face_app.DBcaller.update_logs(log_contents.split('::')[0],log_contents.split('::')[1],log_contents.split('::')[2])
    
    '''
    Desc : Endpoint for both Adhaar card and Pan card

    I/P: Adhaar details(Optional) for verification, pan details(Optional) for verification , pan id image, adhaar front image, adhaar back image
    
    Adhaar Details format:
    
        Example

                "Name_as_in_Aadhar": "Abhay Pandey",
                "DOB_as_in_Aadhar": "19/09/2008",
                "Gender_as_in_Aadhar": " MALE",
                "Aadhar_no_as_in_Aadhar": "7048 0974 1779",
                "Address_as_in_Aadhar": "S/O Ganpat Singh, Singhasan, Singhasan, Sikar, Rajasthan, 332027"
            
            
    Pan Details Format: 
        
        Example
        
               
                "Name_as_in_PAN": "MONIKA MAHADEV SHINDE",
                "Fathers_Name_as_in_PAN": "MAHADEV SHINDE",
                "DOB_as_in_PAN": "31/10/1992",
                "PAN_no_as_inPAN": "EJAXXXXXXX",
                "Entity_type_as_in_PAN": "Person (Individual)"
            
        
    
    O/P:
     
     Returns 
     
        { 
            aadhar_result: {
                        'Name' : 'Vishwajeeth',
                        'DOB' : '1/1/1995',
                        'Gender' : 'Male',
                        'Aadhaar_Number' : '1234 5678 9012',
                        'Address' : 'S/O Ganpat Singh, Singhasan, Singhasan, Sikar, Rajasthan, 332027',
                        'isVerified' : 'True/False/NA',
                    }

            pan_result: {
                    'Name' : 'MONIKA MAHADEV SHINDE',
                    "Father's_Name" : 'MAHADEV SHINDE',
                    'DOB' : '31/10/1992',
                    'PAN_Number' : 'EJAXXXXXXX',
                    'Entity_type' : 'Person (Individual)',
                    'isVerified' : 'True/False',
                }
         }
    '''     
   
    
    root_url = "127.0.0.1:8000"
    aadhar_result = aadhar_ocr(request,adhaar_front,
                            # aadhar_back,
                            Name_as_in_Aadhar,
                            DOB_as_in_Aadhar,
                            Gender_as_in_Aadhar,
                            Aadhar_no_as_in_Aadhar,
                            Address_as_in_Aadhar)


    pan_id = pan_ocr(request,pan_id,
                    Name_as_in_PAN,
                    Fathers_Name_as_in_PAN,
                    DOB_as_in_PAN,
                    PAN_no_as_inPAN,
                    Entity_type_as_in_PAN)

    # #Is verified code ends here
    logger.info(jsonable_encoder({'aadhar_result':aadhar_result, 'pan_result': pan_id}))
    return jsonable_encoder({'aadhar_result':aadhar_result, 'pan_result': pan_id})

#--------------------------------------------------face-ocr-verification-----------------------------------------------------------------
@app.post('/face-ocr-verification')
def total_verification(
    request: Request,\
    Name_as_in_Aadhar: str = "",
    DOB_as_in_Aadhar: str = "",
    Gender_as_in_Aadhar: str = "",
    Aadhar_no_as_in_Aadhar: str = "",
    Address_as_in_Aadhar: str = "",\
    Name_as_in_PAN: str = "",
    Fathers_Name_as_in_PAN: str = "",
    DOB_as_in_PAN: str = "",
    PAN_no_as_inPAN: str = "",
    Entity_type_as_in_PAN: str = "",
    pan_id:UploadFile = File(...),\
    adhaar_front:UploadFile = File(...),\
    adhaar_back:UploadFile = File(...),
    adhaar_uidai:UploadFile = File(...),\
    web_image:UploadFile = File(...),\
    ):

    logger.debug("face-ocr-verification api is called\n")
    log_contents = log_capture_string.getvalue().split('\n')
    log_contents = list(filter(None, log_contents))
    log_contents = log_contents[-1]
    
    '''
    Dec : Endpoint for all i.e face verify, pan ocr and adhaar ocr
    
    I/P: Pan Details (optional for verification) , Adhaar Details(Optional for verification), Pan id image, Adhaar front image, Adhaar back image
         Adhaar Uidai image, Webcam Image

    Adhaar Details format:
    
        Example

                "Name_as_in_Aadhar": "Abhay Pandey",
                "DOB_as_in_Aadhar": "19/09/2008",
                "Gender_as_in_Aadhar": " MALE",
                "Aadhar_no_as_in_Aadhar": "7048 0974 1779",
                "Address_as_in_Aadhar": "S/O Ganpat Singh, Singhasan, Singhasan, Sikar, Rajasthan, 332027"
            
            
    Pan Details Format: 
        
        Example
        
               
                "Name_as_in_PAN": "MONIKA MAHADEV SHINDE",
                "Fathers_Name_as_in_PAN": "MAHADEV SHINDE",
                "DOB_as_in_PAN": "31/10/1992",
                "PAN_no_as_inPAN": "EJAXXXXXXX",
                "Entity_type_as_in_PAN": "Person (Individual)"
            
        
            
    O/P:

        {  

        "Image-verification":

                {
                    
                    'Aadhar_UIDAI,Aadhar_card':{ "verified": true/false/null, "confidence": score/null},
                    "Aadhar_UIDAI,Webcam_image" = {"verified": true/false/null, "confidence": score/null},
                    "PAN_card_image,Webcam_image" = {"verified": true/false/null, "confidence": score/null},
                    "Aadhar_UIDAI,PAN_card" = {"verified":ture/false/null, "confidence": score/null}
                
                }

        "OCR-Verification": { 
            
            aadhar_result: 
                {
                        'Name' : 'Vishwajeeth',
                        'DOB' : '1/1/1995',
                        'Gender' : 'Male',
                        'Aadhaar_Number' : '1234 5678 9012',
                        'Address' : 'S/O Ganpat Singh, Singhasan, Singhasan, Sikar, Rajasthan, 332027',
                        'isVerified' : 'True/False/NA',
                }

            pan_result: 
            
                {
                    'Name' : 'MONIKA MAHADEV SHINDE',
                    "Father's_Name" : 'MAHADEV SHINDE',
                    'DOB' : '31/10/1992',
                    'PAN_Number' : 'EJAXXXXXXX',
                    'Entity_type' : 'Person (Individual)',
                    'isVerified' : 'True/False',
                }
            }
        }

    '''

  

    pan_id = pan_id.file.read()
    adhaar_front= adhaar_front.file.read()
    adhaar_back = adhaar_back.file.read()
    adhaar_uidai = adhaar_uidai.file.read()
    web_image = web_image.file.read()

    root_url = "127.0.0.1:8000"
    verification_resp = verify_images(pan_id, adhaar_front, adhaar_uidai, web_image)
    ocr_results = ocr_api( 
        Name_as_in_Aadhar,
        DOB_as_in_Aadhar,
        Gender_as_in_Aadhar,
        Aadhar_no_as_in_Aadhar,
        Address_as_in_Aadhar,
        Name_as_in_PAN,
        Fathers_Name_as_in_PAN,
        DOB_as_in_PAN,
        PAN_no_as_inPAN,
        Entity_type_as_in_PAN,
        pan_id,adhaar_front, adhaar_back)
    
    logger.info(jsonable_encoder({'Image-verification':verification_resp,'OCR-Verification':ocr_results}))
    return jsonable_encoder({'Image-verification':verification_resp,'OCR-Verification':ocr_results})

#--------------------------------------------verify-doc--------------------------------------------------------------------------------------    
@app.post('/verify-doc')
def verify_doc(verify_img: UploadFile = File(...)):

    if verify_img:
        verify_img = verify_img.file.read()
        verify_img_b64 = base64.b64encode(verify_img).decode("ascii")

    data = azure_ocr.azure_call(verify_img_b64)
    lines_data = data['analyzeResult']['readResults'][0]['lines']
    
    accuracy_arr = [words_dict['confidence'] for dict_obj in lines_data for words_dict in dict_obj['words']]

    avg_accuracy = sum(accuracy_arr)/len(accuracy_arr)

    if avg_accuracy > 0.80:
        return {"Status": "Document quality above threshold (Good)"}        
    else:
        return {"Status": "Document quality below threshold (Poor)"}        

    return


if __name__ == "__main__":
    # ip_addr = config.get("FastAPI","host")
    # port_no = config.get("FastAPI","port")-
    uvicorn.run("main:app",host="192.168.0.18", port=1336)
    # uvicorn.run("main:app", host="192.168.0.10", port=1336)
    # uvicorn.run("face_app:app", host="192.168.0.37", port="1339")

