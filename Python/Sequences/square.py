# Sequences/seq_square.py
import time
import serial
import numpy as np
import cv2
from moduleDetection import detect_modules

PORT = 'COM3'
BAUDRATE = 9600
FRAME_INTERVAL = 0.1  # ~10 Hz
TOLERANCE_MM = 1.5  # Stop when all modules are within this
MAX_CURRENT = 1.5  # Limit max current per axis
Kp = 0.08
Kd = 0.02

# Approx. calibration (adjust as needed)
PIXELS_PER_MM = 10  # rough initial guess, can be refined

# Define square corners (goal positions in pixels)
def generate_square_goals(center=(350, 300), side_mm=10):
    offset = int(side_mm * PIXELS_PER_MM / 2)
    cx, cy = center
    return [
        (cx - offset, cy - offset),  # top-left
        (cx + offset, cy - offset),  # top-right
        (cx + offset, cy + offset),  # bottom-right
        (cx - offset, cy + offset),  # bottom-left
    ]

def assign_nearest(centroids, goals):
    assigned = [-1]*len(centroids)
    used = set()
    for i, c in enumerate(centroids):
        dists = [np.linalg.norm(np.array(c) - np.array(g)) if j not in used else np.inf for j, g in enumerate(goals)]
        j = int(np.argmin(dists))
        assigned[i] = j
        used.add(j)
    return assigned

def main():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(1)

    prev_errors = [np.array([0, 0])] * 4
    square_goals = generate_square_goals()

    print("🧲 Starting closed-loop square control...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera error.")
            break

        centroids, _, _ = detect_modules(frame)
        if len(centroids) != 4:
            print(f"⏳ Waiting for 4 modules (currently {len(centroids)})...")
            send_zero(ser)
            time.sleep(0.5)
            continue

        assignments = assign_nearest(centroids, square_goals)
        total_error = 0
        control_vecs = []

        for i, c in enumerate(centroids):
            goal = square_goals[assignments[i]]
            err_vec = np.array(goal) - np.array(c)
            derr = err_vec - prev_errors[i]
            prev_errors[i] = err_vec

            ctrl = Kp * err_vec + Kd * derr
            control_vecs.append(ctrl)
            total_error += np.linalg.norm(err_vec) / PIXELS_PER_MM  # in mm

        # Average control field across all modules
        net_control = np.mean(control_vecs, axis=0)
        hx = np.clip(net_control[0] / PIXELS_PER_MM, -MAX_CURRENT, MAX_CURRENT)
        hy = np.clip(net_control[1] / PIXELS_PER_MM, -MAX_CURRENT, MAX_CURRENT)

        # Send to Arduino
        ser.write(f"0,{hx:.2f},0,{hy:.2f}\n".encode())
        print(f"→ Sent: Hx={hx:.2f}, Hy={hy:.2f}, total error: {total_error:.2f} mm")

        # Stop if all errors are small
        if total_error / 4 < TOLERANCE_MM:
            print("✅ Square formed! Holding position...")
            send_zero(ser)
            break

        time.sleep(FRAME_INTERVAL)

    cap.release()
    send_zero(ser)
    ser.close()

def send_zero(ser):
    ser.write(b"0,0,0,0\n")