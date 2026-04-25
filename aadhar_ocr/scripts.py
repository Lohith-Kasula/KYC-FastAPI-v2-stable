'''
Description: Python Scripts for PyTorch Model Training, Inference
Author: Vishak G.
Created on: 2023-09-06
'''

# 1. Import libraries
import os
import json
import imutils
import torch
import torchvision
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

import tomli
import imutils

config_path = "../pyproject.toml"

with open(config_path,mode='rb') as fp:
    config = tomli.load(fp) 


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
class AadharCropperModel:
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
            model = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
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

# Add skew detection code here
# skewwd detection
# def corrected_skew(image_path, model):
#     img = image.load_img(img_path, target_size=(256,256))
#     x = image.img_to_array(img)
#     x = np.expand_dims(img, axis=0)

#     ind_pred = model_whole_final.predict(x)
#     y_pos = np.arange(len(labels))
#     score = ind_pred
#     score_up = np.ravel(score)
#     plt.barh(y_pos, score_up, align='center', alpha=0.5)
#     plt.yticks(y_pos, labels)
#     plt.title("prediction")
#     plt.show()
#     plt.imshow(img)
#     plt.show()
#     print("predicted:", score)

#     image_path = 


class SkewDetectionModel:
    def __init__(self, img_path, labels, mode="train", model_path=None):
        self.model_path = model_path
        self.img_path = img_path
        self.labels = labels
        self.mode = mode

    
    def load_img(self):
        img = image.load_img(self.img_path, target_size=(256,256))
        x = image.img_to_array(img)
        x = np.expand_dims(img, axis=0)

        return x ,img
    
    def load_model(self):

        with tf.device('/cpu:0'):
            model = load_model(self.model_path)

        return model

    def predict(self):
        # Image (PIL)
        x, img = self.load_img()
        model_whole_final = self.load_model()

        ind_pred = model_whole_final.predict(x)
        y_pos = np.arange(len(self.labels))
        score = ind_pred
        score_up = np.ravel(score)
        # plt.barh(y_pos, score_up, align='center', alpha=0.5)
        # plt.yticks(y_pos, self.labels)
        # plt.title("prediction")
        # plt.show()
        # plt.imshow(img)
        # plt.show()
        # print("predicted:", score)

        predicted_class_indices=np.argmax(ind_pred,axis=1)
        pred_label = [self.labels[k] for k in predicted_class_indices]

        print(pred_label)

        return pred_label

def skew_detection(img_save_path,debug = False):

    skew_detection_model = SkewDetectionModel(
    img_path=img_save_path, 
    mode="test",
    model_path=config['Tensorflow_Saved_Models']['skew_detection_model'],
    labels=['-90', '0', '90']
    )
    predictions = skew_detection_model.predict()
    img = cv2.imread(img_save_path)
    angle = int(predictions[0])
    
    if angle == 90:
        corrected_image = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == -90:
        corrected_image = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif angle == 0:
        corrected_image = img
    else:
        corrected_image = cv2.rotate(img, cv2.ROTATE_180)
    return corrected_image 



if __name__ == "__main__":
    import tomli
    import imutils

    config_path = "../pyproject.toml"

    with open(config_path,mode='rb') as fp:
        config = tomli.load(fp) 

    print(config['Tensorflow_Saved_Models']['skew_detection_model'])
    skew_detection_model = SkewDetectionModel(img_path=r"E:\D07.Niraj G\Chrome Download\Paassport220744 (2).png", mode="test", model_path=config['Tensorflow_Saved_Models']['skew_detection_model'], labels=['-90', '0', '90'])
    predictions = skew_detection_model.predict()
    

    img_path=r"E:\D07.Niraj G\Chrome Download\Paassport220744 (2).png"
    img = cv2.imread(img_path)
    angle=int(predictions[0])

    if angle == 90:
        corrected_image = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    elif angle == -90:
        corrected_image = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif angle == 0:
         corrected_image =img    
         
    else:
      corrected_image = cv2.rotate(img, cv2.ROTATE_180)
    # img_path = r"V:\skewed_images_sample\9463df3b-242e-4161-9e9b-4770028e9d95\aadhaar.png"
    # img = cv2.imread(img_path)


    # image = cv2.rotate(img, angle=int(predictions[0]))

    cv2.imshow("corrected image", corrected_image)
    cv2.waitKey(0)