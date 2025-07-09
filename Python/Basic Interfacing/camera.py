"""
USB camera capture and video recording with playback and save/discard options.

- Captures live video from USB camera (device 1) at 30 FPS.
- Allows user to start/stop recording with 'r' key; records to a temporary AVI file.
- Displays live feed with recording indicator when active.
- Press 'q' or ESC to stop live feed.
- After stopping, playback the recorded video with controls:
    * Space or 'p' to toggle play/pause
    * Trackbar to seek frames
    * 's' to save the recording with timestamped filename
    * 'n' to discard the recording
    * 'q' or ESC to exit playback
- Handles cleanup on exit (releasing camera, closing windows).
- Supports Ctrl+C interruption with graceful exit.
"""

import cv2
import signal
import sys
import os
import datetime
import time

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
recording = False
out = None
temp_filename = "temp_recording.avi"
final_filename = None
in_replay = False
desired_fps = 30
last_record_time = time.time()

def cleanup_and_exit(signum=None, frame=None):
    print("\nExiting and releasing resources...")
    if cap.isOpened():
        cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()
    sys.exit(0)

def play_recording(filename):
    global final_filename, in_replay
    print(f"\nPlaying back: {filename}")
    cap_play = cv2.VideoCapture(filename)

    if not cap_play.isOpened():
        print("Error: Cannot open the recorded video.")
        return

    total_frames = int(cap_play.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_play.get(cv2.CAP_PROP_FPS)
    print(f"[DEBUG] Playback FPS reported from file: {fps}")

    if fps <= 0 or fps != fps:
        print("[DEBUG] Invalid FPS in video file. Using fallback: 30")
        fps = 30

    delay = int(1000 / fps)
    print(f"[DEBUG] Playback delay per frame (ms): {delay}")

    playing = True
    current_frame = 0
    already_saved = False

    def on_trackbar(val):
        nonlocal current_frame
        current_frame = val
        cap_play.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    frame_width = int(cap_play.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap_play.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cv2.namedWindow('Playback')
    cv2.createTrackbar('Position', 'Playback', 0, total_frames - 1, on_trackbar)

    in_replay = True
    while True:
        if playing:
            ret, frame = cap_play.read()
            if not ret:
                playing = False
                current_frame = total_frames - 1
                cap_play.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                continue
            current_frame = int(cap_play.get(cv2.CAP_PROP_POS_FRAMES))
            cv2.setTrackbarPos('Position', 'Playback', current_frame)
        else:
            cap_play.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap_play.read()
            if not ret:
                break

        if frame is None or frame.size == 0:
            print("Invalid frame.")
            break

        overlay_text = "PAUSE" if not playing else "PLAY"
        cv2.putText(frame, f"[{overlay_text}] Space: toggle | Q/ESC: exit | S: save | N: discard", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        current_time = str(datetime.timedelta(seconds=current_frame / fps))
        cv2.putText(frame, f"Duration: {current_time}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if current_frame == total_frames - 1 and not playing:
            cv2.putText(frame, "End of video. Press Space to restart or Q to exit.", (10, frame_height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow('Playback', frame)

        key = cv2.waitKey(delay if playing else 50) & 0xFF

        if key in [ord(' '), ord('p')]:
            if not playing and current_frame == total_frames - 1:
                cap_play.set(cv2.CAP_PROP_POS_FRAMES, 0)
                current_frame = 0
            playing = not playing
        elif key == ord('s') and not already_saved:
            cap_play.release()
            cv2.destroyAllWindows()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"recording_{timestamp}.avi"
            os.rename(filename, new_filename)
            print(f"Recording saved as {new_filename}")
            final_filename = new_filename
            already_saved = True
            in_replay = False
        
            # Confirmation overlay
            cv2.putText(frame, "SAVED", (200, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.imshow('Playback', frame)
            cv2.waitKey(1000)
            return
        elif key == ord('n') and not already_saved:
            cap_play.release()
            cv2.destroyAllWindows()
            os.remove(filename)
            print("Recording discarded.")
            final_filename = None
            already_saved = True
            in_replay = False
            return
        elif key in [ord('q'), 27]:
            break

    if cap_play.isOpened():
        cap_play.release()
    cv2.destroyAllWindows()
    in_replay = False
    # Reset final_filename after playback exit to avoid replays
    final_filename = None


signal.signal(signal.SIGINT, cleanup_and_exit)

if not cap.isOpened():
    print("Cannot open camera")
    sys.exit()

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Forcing recording FPS: {desired_fps}")

def main_loop():
    global recording, out, final_filename, last_record_time

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame")
            break

        now = time.time()

        if recording:
            if now - last_record_time >= 1.0 / desired_fps:
                out.write(frame)
                last_record_time = now
            cv2.putText(frame, "REC", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow('USB Camera Feed', frame)

        key = cv2.waitKey(1) & 0xFF

        if key in [ord('q'), 27]:
            if final_filename and not in_replay:
                play_recording(final_filename)
                # final_filename will be reset inside play_recording now
            else:
                break
        elif key == ord('x'):
            print("Closing camera.")
            break
        elif key == ord('r'):
            if not recording:
                print("Recording started.")
                out = cv2.VideoWriter(temp_filename, cv2.VideoWriter_fourcc(*'XVID'),
                                      desired_fps, (frame_width, frame_height))
                recording = True
                last_record_time = time.time()
            else:
                print("Recording stopped.")
                recording = False
                out.release()
                out = None
                final_filename = temp_filename

    cleanup_and_exit()

main_loop()