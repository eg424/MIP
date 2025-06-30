import cv2
import signal
import sys
import os
import datetime

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
recording = False
out = None
temp_filename = "temp_recording.avi"
final_filename = None

def cleanup_and_exit(signum=None, frame=None):
    print("\nExiting and releasing resources...")
    if cap.isOpened():
        cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()
    if final_filename:
        play_recording(final_filename)
    sys.exit(0)

def play_recording(filename):
    print(f"\nPlaying back: {filename}")
    cap = cv2.VideoCapture(filename)

    if not cap.isOpened():
        print("Error: Cannot open the recorded video.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30 # Verify why retrieved FPS = 0
    total_time = total_frames / fps
    delay = 1

    playing = True
    current_frame = 0

    def on_trackbar(val):
        nonlocal current_frame
        current_frame = val
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cv2.namedWindow('Playback')
    cv2.createTrackbar('Position', 'Playback', 0, total_frames - 1, on_trackbar)

    while True:
        if playing:
            ret, frame = cap.read()
            if not ret:
                print("Reached end of video.")
                playing = False
                current_frame = total_frames - 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                continue
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            cv2.setTrackbarPos('Position', 'Playback', current_frame)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break

        if frame is None or frame.size == 0:
            print("Invalid frame.")
            break

        overlay_text = "PAUSE" if not playing else "PLAY"
        cv2.putText(frame, f"[{overlay_text}] Space to toggle | Q/ESC to exit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        current_time = str(datetime.timedelta(seconds=current_frame / fps)) # Print current time to .2f
        cv2.putText(frame, f"Duration: {current_time}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        
        if current_frame == total_frames - 1 and not playing:
            cv2.putText(frame, "End of video. Press Space to restart or Q to exit.", (10, frame_height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow('Playback', frame)

        key = cv2.waitKey(delay if playing else 50) & 0xFF

        if key in [ord(' '), ord('p')]:
            if not playing and current_frame == total_frames - 1:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                current_frame = 0
            playing = not playing
        elif key in [ord('q'), 27]:
            break

    cap.release()
    cv2.destroyAllWindows()

    while True:
        choice = input("Save this recording? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S') # Change to control sequence written in serial
            new_filename = f"recording_{timestamp}.avi"
            os.rename(filename, new_filename)
            print(f"Saved as {new_filename}")
            break
        elif choice == 'n':
            os.remove(filename)
            print("Recording discarded.")
            break
        else:
            print("Please enter 'y' or 'n'.")

signal.signal(signal.SIGINT, cleanup_and_exit)

if not cap.isOpened():
    print("Cannot open camera")
    sys.exit()

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = 30 # cap.get(cv2.CAP_PROP_FPS) or 30 # Verify why retrieved FPS = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame")
        break

    if recording:
        out.write(frame)
        cv2.putText(frame, "REC", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow('USB Camera Feed', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q') or key == 27:
        break
    elif key == ord('r'):
        if not recording:
            print("Recording started.")
            out = cv2.VideoWriter(temp_filename, cv2.VideoWriter_fourcc(*'XVID'), fps, (frame_width, frame_height))
            recording = True
        else:
            print("Recording stopped.")
            recording = False
            out.release()
            out = None
            final_filename = temp_filename

cleanup_and_exit()