# Testing version for "tracking.py"
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load image
img = cv2.imread(r'C:\Users\erikg\Pictures\Screenshots\Modules\6modsq.png')

# Convert to greyscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Crop
cropped = gray[0:490, 270:810]

# Median Blur
blurred = cv2.medianBlur(cropped, 5)

# Threshold
_, th = cv2.threshold(blurred, 90, 255, cv2.THRESH_BINARY)

# Find contours of all connected components
contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Compute centroids
centroids = []
areas = []

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 1000:  # Filter small noise
        continue
    M = cv2.moments(cnt)
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        centroids.append((cX, cY))
        areas.append(area)

# Plot
fig, axes = plt.subplots(1, 3, figsize=(12, 5))

axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
axes[0].set_title('Original Image')
axes[0].axis('off')

axes[1].imshow(cropped, cmap='gray')
axes[1].set_title('Cropped Greyscale')
axes[1].axis('off')

axes[2].imshow(th, cmap='gray', origin='upper')
for (cx, cy), area in zip(centroids, areas):
    axes[2].scatter(cx, cy, color='red', s=50)
    axes[2].text(cx + 5, cy, f"{int(area)}", color='green')
axes[2].set_title('Groups and Centroid(s)')
axes[2].axis('off')

plt.tight_layout()
plt.show()