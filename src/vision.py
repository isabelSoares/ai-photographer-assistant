"""
Visualize Detections
============================

This script draws bounding boxes on your photos to show WHERE
the model detected people. Saves annotated images to the outputs/ folder.

WHAT YOU'LL SEE:
- Green rectangles around each detected person
- A confidence score label on each box (e.g., "Person 0.92")
- The original image is NOT modified (we save copies)

HOW DRAWING WORKS (OpenCV basics):
- Images are loaded as NumPy arrays of shape (height, width, 3)
- Each pixel is 3 values: Blue, Green, Red (BGR, not RGB!)
- cv2.rectangle() draws a box by modifying pixel values
- cv2.putText() draws text the same way

Usage:
    python src/visualize_detections.py --input ./src/data/assets
    python src/visualize_detections.py --input ./src/data/assets/photo.jpeg --confidence 0.3
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# Supported image formats
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

# Visual settings for the bounding boxes
BOX_COLOR = (0, 255, 0)  # Green in BGR format
BOX_THICKNESS = 2         # Pixels
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.6
FONT_COLOR = (0, 255, 0)  # Green text
FONT_THICKNESS = 2


def draw_detections(image: np.ndarray, detections: list) -> np.ndarray:
    """
    Draw bounding boxes and labels on the image.

    This is where the "computer vision" visualization happens:
    - We're directly manipulating the image pixel array
    - Each detection gets a rectangle and a label

    Args:
        image (np.ndarray): The input image as a NumPy array.
        detections (list): A list of detections, where each detection is a dictionary
                           with keys 'box' (bounding box coordinates) and 'label' (class name).

    Returns:
        np.ndarray: The image with bounding boxes and labels drawn.
    """
    for detection in detections:
        box = detection['box']  # Bounding box coordinates (x1, y1, x2, y2)
        label = detection['label']  # Class label

        # Draw the bounding box
        cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), BOX_COLOR, BOX_THICKNESS)

        # Draw the label above the bounding box
        label_position = (box[0], box[1] - 10 if box[1] - 10 > 10 else box[1] + 10)
        cv2.putText(image, label, label_position, FONT, FONT_SCALE, FONT_COLOR, FONT_THICKNESS)

    return image