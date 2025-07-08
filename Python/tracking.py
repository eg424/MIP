import cv2
import numpy as np

def detect_modules(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Manual fixed crop coordinates and size
    y, x = 10, 200
    h, w = 335, 340
    cropped = gray[y:y+h, x:x+w]

    # Further processing for detecting modules (white squares)
    blurred_cropped = cv2.medianBlur(cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 82, 255, cv2.THRESH_BINARY)

    # Morphological closing to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)

    # Find contours in cropped processed image
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centroids = []
    areas = []
    bounding_boxes = []

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 1000 or area > 20000:
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        bounding_boxes.append((x_cnt, y_cnt, w_cnt, h_cnt))
        aspect_ratio = w_cnt / float(h_cnt)

        if aspect_ratio < 0.4 or aspect_ratio > 2.2:
            print(f"Rejected contour {i} due to aspect ratio: {aspect_ratio:.2f}")
            continue

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centroids.append((cX, cY))
            areas.append(area)

    # Return centroids, bounding boxes relative to cropped image, and fixed crop offset for original image reference
    return centroids, bounding_boxes, (x, y, w, h)