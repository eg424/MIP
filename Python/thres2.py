'''
Thres.py but on live input, to test module detection.
Usedbefore establishing detect_modules function in "tracking.py".
'''

import cv2
import numpy as np

def process_frame(frame):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold to detect workspace (binary inverse)
    _, th = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Largest contour as workspace
    workspace_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(workspace_contour)
    
    # Draw bounding box around workspace on the original frame (blue rectangle)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Crop to workspace
    cropped = gray[y:y + h, x:x + w]

    # Further preprocessing
    blurred_cropped = cv2.medianBlur(cropped, 5)
    _, th_cropped = cv2.threshold(blurred_cropped, 82, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(th_cropped, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centroids = []
    areas = []
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 800 or area > 20000:
            continue

        x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
        aspect_ratio = w_cnt / h_cnt

        if aspect_ratio < 0.4 or aspect_ratio > 2.2:
            continue
        if x_cnt < 5 or y_cnt < 5 or x_cnt + w_cnt > cropped.shape[1] - 5 or y_cnt + h_cnt > cropped.shape[0] - 5:
            continue

        # Draw rectangle on original frame (adjust coordinates to original frame)
        top_left = (x + x_cnt, y + y_cnt)
        bottom_right = (x + x_cnt + w_cnt, y + y_cnt + h_cnt)
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0))

        # Draw centroid
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"]) + x
            cY = int(M["m01"] / M["m00"]) + y
            centroids.append((cX, cY))
            cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
            areas.append(area)

    return frame


def main():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
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
    main()