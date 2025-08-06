"""
Precisely detects centroids of modules in all configurations
and distance between them.

- "detect_modules" is called in main.py for trajectory tracking.
- "process_image" and "process_frame" are used in this script under
different modes.
    * process_image crops the workspace according to black values,
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
import itertools

# Constants
y, x = 20, 180
h, w = 325, 325
pixels_per_mm = 271 / 32

# Select 'loop', 'single', or 'live' 
mode = 'live' 

# Paths for image files/folder for modes
folder_path = r'C:\Users\erikg\MIP\Python\Images'  # Loop mode
single_image_path = r'C:\Users\erikg\MIP\Python\Images\4mod2ch2liq.png'  # Change accordingly


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
        if area < 500 or area > 20000:
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


def detect_modules(frame):
    # Binary colourspace
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_cropped = gray[y:y + h, x:x + w]

    # Omit red regions for module detection    
    frame, red_mask, red_contours = detect_walls(frame)
    gray_cropped[red_mask > 0] = 0
    
    # Median blur and binary thresholding
    blurred_cropped = cv2.medianBlur(gray_cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 82, 255, cv2.THRESH_BINARY)

    # Find contours of the thresholded image
    contours, _ = cv2.findContours(th_cropped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centroids = []
    module_boxes = []
    aspect_ratios = []

    # Detect modules
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500 or area > 20000:
            continue
        
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect).astype(int)
        box += np.array([x, y])

        width, height = rect[1]
        if height == 0:
            continue

        aspect_ratio = min(width, height) / max(width, height)        
        if aspect_ratio < 0.2 or aspect_ratio > 2.2:
            continue
        aspect_ratios.append(aspect_ratio)
        
        structure = "Unknown"
        if area < 1000:
            structure = "Module"
        elif 0.2 <= aspect_ratio < 0.6:
            structure = "Chain"
        elif 0.6 <= aspect_ratio < 0.9 and area > 1000:
            structure = "Gripper"
        elif 0.9 <= aspect_ratio <= 1.1:
            structure = "Square"

        elif 0.9 <= aspect_ratio < 0.95 and area > 3000:
            structure = "Ring"
        
        # Draw boundaries of detected module/structure
        cv2.drawContours(frame, [box], 0, (0, 255, 0))
        module_boxes.append(box)

        # Calculate centroid(s)
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"]) + x
            cY = int(M["m01"] / M["m00"]) + y
            centroids.append((cX, cY))
            cv2.circle(frame, (cX, cY), 2, (0, 0, 255), -1)
            cv2.putText(frame, structure, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # for i, ar in enumerate(aspect_ratios, 1):
    #     print(f"Module {i} aspect ratio: {ar:.2f}")
    
    draw_im_dist(frame, centroids, pixels_per_mm)

    return centroids, module_boxes


def draw_im_dist(frame, centroids, pixels_per_mm):
    for (pt1, pt2) in itertools.combinations(centroids, 2):
        dx = pt2[0] - pt1[0]
        dy = pt2[1] - pt1[1]
        pixel_distance = np.hypot(dx, dy)
        mm_distance = pixel_distance / pixels_per_mm

        mid_point = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)

        cv2.line(frame, pt1, pt2, (255, 255, 0), 1)
        cv2.putText(frame, f"{mm_distance:.1f} mm", mid_point,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def detect_walls(frame):
    # HSV colourspace
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_cropped = hsv[y:y + h, x:x + w]
    
    # Thresholding values
    lower_red1 = np.array([0, 20, 80])
    upper_red1 = np.array([25, 255, 255])
    lower_red2 = np.array([160, 20, 80])
    upper_red2 = np.array([180, 255, 255])

    # Red colour detection mask
    mask1 = cv2.inRange(hsv_cropped, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_cropped, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Find red boundaries
    red_contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    return frame, red_mask, red_contours


def draw_walls(frame):
    frame, red_mask, red_contours = detect_walls(frame)
    for cnt in red_contours:
        area = cv2.contourArea(cnt)
        if area > 500 or area < 20000:
            cnt += np.array([[x, y]])  # Offset to frame coordinates
            cv2.drawContours(frame, [cnt], -1, (0, 0, 255), 2)
        
    return frame, red_contours
    

def show_nav_workspace(frame, red_contours, module_boxes, idx1=5, idx2=6):
    # Sort red contours by area (largest to smallest)
    sorted_contours = sorted(red_contours, key=cv2.contourArea, reverse=True)
    
    if len(sorted_contours) < 3:
        return np.zeros(frame.shape[:2], dtype=np.uint8)

    outer_contour = sorted_contours[0]  # Outer walls
    inner_contour = sorted_contours[1]  # Workspace
    rhombus_contour = sorted_contours[2]  # Rhombus

    # === 1. Create binary mask (for A* etc.) ===
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [outer_contour], -1, 255, thickness=cv2.FILLED)
    cv2.drawContours(mask, [inner_contour], -1, 0, thickness=cv2.FILLED)
    cv2.drawContours(mask, [rhombus_contour], -1, 255, thickness=cv2.FILLED)

    # === 2. Create visualization image ===
    vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # === 3. Draw module boxes in color ===
    for box in module_boxes:
        cv2.drawContours(vis, [box], -1, (0, 255, 255), 2)  # Yellow outline
        cv2.putText(vis, "Module", tuple(box[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # cv2.imshow("Live Workspace Mask", vis)

    return mask



def process_frame(frame):
    # Define workspace
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Detect module(s) and their distance
    centroids, module_boxes = detect_modules(frame)
    
    # Draw walls
    frame, red_contours = draw_walls(frame)

    # Show navigable workspace and module(s)
    show_nav_workspace(frame, red_contours, module_boxes)

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

        if cv2.waitKey(30) & 0xFF == ord('q'):
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