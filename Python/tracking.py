import cv2
import numpy as np

def detect_modules(frame):
    # Detect white squares
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crop to workspace
    cropped = gray[0:490, 270:810]

    # Median Blur
    blurred = cv2.medianBlur(cropped, 5)

    # Threshold
    _, th = cv2.threshold(blurred, 82, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def is_square(cnt):
        area = cv2.contourArea(cnt)
        if area < 300:  # Reject small noise
            return False
        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            return False
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        return 0.85 <= aspect_ratio <= 1.15

    # Find square centroids
    centroids = []
    bounding_boxes = []
    for cnt in contours:
        if is_square(cnt):
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                centroids.append((cX, cY))
                
                x, y, w, h = cv2.boundingRect(cnt)
                bounding_boxes.append((x, y, w, h))
    return centroids, bounding_boxes