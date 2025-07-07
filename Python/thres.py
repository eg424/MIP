import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load image
img = cv2.imread(r'C:\Users\erikg\Pictures\Screenshots\Modules\6modsq.png') # 6modsq also bright

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Blur to reduce noise
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Threshold to detect workspace (inverse to get dark areas)
_, th = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY_INV)

# Find contours
contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Find the largest rectangular contour (assumed to be workspace)
workspace_contour = max(contours, key=cv2.contourArea)
x, y, w, h = cv2.boundingRect(workspace_contour)

# Crop to workspace
cropped = gray[y:y+h, x:x+w]

# Median blur to reduce speckles
blurred_cropped = cv2.medianBlur(cropped, 5)

# Threshold to isolate brighter cubes
_, th_cropped = cv2.threshold(blurred_cropped, 85, 255, cv2.THRESH_BINARY)

# Morphological closing
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)

# Find contours in closed binary image
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Compute centroids and areas
centroids = []
areas = []

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 1500:  # Filter small noise
        continue
    
    x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
    aspect_ratio = w_cnt / h_cnt
    print(aspect_ratio)

    # Filter by shape and proximity to image edge
    if aspect_ratio < 0.4 or aspect_ratio > 1.4:
        continue
    if x_cnt < 5 or y_cnt < 5 or x_cnt + w_cnt > cropped.shape[1] - 5 or y_cnt + h_cnt > cropped.shape[0] - 5:
        continue
    
    M = cv2.moments(cnt)
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        centroids.append((cX, cY))
        areas.append(area)

# Plot results
fig, axes = plt.subplots(1, 3, figsize=(12, 5))

axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
axes[0].set_title('Original Image')
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