import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

loop = True  # Set to True to loop through all images
single = r'C:\Users\erikg\Pictures\Screenshots\Modules\4mod2ch2liq.png'  # Failed: 4mod2ch2liq, 6mod2ch, 6mod3ch, 6mod4sq2ch

def process_image(img, filename=""):
    
    print(f"File name: {filename}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold to detect workspace
    _, th = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Largest contour as workspace
    workspace_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(workspace_contour)
    print(f"Workspace bounding box: x={x}, y={y}, w={w}, h={h}")

    # Crop to workspace
    cropped = gray[y:y + h, x:x + w]

    # Further preprocessing
    blurred_cropped = cv2.medianBlur(cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 85, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} contours in cropped image.")
    
    centroids = []
    areas = []

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 1500 or area > 20000:
            print(f"Rejected contour {i} due to area: {area}")
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        aspect_ratio = w_cnt / h_cnt
        print(f"Contour {i} aspect ratio: {aspect_ratio:.2f}")

        if aspect_ratio < 0.4 or aspect_ratio > 1.4:
            print(f"Rejected contour {i} due to aspect ratio: {aspect_ratio:.2f}")
            continue
        if x_cnt < 5 or y_cnt < 5 or x_cnt + w_cnt > cropped.shape[1] - 5 or y_cnt + h_cnt > cropped.shape[0] - 5:
            print(f"Rejected contour {i} near border.")
            continue

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centroids.append((cX, cY))
            areas.append(area)
            print(f"Contour {i} accepted. Centroid: ({cX}, {cY}), Area: {int(area)}")

    # Plotting
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

# Single image/Loop through all
if loop:
    folder_path = r'C:\Users\erikg\Pictures\Screenshots\Modules'
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]

    for filename in image_files:
        full_path = os.path.join(folder_path, filename)
        img = cv2.imread(full_path)
        process_image(img, filename)
else:
    img = cv2.imread(single)
    filename = os.path.basename(single)
    process_image(img, filename)