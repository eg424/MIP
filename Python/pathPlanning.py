import cv2
import numpy as np
import itertools
from moduleDetection import detect_modules, draw_walls, show_nav_workspace

# Constants
y, x = 20, 190
h, w = 325, 325
pixels_per_mm = 271 / 32


def mask_to_grid(mask, grid_size_mm=1):
    cell_size_pixels = int(grid_size_mm * pixels_per_mm)

    grid_h = mask.shape[0] // cell_size_pixels
    grid_w = mask.shape[1] // cell_size_pixels

    resized_mask = cv2.resize(mask, (grid_w, grid_h), interpolation=cv2.INTER_NEAREST)
    occupancy_grid = (resized_mask > 0).astype(np.uint8)

    return occupancy_grid


def display_grid(occupancy_grid):
    grid_vis = (1 - occupancy_grid) * 255  # Flip: free=255, obstacle=0
    grid_vis = cv2.resize(grid_vis.astype(np.uint8), (640, 360), interpolation=cv2.INTER_NEAREST)
    cv2.imshow("Occupancy Grid", grid_vis)


def process_frame(frame):
    _, module_boxes = detect_modules(frame)
    _, red_contours = draw_walls(frame)
    mask = show_nav_workspace(frame, red_contours, module_boxes)

    # Convert mask to occupancy grid and display it
    occupancy_grid = mask_to_grid(mask)
    display_grid(occupancy_grid)
    
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

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


live_mode()