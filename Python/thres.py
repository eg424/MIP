import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load image
img = cv2.imread(r'C:\Users\erikg\Pictures\Screenshots\Screenshot 2025-07-04 142631.png')

# Convert to greyscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Crop
# h, w = gray.shape
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
    if 0.85 <= aspect_ratio <= 1.15:  # Square-ish
        return True
    return False


# Find square centroids
centroids = []
for cnt in contours:
    if is_square(cnt):
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centroids.append((cX, cY))


# Plot
fig, axes = plt.subplots(1, 3, figsize=(12, 5))

axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
axes[0].set_title('Original Image')
axes[0].axis('off')

axes[1].imshow(cropped, cmap='gray')
axes[1].set_title('Original Cropped Greyscale')
axes[1].axis('off')

axes[2].imshow(th, cmap='gray', origin='upper')
for (cx, cy) in centroids:
    axes[2].scatter(cx, cy, color='red', s=40)
axes[2].set_title('Thresholded Image (Squares Only)')
axes[2].axis('off')

plt.tight_layout()
plt.show()