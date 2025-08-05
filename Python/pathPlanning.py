import cv2
import numpy as np
import itertools
from moduleDetection import detect_modules, draw_walls, show_nav_workspace
import heapq

# Constants
y, x = 20, 180
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


def heuristic(a, b):
    # Euclidean distance as heuristic function for A*
    return np.linalg.norm(np.array(a) - np.array(b))


def astar(grid, start, goal):
    h, w = grid.shape

    # Open set implemented as a priority queue (heapq)
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, [start]))

    visited = set()  # Set to keep track of visited nodes to prevent revisiting

    while open_set:
        # Pop node with lowest f_score = g_score + heuristic
        _, cost, current, path = heapq.heappop(open_set)

        # If goal is reached, return the path
        if current == goal:
            return path

        if current in visited:
            continue  # Skip if already processed
        visited.add(current)

        # Explore neighbors (8-connectivity)
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nx, ny = current[0] + dx, current[1] + dy

            # Check if neighbor is inside grid bounds and free (not an obstacle)
            if 0 <= nx < h and 0 <= ny < w and grid[nx, ny] == 0:
                # Diagonal moves cost more (√2), straight moves cost 1
                step_cost = np.sqrt(2) if dx != 0 and dy != 0 else 1
                new_cost = cost + step_cost
                # Calculate priority: new cost + heuristic estimate to goal
                priority = new_cost + heuristic((nx, ny), goal)
                # Add neighbor to open set with updated path
                heapq.heappush(open_set, (priority, new_cost, (nx, ny), path + [(nx, ny)]))

    return None  # Return None if no path is found


def process_frame(frame):
    _, module_boxes = detect_modules(frame)
    _, red_contours = draw_walls(frame)
    mask = show_nav_workspace(frame, red_contours, module_boxes)

    # Convert mask to occupancy grid and display it
    occupancy_grid = mask_to_grid(mask)
    display_grid(occupancy_grid)
    
    return frame


def inflate_obstacles(occupancy_grid):
    inflation_cells = int(np.ceil(1.5)) # Module radius
    # Create a circular kernel for dilation
    kernel_size = inflation_cells * 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    inflated_grid = cv2.dilate(occupancy_grid, kernel, iterations=1)
    return inflated_grid


def live_mode():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    print("Click once on the occupancy grid window to set the goal point.")
    print("The start point is automatically set to the first detected module centroid.")

    start, goal = None, None
    clicked_points = []
    occupancy_grid = None  # <- define here so it’s accessible in mouse_callback

    def mouse_callback(event, x, y, flags, param):
        nonlocal goal, clicked_points, occupancy_grid
        if event == cv2.EVENT_LBUTTONDOWN and occupancy_grid is not None:
            # Scale click to grid coordinates
            grid_h, grid_w = occupancy_grid.shape
            clicked_col = int(x * grid_w / 640)
            clicked_row = int(y * grid_h / 360)
            goal = (clicked_row, clicked_col)
            print(f"Goal set to: {goal}")

    cv2.namedWindow("Occupancy Grid")
    cv2.setMouseCallback("Occupancy Grid", mouse_callback)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        centroids, module_boxes = detect_modules(frame)
        frame, red_contours = draw_walls(frame)
        mask = show_nav_workspace(frame, red_contours, module_boxes)
        occupancy_grid = mask_to_grid(mask)

        if centroids:
            cell_size_pixels = int(1 * pixels_per_mm)
            start_pixel = centroids[0]
            start = (start_pixel[1] // cell_size_pixels, start_pixel[0] // cell_size_pixels)
        else:
            start = None

        # Inflate obstacles by 1.5 mm
        inflated_grid = inflate_obstacles(occupancy_grid)

        # Visualize:
        # 255 = free space
        # 0 = original obstacle
        # 127 = inflated area excluding original obstacles (gray)
        grid_vis = np.ones_like(occupancy_grid, dtype=np.uint8) * 255  # start with free space white
        grid_vis[occupancy_grid == 1] = 0
        inflated_only = (inflated_grid == 1) & (occupancy_grid == 0)
        grid_vis[inflated_only] = 127

        # Convert to BGR color image for coloring path
        grid_color = cv2.cvtColor(grid_vis, cv2.COLOR_GRAY2BGR)

        if start and goal:
            path = astar(inflated_grid, start, goal)
            if path:
                for p in path:
                    grid_color[p[0], p[1]] = (255, 0, 0)  # Blue path

        resized_vis = cv2.resize(grid_color, (640, 360), interpolation=cv2.INTER_NEAREST)
        cv2.imshow("Occupancy Grid", resized_vis)

            

        key = cv2.waitKey(30) & 0xFF
        if key == ord('r'):
            goal = None
            print("Goal reset. Click to set a new goal.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

live_mode()