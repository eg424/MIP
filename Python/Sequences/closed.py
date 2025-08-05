import time
import numpy as np
import cv2
from moduleDetection import detect_modules
from main import cap, ser

# === CONFIGURABLE PARAMETERS === #
GOAL_POINT = (330, 280)     # Goal location (x, y) in image space
K_ATTRACT = 1.0             # Attractive gain
K_REPEL = 80000             # Repulsive gain (higher = stronger avoidance)
OBSTACLE_RADIUS = 60        # Influence radius of obstacles (pixels)
MAX_FORCE = 1.5             # Max magnitude for magnetic field components
DURATION = 20               # Max duration of navigation (seconds)
FPS = 10                    # Control frequency
# ============================== #

def compute_force(centroid, obstacles, goal):
    """
    Compute total force vector: F = F_attr + sum(F_rep_i)
    """
    cX, cY = centroid
    gx, gy = goal

    # Attractive force
    dx = gx - cX
    dy = gy - cY
    dist = np.hypot(dx, dy)
    fx_attr = K_ATTRACT * dx
    fy_attr = K_ATTRACT * dy

    # Repulsive force
    fx_rep, fy_rep = 0.0, 0.0
    for ox, oy in obstacles:
        ox_dist = cX - ox
        oy_dist = cY - oy
        d = np.hypot(ox_dist, oy_dist)
        if d < 1e-2 or d > OBSTACLE_RADIUS:
            continue
        rep_scale = K_REPEL * (1.0 / d - 1.0 / OBSTACLE_RADIUS) / (d**3)
        fx_rep += rep_scale * ox_dist
        fy_rep += rep_scale * oy_dist

    fx = fx_attr + fx_rep
    fy = fy_attr + fy_rep

    return fx, fy

def normalize_force_to_currents(fx, fy, max_current=2.0):
    # Normalize force vector
    norm = np.hypot(fx, fy)
    if norm == 0:
        return 0, 0, 0, 0
    fx_norm = fx / norm
    fy_norm = fy / norm

    # Empirical gain factors from calibration
    # Assume Hx saturates around 8 A → 24 mT (3 mT/A)
    # Hy more linear → 11 mT at 10 A (1.1 mT/A)
    GAIN_X = 3.0  # mT/A
    GAIN_Y = 1.1  # mT/A

    # Apply inverse of gains to compensate force direction
    fx_scaled = fx_norm / GAIN_X
    fy_scaled = fy_norm / GAIN_Y

    # Rescale to match max_current
    force_scaled = np.array([fx_scaled, fy_scaled])
    scale = np.linalg.norm(force_scaled)
    if scale > 0:
        force_scaled = (force_scaled / scale) * max_current

    fx_cmd, fy_cmd = force_scaled
    return fx_cmd, fy_cmd, 0, 0  # Only using 2 axes


def main(stop_event=None):
    print("Starting reactive navigation...")
    start_time = time.time()
    
    while time.time() - start_time < DURATION:
        if stop_event and stop_event.is_set():
            print("Sequence interrupted.")
            break

        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        centroids, boxes = detect_modules(frame)
        if len(centroids) == 0:
            print("No module detected.")
            time.sleep(1.0 / FPS)
            continue

        robot_pos = centroids[0]
        obstacles = centroids[1:]  # All others are obstacles

        fx, fy = compute_force(robot_pos, obstacles, GOAL_POINT)
        i1, i2, i3, i4 = normalize_force_to_currents(fx, fy)

        current_cmd = f"{i1:.2f},{i2:.2f},{i3:.2f},{i4:.2f}"
        print(f"Sending: {current_cmd} | Pos: {robot_pos} → {GOAL_POINT}")
        if ser and ser.is_open:
            ser.write((current_cmd + '\n').encode())

        # Visual debug (optional)
        cv2.circle(frame, GOAL_POINT, 5, (0, 255, 0), -1)
        cv2.arrowedLine(frame, robot_pos, (int(robot_pos[0] + fx), int(robot_pos[1] + fy)), (0, 0, 255), 2)
        cv2.imshow("Reactive Navigation", frame)
        cv2.waitKey(1)

        time.sleep(1.0 / FPS)

    print("Reactive navigation ended.")
    # Send zero current to stop
    if ser and ser.is_open:
        ser.write("0,0,0,0\n".encode())