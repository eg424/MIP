# Measures distance travelled by module from images (length of tracked trajectory)

import cv2
import numpy as np
import os

folder_path = r'C:\Users\erikg\MIP\Python\Tracking\Fixed\M1'

pixels_per_mm = 271 / 32

images_info = [
    ("[0,0,0,-1.5]_20250806_144536_trajectory.png", "Up rolling motion"),
    ("[0,0,0,1.5]_20250806_144453_trajectory.png", "Down rolling motion"),
    ("[0,0.5,0,0]_20250806_144226_trajectory.png", "Left rolling motion"),
    ("[0,-0.5,0,0]_20250806_144258_trajectory.png", "Right rolling motion"),
    ("[0,-0.5,0,-1.5]_20250806_145143_trajectory.png", "Up + Right rolling motion"),
    ("[0,-0.5,0,1.5]_20250806_145352_trajectory.png", "Down + Right rolling motion"),
    ("[0,0.5,0,-1.5]_20250806_144949_trajectory.png", "Up + Left rolling motion"),
    ("[0,0.5,0,1.5]_20250806_145252_trajectory.png", "Down + Left rolling motion"),
]

def measure_trajectory(img):
    y, x = 20, 190
    h, w = 325, 325
    cropped = img[y:y+h, x:x+w]

    # Simple BGR threshold for red pixels
    lower_red = np.array([0, 0, 150])
    upper_red = np.array([100, 100, 255])

    mask = cv2.inRange(cropped, lower_red, upper_red)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return 0, None

    longest_contour = max(contours, key=lambda c: cv2.arcLength(c, False))

    # Shift contour back to original image coordinates
    longest_contour += np.array([x, y])
    points = longest_contour[:, 0, :]
    length = 0.0
    
    for i in range(1, len(points)):
        length += np.linalg.norm(points[i] - points[i - 1])

    return length, longest_contour


def overlay_red(img, contour):
    overlay_img = img.copy()
    if contour is not None:
        cv2.drawContours(overlay_img, [contour], -1, (0, 255, 0), 3)
    return overlay_img


def show_images():
    for filename, label in images_info:
        path = os.path.join(folder_path, filename)
        img = cv2.imread(path)
        if img is None:
            print(f"Failed to load {filename}")
            continue

        length_px, contour = measure_trajectory(img)
        length_mm = length_px / pixels_per_mm

        overlay_img = overlay_red(img, contour)

        title = f"{filename}"
        if label:
            title += f" - {label}"
        title += f"\nLength: {length_mm:.2f} mm"
        print(title)

        cv2.imshow(title, overlay_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    show_images()
