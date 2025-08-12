import cv2
import numpy as np
import serial
import time
import heapq
import os
import threading
import datetime
from moduleDetection import detect_modules, draw_walls, show_nav_workspace
from main import send_zero_pwm, start_recording, stop_recording, input_queue
from fsm import FiniteStateMachine

# Constants
y, x = 20, 190
h, w = 325, 325
pixels_per_mm = 271 / 32
theta = 0
alpha = 0
beta = 0

direction_to_serial = {
    "UP": "0,0,0,-1.5\n",
    "DOWN": "0,0,0,1.5\n",
    "LEFT": "0,0.5,0,0\n",
    "RIGHT": "0,-0.5,0,0\n",
    "UP_LEFT": "0,0.5,0,-1.5\n",
    "UP_RIGHT": "0,-0.5,0,-1.5\n",
    "DOWN_LEFT": "0,0.5,0,1.5\n",
    "DOWN_RIGHT": "0,-0.5,0,1.5\n"
}

secondary_sequences = {
    "DOWN": [
        ("0,0,2,1.5\n", 0.2),
        ("0,0.5,0,0\n", 0.2),
        ("0,0,0,0\n", 0.1)
    ],
    "UP": [
        ("0,0,-2,-1.5\n", 0.2),
        ("0,0.5,0,0\n", 0.2),
        ("0,0,0,0\n", 0.1)
    ],
    "RIGHT": [
        ("4.5,0.5,0,0\n", 0.2),
        ("0,0,0,-1.5\n", 0.2),
        ("0,0,0,0\n", 0.1)
    ],
    "LEFT": [
        ("-4.5,-0.5,0,0\n", 0.2),
        ("0,0,0,1.5\n", 0.2),
        ("0,0,0,0\n", 0.1)
    ]
}

def norm_angle(x):
    return ((round(x / 90) * 90 + 180) % 360) - 180


def get_field_command(move, theta, alpha, beta):
    theta = norm_angle(theta)
    alpha = norm_angle(alpha)
    beta = norm_angle(beta)

    # Default case
    if theta == 0 and beta == 0:
        return direction_to_serial[move]

    # Handle face-forward or backward
    if theta == 90:
        if move == "LEFT":
            return direction_to_serial["RIGHT"]
        elif move == "RIGHT":
            return direction_to_serial["LEFT"]
    elif theta == -90:
        if move == "LEFT":
            return direction_to_serial["LEFT"]
        elif move == "RIGHT":
            return direction_to_serial["RIGHT"]

    # Handle face-left or right
    if beta == 90:
        if move == "UP":
            return direction_to_serial["RIGHT"]
        elif move == "DOWN":
            return direction_to_serial["LEFT"]
    elif beta == -90:
        if move == "UP":
            return direction_to_serial["LEFT"]
        elif move == "DOWN":
            return direction_to_serial["RIGHT"]

    # Fallback
    print(f"[WARN] Unhandled orientation θ={theta}, α={alpha}, β={beta}. Using original.")
    return direction_to_serial[move]


def heuristic(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def astar(grid, start, goal):
    h, w = grid.shape
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start]))
    visited = set()

    while open_set:
        _, cost, current, path = heapq.heappop(open_set)
        if current == goal:
            return path
        if current in visited:
            continue
        visited.add(current)

        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < h and 0 <= ny < w and grid[nx, ny] == 0:
                # Check if diagonal
                if abs(dx) == 1 and abs(dy) == 1:
                    # First 5 steps from start = no penalty
                    if len(path) <= 3:
                        step_cost = 1
                    else:
                        step_cost = 1.4  # penalised diagonal
                else:
                    step_cost = 1  # straight move

                new_cost = cost + step_cost
                priority = new_cost + heuristic((nx, ny), goal)
                heapq.heappush(open_set, (priority, new_cost, (nx, ny), path + [(nx, ny)]))
    return None



def inflate_obstacles(occupancy_grid):
    inflation_cells = int(np.ceil(1.5))  # 1.5 mm radius
    kernel_size = inflation_cells * 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.dilate(occupancy_grid, kernel, iterations=1)


def path_to_directions(path):
    directions = []
    for i in range(1, len(path)):
        dx = path[i][0] - path[i-1][0]
        dy = path[i][1] - path[i-1][1]
        if dx == -1 and dy == 0:
            directions.append("UP")
        elif dx == 1 and dy == 0:
            directions.append("DOWN")
        elif dx == 0 and dy == -1:
            directions.append("LEFT")
        elif dx == 0 and dy == 1:
            directions.append("RIGHT")
        elif dx == -1 and dy == -1:
            directions.append("UP_LEFT")
        elif dx == -1 and dy == 1:
            directions.append("UP_RIGHT")
        elif dx == 1 and dy == -1:
            directions.append("DOWN_LEFT")
        elif dx == 1 and dy == 1:
            directions.append("DOWN_RIGHT")
    return directions


