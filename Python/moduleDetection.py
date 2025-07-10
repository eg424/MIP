"""
Precisely detects centroids of modules in all configurations.

- "detect_modules" is called in main.py for trajectory tracking.
- "process_image" and "process_frame" are used in this script under
different modes.
    * Both functions crop the workspace according to black values,
      rather than manually.

Modes:
- loop: process all images in the "Images" folder
- single: process one specific image file
- live: live camera feed processing. 
    * NOTE: Cannot be run simultaneously with main.py,
      close the terminal before, or use a different mode.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# Select 'loop', 'single', or 'live' 
mode = 'live' 

# Paths for image files/folder for modes
folder_path = r'C:\Users\erikg\MIP\Python\Images'  # Loop mode
single_image_path = r'C:\Users\erikg\MIP\Python\Images\4mod2ch2liq.png'  # Change accordingly

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
        if area < 500 or area > 20000:
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        bounding_boxes.append((x_cnt, y_cnt, w_cnt, h_cnt))
        aspect_ratio = w_cnt / float(h_cnt)

        if aspect_ratio < 0.4 or aspect_ratio > 2.2:
            #print(f"Rejected contour {i} due to aspect ratio: {aspect_ratio:.2f}")
            continue

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centroids.append((cX, cY))
            areas.append(area)

    # Return centroids, bounding boxes relative to cropped image, and fixed crop offset for original image reference
    return centroids, bounding_boxes, (x, y, w, h)


def process_image(img, filename=""):
    """
    Process a single image (BGR numpy array) and show matplotlib plots.
    """
    # print(f"File name: {filename}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    workspace_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(workspace_contour)
    # print(f"Workspace bounding box: x={x}, y={y}, w={w}, h={h}")

    cropped = gray[y:y + h, x:x + w]
    blurred_cropped = cv2.medianBlur(cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 82, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # print(f"Found {len(contours)} contours in cropped image.")

    centroids = []
    areas = []

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 700 or area > 20000:
            # print(f"Rejected contour {i} due to area: {area}")
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        aspect_ratio = w_cnt / h_cnt
        # print(f"Contour {i} aspect ratio: {aspect_ratio:.2f}")

        if aspect_ratio < 0.4 or aspect_ratio > 2.2:
            # print(f"Rejected contour {i} due to aspect ratio: {aspect_ratio:.2f}")
            continue
        if x_cnt < 5 or y_cnt < 5 or x_cnt + w_cnt > cropped.shape[1] - 5 or y_cnt + h_cnt > cropped.shape[0] - 5:
            # print(f"Rejected contour {i} near border.")
            continue

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centroids.append((cX, cY))
            areas.append(area)
            # print(f"Contour {i} accepted. Centroid: ({cX}, {cY}), Area: {int(area)}")

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(12, 5))

    axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    axes[0].set_title(f'Original Image: {filename}')
    axes[0].axis('off')

    axes[1].imshow(cropped, cmap='gray')
    axes[1].set_title('Auto-cropped Greyscale')
    axes[1].axis('off')

    axes[2].imshow(closed, cmap='gray')
    for (cx, cy), area in zip(centroids, areas):
        axes[2].scatter(cx, cy, color='red', s=50)
        axes[2].text(cx + 5, cy, f"{int(area)}", color='green')
    axes[2].set_title('Groups and Centroid(s)')
    axes[2].axis('off')

    plt.tight_layout()
    plt.show()


def process_frame(frame):
    """
    Process a single video frame (BGR numpy array) and return frame with overlays.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return frame

    workspace_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(workspace_contour)

    # Draw workspace bounding box (blue)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cropped = gray[y:y + h, x:x + w]
    blurred_cropped = cv2.medianBlur(cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 82, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 700 or area > 20000:
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        aspect_ratio = w_cnt / h_cnt
        if aspect_ratio < 0.4 or aspect_ratio > 2.2:
            continue
        if x_cnt < 5 or y_cnt < 5 or x_cnt + w_cnt > cropped.shape[1] - 5 or y_cnt + h_cnt > cropped.shape[0] - 5:
            continue

        # Draw rectangles (green)
        top_left = (x + x_cnt, y + y_cnt)
        bottom_right = (x + x_cnt + w_cnt, y + y_cnt + h_cnt)
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0))

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"]) + x
            cY = int(M["m01"] / M["m00"]) + y
            cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)

    return frame


def live_mode():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) 
    if not cap.isOpened():
        print("Error: Could not open video capture. Close other terminals using the camera and try again.")
        return

    print("Press 'q' to quit live view.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        processed_frame = process_frame(frame)
        cv2.imshow("Live Module Detection", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if mode == 'loop':
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        for filename in image_files:
            full_path = os.path.join(folder_path, filename)
            img = cv2.imread(full_path)
            if img is not None:
                process_image(img, filename)
            else:
                print(f"Failed to load {filename}")

    elif mode == 'single':
        img = cv2.imread(single_image_path)
        if img is not None:
            process_image(img, os.path.basename(single_image_path))
        else:
            print(f"Failed to load {single_image_path}")

    elif mode == 'live':
        live_mode()

    else:
        print("Invalid mode selected. Choose 'loop', 'single', or 'live'.")