"""
Sequential cycle testing and centroid tracking for modular robots.

This script performs repeated actuation cycles via serial commands to a robot, 
detects the position of the robot module(s) using a camera, and logs positional 
data to a CSV file.

Features:
- Sends predefined coil current sequences (UP, DOWN, LEFT, RIGHT) over serial.
- Captures multiple frames per cycle to determine the centroid of the robot module(s).
- Computes Euclidean and Manhattan displacement from the initial detected centroid.
- Optionally previews camera feed during cycle execution.
- Saves timestamped cycle data, centroid coordinates, and displacements to CSV.
- Configurable via command-line arguments for serial port, baud rate, number of cycles, 
  number of frames per sample, cycle pause, and command pause.
"""

import argparse
import csv
import math
import time
from datetime import datetime
import os
import cv2
import serial

from moduleDetection import detect_modules

def euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_centroid_from_frame(cap, n_frames=3):
    centroids = []
    for _ in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        cs, _ = detect_modules(frame)
        if cs and len(cs) >= 1:
            # Pick first centroid if multiple present
            centroids.append(tuple(cs[0]))
        else:
            centroids.append(None)
        time.sleep(0.05)

    # Choose the most common non-None centroid (simple majority heuristic)
    filtered = [c for c in centroids if c is not None]
    if not filtered:
        return None
    # Average coordinates
    xs = [c[0] for c in filtered]
    ys = [c[1] for c in filtered]
    return (sum(xs)/len(xs), sum(ys)/len(ys))


def run_cycles(port='COM3', baud=9600, cycles=10, out_csv='trial.csv',
               sample_frames=3, preview=False,
               cycle_pause=0.3, cmd_pause=0.2):

    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    
    # Prepare output file
    header = ['timestamp', 'cycle', 'single_module_detected', 'centroid_x', 'centroid_y',
              'euclidean_from_start', 'manhattan_from_start', 'x_disp_from_start', 'y_disp_from_start']
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)

    with serial.Serial(port, baud, timeout=2) as ser, open(out_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

        # Small delay to let Arduino reset and clear input buffer
        time.sleep(1.0)
        ser.reset_input_buffer()

        # Clear any initial serial junk
        while ser.in_waiting:
            try:
                _ = ser.readline().decode().strip()
            except Exception:
                break

        initial_centroid = None
        print(f"[seq_cycles] Starting {cycles} cycles. Output -> {out_csv}")

        for c in range(1, cycles + 1):
            if not ser.is_open:
                raise RuntimeError("Serial port closed unexpectedly.")

            # Send sequence 
            # UP
            # ser.write(b'0,0,0,-1.5\n') # (b'0,0,-2,-1.5'\n)
            # print(f"[cycle {c}] Sent: 0,0,0,-1.5")
            # time.sleep(cycle_pause)

            # ser.write(b'0,0.5,0,0\n')
            # print(f"[cycle {c}] Sent: 0,0.5,0,0")
            # time.sleep(cmd_pause)

            # ser.write(b'0,0,0,0\n')
            # print(f"[cycle {c}] Sent: 0,0,0,0")
            # time.sleep(0.2)
            
            # DOWN
            # ser.write(b'0,0,0,1.5\n') # (b'0,0,2,1.5'\n)
            # print(f"[cycle {c}] Sent: 0,0,0,1.5")
            # time.sleep(cycle_pause)

            # ser.write(b'0,1,0,0\n')
            # print(f"[cycle {c}] Sent: 0,0.5,0,0")
            # time.sleep(cmd_pause)

            # ser.write(b'0,0,0,0\n')
            # print(f"[cycle {c}] Sent: 0,0,0,0")
            # time.sleep(0.2)
            
            # LEFT
            ser.write(b'-4,-1,0,0\n') # ,0.5,0,0
            print(f"[cycle {c}] Sent: 0,0.5,0,0")
            time.sleep(cycle_pause)

            ser.write(b'0,0,0,2.5\n')
            print(f"[cycle {c}] Sent: 0,0,0,1.5")
            time.sleep(cmd_pause)

            ser.write(b'0,0,0,0\n')
            print(f"[cycle {c}] Sent: 0,0,0,0")
            time.sleep(0.2)
            
            # RIGHT 0,-0.5,0,0 # 9,0.5,0,0
            # ser.write(b'0,-0.5,0,0\n') # -4.5,-0.5,0,0
            # print(f"[cycle {c}] Sent: 0,-0.5,0,0")
            # time.sleep(cycle_pause)

            # ser.write(b'0,0,0,1.5\n')
            # print(f"[cycle {c}] Sent: 0,0,0,1.5")
            # time.sleep(cmd_pause)

            # ser.write(b'0,0,0,0\n')
            # print(f"[cycle {c}] Sent: 0,0,0,0")
            # time.sleep(0.2)

            centroid = get_centroid_from_frame(cap, n_frames=sample_frames)

            single_detected = 0
            euclid = ''
            manh = ''
            xdisp = ''
            ydisp = ''

            if centroid is not None:
                if initial_centroid is None:
                    initial_centroid = centroid
                    print(f"[seq_cycles] Initial centroid set to {initial_centroid}")

                # Compute displacement for the first centroid observed
                single_detected = 1
                euclid = euclidean(centroid, initial_centroid)
                manh = manhattan(centroid, initial_centroid)
                xdisp = centroid[0] - initial_centroid[0]
                ydisp = centroid[1] - initial_centroid[1]

                print(f"[cycle {c}] Single module detected. centroid={centroid}. "
                      f"Euclid={euclid:.2f}, Manhattan={manh:.2f}, x={xdisp:.2f}, y={ydisp:.2f}")
            else:
                print(f"[cycle {c}] No reliable centroid detected (centroid=None).")

            writer.writerow([datetime.now().isoformat(), c, single_detected,
                             centroid[0] if centroid else '', centroid[1] if centroid else '',
                             f"{euclid:.6f}" if euclid != '' else '', f"{manh:.6f}" if manh != '' else '',
                             f"{xdisp:.6f}" if xdisp != '' else '', f"{ydisp:.6f}" if ydisp != '' else ''])
            csvfile.flush()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run cycles and record displacements.")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--out", default="trial.csv")
    parser.add_argument("--sample_frames", type=int, default=3, help="Number of frames to average per cycle sampling.")
    parser.add_argument("--preview", action="store_true", help="Show camera preview during run.")
    parser.add_argument("--cycle_pause", type=float, default=0.2, help="Pause after pivot command (s).")
    parser.add_argument("--cmd_pause", type=float, default=0.2, help="Pause after move command (s).")
    args = parser.parse_args()

    run_cycles(port=args.port, baud=args.baud, cycles=args.cycles, out_csv=args.out,
               sample_frames=args.sample_frames, preview=args.preview,
               cycle_pause=args.cycle_pause, cmd_pause=args.cmd_pause)