def live_mode(ser):
    fsm = FiniteStateMachine()
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    # -------------------
    # Secondary motion sequences
    # -------------------
    secondary_sequences = {
        "DOWN": [
            ("0,0.5,0,0\n", 0.2),
            ("0,0,2,1.5\n", 0.2),
            ("0,0,0,0\n", 0.1)
        ],
        "UP": [
            ("0,0.5,0,0\n", 0.2),
            ("0,0,-2,-1.5\n", 0.2),
            ("0,0,0,0\n", 0.1)
        ],
        "RIGHT": [
            ("4.5,0.5,0,0\n", 0.2),
            ("0,0,0,-1.5\n", 0.2),
            ("0,0,0,0\n", 0.1)
        ],
        "LEFT": [
            ("-4.5,-0.5,0,0\n", 0.2),
            ("0,0,0,1.5\n", 0.2),
            ("0,0,0,0\n", 0.1)
        ]
    }

    print("Click on the occupancy grid window to set the goal point.")
    print("Press 'Enter' to start movement. Press 'r' to reset goal. Press 'q' to quit.")

    goal = None
    goal_reached = False
    movement_enabled = False
    cell_size_pixels = int(1 * pixels_per_mm)
    tolerance_cells = 1

    directions = []
    direction_index = 0

    def mouse_callback(event, x, y, flags, param):
        nonlocal goal, goal_reached, movement_enabled, directions, direction_index
        if event == cv2.EVENT_LBUTTONDOWN:
            goal_reached = False
            movement_enabled = False
            directions = []
            direction_index = 0
            clicked_col = int(x * occupancy_grid.shape[1] / 640)
            clicked_row = int(y * occupancy_grid.shape[0] / 360)
            goal = (clicked_row, clicked_col)
            print(f"Goal set to: {goal}. Press 'Enter' to begin movement.")

    cv2.namedWindow("Occupancy Grid")
    cv2.setMouseCallback("Occupancy Grid", mouse_callback)

    start = None
    waiting_for_confirmation = False
    last_command_sent = None
    prev_dist_to_goal = None
    time_sent = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        centroids, module_boxes = detect_modules(frame)
        frame, red_contours = draw_walls(frame)
        mask = show_nav_workspace(frame, red_contours, module_boxes)
        cv2.imshow("Live Module Detection", frame)

        occupancy_grid = cv2.resize(mask, (mask.shape[1] // cell_size_pixels, mask.shape[0] // cell_size_pixels),
                                    interpolation=cv2.INTER_NEAREST)
        occupancy_grid = (occupancy_grid > 0).astype(np.uint8)
        inflated_grid = inflate_obstacles(occupancy_grid)

        grid_vis = np.ones_like(occupancy_grid, dtype=np.uint8) * 255
        grid_vis[occupancy_grid == 1] = 0
        inflated_only = (inflated_grid == 1) & (occupancy_grid == 0)
        grid_vis[inflated_only] = 127
        grid_color = cv2.cvtColor(grid_vis, cv2.COLOR_GRAY2BGR)

        if centroids:
            module_pos = centroids[0]
            start = (module_pos[1] // cell_size_pixels, module_pos[0] // cell_size_pixels)

            if goal and not goal_reached:
                dist_to_goal = np.linalg.norm(np.array(start) - np.array(goal))
                if dist_to_goal <= tolerance_cells:
                    print("Goal reached.")
                    goal_reached = True
                    movement_enabled = False
                    directions = []
                    direction_index = 0
                    stop_recording()
                    if ser:
                        try:
                            send_zero_pwm()
                            ser.close()
                        except:
                            pass
                        ser = None

            if movement_enabled and not goal_reached and not directions and goal:
                path = astar(inflated_grid, start, goal)
                if path and len(path) > 1:
                    directions = path_to_directions(path)
                    direction_index = 0

            if movement_enabled and directions and direction_index < len(directions) and ser and not goal_reached:
                if not waiting_for_confirmation:
                    d = directions[direction_index]
                    prev_dist_to_goal = np.linalg.norm(np.array(start) - np.array(goal))

                    # First move → single command
                    if fsm.command_count == 0:
                        cmd = get_field_command(d, fsm.theta_degrees, fsm.alpha_degrees, fsm.beta_degrees)
                        print(f"Sending first move until movement detected: {cmd.strip()}")
                        first_move_start_pos = start

                        # Parse the currents into floats so we can adjust them
                        cmd_parts = cmd.strip().split(",")
                        currents = [float(c) for c in cmd_parts]

                        last_increase_time = time.time()

                        while True:
                            # Send current command
                            ser.write(("{:.3f},{:.3f},{:.3f},{:.3f}\n".format(*currents)).encode())
                            time.sleep(0.3)  # short delay between re-sends

                            # Check movement
                            ret2, frame2 = cap.read()
                            if not ret2:
                                break
                            centroids2, _ = detect_modules(frame2)
                            if centroids2:
                                module_pos2 = centroids2[0]
                                new_start = (module_pos2[1] // cell_size_pixels, module_pos2[0] // cell_size_pixels)
                                distance_travelled_px = np.linalg.norm(np.array(new_start) - np.array(first_move_start_pos))

                                if distance_travelled_px > 0.2:  # movement threshold in pixels
                                    print(f"[First Move] Movement detected: {distance_travelled_px:.2f}px")
                                    break

                            # Increase current magnitude every 2 seconds if no movement
                            if time.time() - last_increase_time >= 2.0:
                                for i in range(len(currents)):
                                    if currents[i] != 0.0:  # Only adjust the non-zero coil
                                        sign = 1 if currents[i] > 0 else -1
                                        currents[i] = round(currents[i] + sign * 0.2, 3)
                                print(f"[First Move] No movement — increasing current to: {currents}")
                                last_increase_time = time.time()

                        # Once movement detected, record command for FSM
                        fsm.process_command(d)
                        direction_index += 1
                        waiting_for_confirmation = False

                    else:
                        # Subsequent moves → sequence
                        if d in secondary_sequences:
                            print(f"Sending secondary sequence for: {d}")
                            for seq_cmd, seq_delay in secondary_sequences[d]:
                                ser.write(seq_cmd.encode())
                                print(f"  Sent: {seq_cmd.strip()}, delay {seq_delay}s")
                                time.sleep(seq_delay)
                        else:
                            cmd = get_field_command(d, fsm.theta_degrees, fsm.alpha_degrees, fsm.beta_degrees)
                            ser.write(cmd.encode())
                            print(f"Sent fallback: {cmd.strip()}")

                        waiting_for_confirmation = True
                        last_command_sent = d
                        time_sent = time.time()

                else:
                    if time.time() - time_sent >= 0.2:
                        ret2, frame2 = cap.read()
                        if ret2:
                            centroids2, _ = detect_modules(frame2)
                            if centroids2:
                                module_pos2 = centroids2[0]
                                new_start = (module_pos2[1] // cell_size_pixels, module_pos2[0] // cell_size_pixels)
                                new_dist_to_goal = np.linalg.norm(np.array(new_start) - np.array(goal))

                                distance_travelled_px = np.linalg.norm(np.array(new_start) - np.array(start))
                                if fsm.apply_move_feedback(distance_travelled_px, new_dist_to_goal):
                                    # Goal reached by FSM’s definition
                                    goal_reached = True
                                    movement_enabled = False
                                    directions = []
                                    direction_index = 0
                                    stop_recording()
                                    if ser:
                                        try:
                                            send_zero_pwm()
                                            ser.close()
                                        except:
                                            pass
                                        ser = None
                                else:
                                    # Movement was good enough to count as a valid step
                                    if new_dist_to_goal < prev_dist_to_goal:
                                        fsm.process_command(last_command_sent)
                                        direction_index += 1
                                        start = new_start
                                        waiting_for_confirmation = False
                                    else:
                                        # Failed move → retry
                                        print("[FSM] Movement ineffective — retrying with sequence.")
                                        if last_command_sent in secondary_sequences:
                                            for seq_cmd, seq_delay in secondary_sequences[last_command_sent]:
                                                ser.write(seq_cmd.encode())
                                                print(f"  Retry Sent: {seq_cmd.strip()}, delay {seq_delay}s")
                                                time.sleep(seq_delay)
                                        else:
                                            cmd = get_field_command(last_command_sent, fsm.theta_degrees, fsm.alpha_degrees, fsm.beta_degrees)
                                            ser.write(cmd.encode())
                                            print(f"Retry fallback: {cmd.strip()}")
                                        time_sent = time.time()


        if goal and start:
            path = astar(inflated_grid, start, goal)
            if path:
                for p in path:
                    grid_color[p[0], p[1]] = (255, 0, 0)

        resized_vis = cv2.resize(grid_color, (640, 360), interpolation=cv2.INTER_NEAREST)
        cv2.imshow("Occupancy Grid", resized_vis)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            goal = None
            goal_reached = False
            movement_enabled = False
            directions = []
            direction_index = 0
            fsm.reset()
            stop_recording()
            send_zero_pwm()
            if ser:
                try:
                    ser.close()
                except:
                    pass
                ser = None
            print("Goal reset. Orientation reset.")

        elif key == ord('q'):
            stop_recording()
            if ser:
                try:
                    send_zero_pwm()
                    ser.close()
                except:
                    pass
            break

        elif key == 13:
            if goal and not goal_reached:
                start_recording()
                movement_enabled = True
                directions = []
                direction_index = 0
                input_queue.put("pathplan_goal")
                print("Movement enabled and recording started.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ser = serial.Serial("COM8", 9600, timeout=2)
    live_mode(ser)