import base64
import json
import requests
import time
from PIL import Image
from io import BytesIO
import configparser
import logging
logger = logging.getLogger("uvicorn")

# Add your Computer Vision subscription key and endpoint to your environment variables.
config = configparser.ConfigParser()
config.read("face_recognition.properties")

subscription_key = config.get('AzureComputerVision', 'subscription_key')
endpoint = config.get('AzureComputerVision', 'endpoint')

ocr_url = endpoint + "vision/v3.1/ocr"
params = {'language': 'en', 'detectOrientation': 'true'}

# img_counter = 1

def azure_call(image_string):
    # Read the image into a byte array
    image_bytes = base64.b64decode(image_string)
    # with open(r'E:\DS-Team\OCR_Demo_samples\Face_recognition_Aadhar_PAN\aadhar\New files - aadhar\ab_bmp.png','w') as f:
    #     f.write(image_bytes)
    #image_bmp = Image.open(BytesIO(image_bytes))
    #image_bmp.save(r'E:\DS-Team\OCR_Demo_samples\Face_recognition_Aadhar_PAN\aadhar\New files - aadhar\ab_bmp.png')
    
    #print(len(image_data))
    text_recognition_url = endpoint + "/vision/v3.1/read/analyze"

    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
               'Content-Type': "application/octet-stream"}
    #data = {'url': image_data}

    response = requests.post(
        text_recognition_url, headers=headers,  data=image_bytes) #language='en',
    #print(response, response.json())
    response.raise_for_status()
    logger.info(f"azure_call {response}")


   

    # Holds the URI used to retrieve the recognized text.
    #operation_url = response.headers["Operation-Location"]

    # The recognized text isn't immediately available, so poll to wait for completion.
    analysis = {}

    poll = True
    while (poll):
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()

        #print(json.dumps(analysis, indent=4))

        time.sleep(1)
        if ("analyzeResult" in analysis):
            poll = False
        if ("status" in analysis and analysis['status'] == 'failed'):
            poll = False


    # Saving the output as json
    # with open(f"new_res.json", 'w') as file: #datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    #    json.dump(analysis,file, indent=4)

    return analysis
