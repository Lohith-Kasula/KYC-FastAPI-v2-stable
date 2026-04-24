import tomli
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from tensorflow.keras.models import load_model
import tensorflow as tf
import keras.utils as image
import numpy as np
import matplotlib.pyplot as plt

config_file_path = "../pyproject.toml"

# Load configuration file
with open(config_file_path, mode='rb') as fp:
    config = tomli.load(fp)

def load_image(pil_image):
    # No need to open the image, it's already a PIL Image object
    img = pil_image.resize((380, 380))  # Resize if needed
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)  # Expand dims to make it (1, 256, 256, 3)
    
    return img, x
 # Corrected this to expand the correct dimension

    return img, x

def load_tf_model():
    # Load model file path from configuration
    load_model_fp = config['Tensorflow_Saved_Models']['kyc_aadhar_classifier']
    
    # Load model on CPU (since you set CUDA devices to -1)
    with tf.device('/cpu:0'):
        model = load_model(load_model_fp)

    return model

def return_truth_labels():
    # Return labels from configuration
    return config['Tensorflow_Trained_Labels']['kyc_aadhar_classifier']

from PIL import Image

def predict_doc_type(image_input, debug=True):
    # If the input is a file path, load the image
    if isinstance(image_input, str):
        pil_image = Image.open(image_input)
    else:
        pil_image = image_input

    returned_img, returned_img_array = load_image(pil_image)
    
    # The rest of your code follows...
    model = load_tf_model()
    labels = return_truth_labels()
    pred = model.predict(returned_img_array)

    y_pos = np.arange(len(labels))
    score_up = np.ravel(pred)

    if debug:
        plt.barh(y_pos, score_up, align='center', alpha=0.5)
        plt.yticks(y_pos, labels)
        plt.imshow(returned_img)
        plt.show()

    predicted_class_indices = np.argmax(pred, axis=1)
    pred_label = [labels[k] for k in predicted_class_indices]

    final_result = {'label': '', 'score': ''}

    if pred_label:
        final_result['label'] = pred_label[0]
        final_result['score'] = score_up[predicted_class_indices][0]

    return final_result




if __name__ == "__main__":
    img_path = r"C:\Users\vishak\Downloads\images_1.png"
    predict_doc_type(img_path=img_path)
