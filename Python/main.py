import cv2
import signal
import sys
import os
import datetime
import time
import threading
import queue
import serial
import importlib
import math
from moduleDetection import detect_modules, process_frame
import matplotlib
import pathPlanning

# Globals
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
recording = False
out = None
final_filename = None
in_replay = False
last_record_time = time.time()
current_input_string = ""
waiting_for_input = True 
input_queue = queue.Queue()
ser = None
pwm_zeroed = False 
last_pwm_send_time = 0
auto_playback_filename = None
colour_map = matplotlib.colormaps['tab10'].resampled(10)
sequence_stop_event = threading.Event()

# Setup
PORT = 'COM3'
BAUDRATE = 9600
TIMEOUT = 2
DESIRED_FPS = 30
TEMP_FILENAME = "temp_recording.avi"
FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


def serial_thread():
    global ser, current_input_string, waiting_for_input, pwm_zeroed, in_replay
    time.sleep(0.5)
    
    named_sequences = {"square", "M1_straight", "M1M2_straight", "closed"}
    valid_sequences = {str(i) for i in range(1,15)}.union({f"seq{i}" for i in range(1,15)}, named_sequences)

    while True:
        if waiting_for_input:
            if in_replay:
                continue
            
            print("\nInput sequence to run:")
            print("  - Enter sequence number (e.g. 1) or name (e.g. seq1)")
            print("  - Or enter currents as comma-separated values (e.g. 3.0, 1.5, -2.0, 0.5) for manual input")
            
            choice = input("Enter desired sequence: ").strip()
            
            # Detect manual PWM input (comma-separated floats)
            if ',' in choice:
                try:
                    floats = [float(p.strip()) for p in choice.split(',')]
                    current_input_string = choice
                    input_queue.put(choice)
                    waiting_for_input = False
                    if ser.is_open:
                        time.sleep(0.5)
                        ser.write((choice + '\n').encode())
                    start_recording()
                except ValueError:
                    print("Invalid currents input. Please enter comma-separated floats.")
                continue

            if choice in valid_sequences:
                if choice.isdigit():
                    seq_name = f"seq{choice}"
                else:
                    seq_name = choice
                    
                current_input_string = seq_name
                input_queue.put(seq_name)
                close_serial()
                 
                run_seq(seq_name)
                open_serial()
                waiting_for_input = False
                continue
                
            # Path Planning Mode
            if choice.lower() == "pathplan":
                waiting_for_input = False
                current_input_string = "pathplan"
                print("Path Planning mode selected. Recording will start when you set a goal and press Enter.")
                try:
                    run_path_planning()
                except Exception as e:
                    print(f"[main] Error running path planning: {e}")
                waiting_for_input = True
                continue

            else:
                print("Invalid choice. Please enter a valid sequence number/name or manual currents.")
        else:
            time.sleep(0.1)
            

def open_serial():
    global ser
    if ser is None or not ser.is_open:
        try:
            ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    timeout=TIMEOUT,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
)
            time.sleep(1)
            # print("[main] Serial port opened.")
        except Exception as e:
            print(f"[main] Could not open serial port: {e}")
            

def close_serial():
    global ser
    if ser and ser.is_open:
        try:
            ser.close()
            # print("[main] Serial port closed.")
        except:
            pass
        ser = None


def send_zero_pwm():
    global ser, pwm_zeroed, last_pwm_send_time
    if ser and ser.is_open:
        ser.write("0,0,0,0\n".encode())
        pwm_zeroed = True
        last_pwm_send_time = time.time()
        
            
def run_seq(seq_name):
    global recording, sequence_stop_event
    
    seq_path = f"Sequences.{seq_name}"

    try:
        module = importlib.import_module(seq_path)
        print(f"Running sequence: {seq_name}")
        
        # If the module supports stopping, pass the stop event
        if hasattr(module, "main"):
            start_recording()
            if "stop_event" in module.main.__code__.co_varnames:
                module.main(stop_event=sequence_stop_event)
            else:
                module.main()
        else:
            print(f"'{seq_name}' does not have a 'main()' function.")
            return

        if not sequence_stop_event.is_set():
            print(f"Sequence '{seq_name}' finished running.")
        
        if recording:
            print("Stopping recording after sequence completion.")
            stop_recording()

    except ModuleNotFoundError:
        print(f"Sequence '{seq_name}' not found.")
    except AttributeError:
        print(f"'{seq_name}' does not have a 'main()' function.")
    
    sequence_stop_event.clear()
 

def run_path_planning():
    # Run live_mode in the current thread (blocking)
    print("[main] Starting path planning mode. Press 'q' in path planning window to exit.")
    open_serial()
    pathPlanning.live_mode(ser)
    #pathPlanning2.live_mode(ser)
 

def start_recording():
    global recording, out, last_record_time, waiting_for_input
    
    _, frame = cap.read()
    recording = True

    if recording:
        if not input_queue.empty():
            input_queue.get()

        out = cv2.VideoWriter(TEMP_FILENAME, cv2.VideoWriter_fourcc(*'XVID'), DESIRED_FPS, (FRAME_WIDTH, FRAME_HEIGHT))
        recording = True
        last_record_time = time.time()
        waiting_for_input = False
        cv2.putText(frame, "REC", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        print("Recording started. Press 'R' to stop recording.")
            

def stop_recording():
    global recording, out, waiting_for_input, final_filename, auto_playback_filename
    global pwm_zeroed, last_pwm_send_time

    recording = False
    if out:
        out.release()
        out = None
    sequence_stop_event.set()
    send_zero_pwm()
    pwm_zeroed = True
    last_pwm_send_time = 0

    print("Recording stopped. Press 'Q' or 'ESC' to play the recording.")
    final_filename = TEMP_FILENAME
    auto_playback_filename = TEMP_FILENAME
    waiting_for_input = True

    # Clear any pending inputs
    with input_queue.mutex:
        input_queue.queue.clear()


def save_video(filename, current_input_string):
    # Prepare new filename
    safe_input = current_input_string.replace(' ', '')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"[{safe_input}]_{timestamp}.avi"
    
    # Rename original file
    os.rename(filename, new_filename)
    print(f"Recording saved as {new_filename}")
    
    # Open renamed video for reading
    cap_video = cv2.VideoCapture(new_filename)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = cap_video.get(cv2.CAP_PROP_FPS)
    width = int(cap_video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap_video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    temp_overlay_filename = f"overlay_{new_filename}"
    out_video = cv2.VideoWriter(temp_overlay_filename, fourcc, fps, (width, height))
    
    for frame_idx in range(total_frames):
        ret, frame = cap_video.read()
        if not ret:
            break
        
        seconds = int(frame_idx / fps)
        cv2.putText(frame, f"({seconds} s)", (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        out_video.write(frame)
    
    cap_video.release()
    out_video.release()
    
    # Replace original file with the overlayed video
    os.remove(new_filename)
    os.rename(temp_overlay_filename, new_filename)
    already_saved = True
    
    return new_filename


def save_img(new_filename, trajectories, fps, total_frames, initial_frame, initial_centroids):
   
    # Reload last frame without overlay text for full trajectory image
    cap_reopen = cv2.VideoCapture(new_filename)
    cap_reopen.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, last_frame = cap_reopen.read()
    cap_reopen.release()

    def draw_trajectory(img, traj_segment, colour_map):
        num_centroids = len(traj_segment[0]) if len(traj_segment) > 0 else 0
        for i in range(num_centroids):
            points = []
            for t in traj_segment:
                if len(t) > i:
                    points.append(t[i])
            if len(points) < 2:
                continue
            if num_centroids == 1:
                colour = (0, 0, 255)
            else:
                c = colour_map(i)
                colour = (int(c[2]*255), int(c[1]*255), int(c[0]*255))
            for j in range(1, len(points)):
                cv2.line(img, points[j-1], points[j], colour, 2)

    # Save full trajectory image
    traj_img = last_frame.copy()
    draw_trajectory(traj_img, trajectories, colour_map)
    img_filename = new_filename.rsplit('.', 1)[0] + "_trajectory.png"
    cv2.imwrite(img_filename, traj_img)
    print(f"Full trajectory image saved as '{img_filename}'")

    # If video > 30 s, save trajectory images every 10 s
    duration_sec = total_frames / fps
    if duration_sec >= 30:
        interval = 10
        num_intervals = math.floor(duration_sec / interval)
        for i in range(1, num_intervals + 1):
            frame_idx = int(i * interval * fps)
            if frame_idx >= total_frames:
                break
            cap_reopen = cv2.VideoCapture(new_filename)
            cap_reopen.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap_reopen.read()
            cap_reopen.release()
            if not ret:
                print(f"Failed to read frame at {frame_idx} for interval {i}.")
                continue
            
            # Draw trajectory up to this frame only
            traj_segment = trajectories[:frame_idx + 1]
            img_interval = frame.copy()
            draw_trajectory(img_interval, traj_segment, colour_map)
            interval_img_filename = new_filename.rsplit('.', 1)[0] + f"_trajectory_{i*interval}s.png"
            cv2.imwrite(interval_img_filename, img_interval)
            print(f"Trajectory image at {i*interval}s saved as '{interval_img_filename}'")

    # Save initial separation image
    if initial_frame is not None and len(initial_centroids) > 1:
        init_dist_img = initial_frame.copy()
        process_frame(init_dist_img)
        cv2.putText(init_dist_img, "(0 s)", (10, init_dist_img.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        init_dist_filename = new_filename.rsplit('.', 1)[0] + "_initial_distance.png"
        cv2.imwrite(init_dist_filename, init_dist_img)
        print(f"Initial distance image saved as '{init_dist_filename}'")


def detect_merge(trajectories, new_filename, fps, initial_frame, initial_centroids):
    if initial_frame is not None and len(initial_centroids) > 1:
        merge_frame_idx = None
        for idx, centroids_in_frame in enumerate(trajectories):
            if len(centroids_in_frame) == 1:
                merge_frame_idx = idx
                break

        if merge_frame_idx is not None:
            merge_time_sec = merge_frame_idx / fps
            print(f"Modules merged into one at frame {merge_frame_idx}, approx {merge_time_sec:.2f} seconds.")
            with open(new_filename.rsplit('.', 1)[0] + "_merge_time.txt", "w") as f:
                f.write(f"Modules merged into one at frame {merge_frame_idx} (time = {merge_time_sec:.2f} s)\n")
        else:
            print("Modules did not merge into one during the recording.")


def play_recording(filename):
    global final_filename, in_replay, waiting_for_input
    
    print(f"Playing back: {filename}")
    cap_play = cv2.VideoCapture(filename)
    total_frames = int(cap_play.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_play.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)

    playing = True
    current_frame = 0
    already_saved = False
    trajectories = []
    in_replay = True

    initial_frame = None
    initial_centroids = None

    def on_trackbar(val):
        nonlocal current_frame
        current_frame = val
        cap_play.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    cv2.namedWindow('Playback')
    cv2.createTrackbar('Position', 'Playback', 0, total_frames - 1, on_trackbar)
    
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
            centroids, _ = detect_modules(frame)
            
            # Save first frame and initial centroids for later check
            if initial_frame is None:
                initial_frame = frame.copy()
                initial_centroids = centroids.copy()

            trajectories.append(centroids)
            
        else:
            cap_play.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap_play.read()
            if not ret:
                break

        # Interface Overlay
        overlay_text = "PAUSE" if not playing else "PLAY"
        cv2.putText(frame, f"[{overlay_text}] Space: toggle | Q/ESC: exit | S: save | N: discard", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Duration Overlay
        current_time = str(datetime.timedelta(seconds=current_frame / fps))
        cv2.putText(frame, f"Duration: {current_time}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw trajectory paths on every frame during playback or pause
        for i in range(len(trajectories[0]) if len(trajectories) > 0 else 0):
            points = []
            for t in trajectories:
                if len(t) > i:
                    points.append(t[i])
            if len(points) < 2:
                continue
            if len(trajectories[0]) == 1:
                colour = (0, 0, 255)
            else:
                c = colour_map(i)
                colour = (int(c[2]*255), int(c[1]*255), int(c[0]*255))
            for j in range(1, len(points)):
                cv2.line(frame, points[j-1], points[j], colour, 2)

        # End of Video Overlay
        if current_frame == total_frames - 1 and not playing:
            cv2.putText(frame, "End of video. Press Space to restart or Q to exit.", (10, FRAME_HEIGHT - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow('Playback', frame)
        key = cv2.waitKey(delay if playing else 50) & 0xFF

        # Play/Pause
        if key in [ord(' '), ord('p')] and not playing:
            playing = not playing
            if current_frame == total_frames - 1:
                cap_play.set(cv2.CAP_PROP_POS_FRAMES, 0)
                current_frame = 0
                
        # Save Recording and Images    
        elif key == ord('s') and not already_saved:
            cap_play.release()
            cv2.destroyAllWindows()
            
            new_filename = save_video(filename, current_input_string)

            # Save trajectory image using last frame and trajectories
            if len(trajectories) > 0 and len(trajectories[0]) > 0:
                save_img(new_filename, trajectories, fps, total_frames, initial_frame, initial_centroids) # Test
                        
            # Confirmation Overlay
            cv2.putText(frame, "SAVED", (200, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.imshow('Playback', frame)
            cv2.waitKey(500)
            cv2.destroyWindow('Playback')
                    
            final_filename = new_filename
            already_saved = True
            in_replay = False
            waiting_for_input = True
            return
        
        # Discard Recording
        elif key == ord('n') and not already_saved:
            cap_play.release()
            cv2.destroyAllWindows()
            
            if os.path.exists(filename):
                os.remove(filename)
            print("Recording discarded.")
            
            final_filename = None
            already_saved = False
            in_replay = False
            waiting_for_input = True
            
            return
        
        # Exit
        elif key in [ord('q'), 27]:
            break

    cap_play.release()
    cv2.destroyAllWindows()
    in_replay = False
    
    # Safety prompt to save/discard
    if not already_saved:
        while True:
            choice = input("Save this recording? (y/n): ").strip().lower()
            if choice == 'y':
                safe_input = current_input_string.replace(' ', '')
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"[{safe_input}]_{timestamp}.avi"
                os.rename(filename, new_filename)
                print(f"Recording saved as {new_filename}")
                final_filename = new_filename
                break
            elif choice == 'n': # Test if it works fine, missing a few flags
                os.remove(filename)
                print("Recording discarded.")
                final_filename = None
                break

    waiting_for_input = True


def main_loop():
    global recording, out, final_filename, last_record_time, waiting_for_input
    global pwm_zeroed, last_pwm_send_time, auto_playback_filename

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()

        # Periodic zero PWM if in zero-mode
        if pwm_zeroed and ser and ser.is_open:
            if now - last_pwm_send_time > 0.5:
                send_zero_pwm()
                last_pwm_send_time = now

        if recording:
            if out is not None and now - last_record_time >= 1.0 / DESIRED_FPS:
                out.write(frame)
                last_record_time = now
            cv2.putText(frame, "REC", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        frame = process_frame(frame)
        
        # Display frame
        cv2.imshow('USB Camera Feed', frame)
        key = cv2.waitKey(1) & 0xFF

        # Automated playback after sequence finishes            
        if auto_playback_filename:
            filename_to_play = auto_playback_filename
            auto_playback_filename = None  # Reset before playing
            play_recording(filename_to_play)
            final_filename = None  # It will be reset in playback if saved/discarded
            input_queue.queue.clear() # Test
            waiting_for_input = True
        
        # Press 'X' to return to live feedback
        elif key == ord('x'):
            break
        
        # Press 'R' to stop recording
        elif key == ord('r'):
            if not recording:
                start_recording()
            else:
                stop_recording() # Test if it works
    cleanup_and_exit()


def cleanup_and_exit(signum=None, frame=None):
    print("\nExiting and releasing resources...")
    send_zero_pwm()
    if cap.isOpened():
        cap.release()
    if out is not None:
        out.release()
    if ser is not None and ser.is_open:
        ser.close()
    cv2.destroyAllWindows()
    sys.exit(0)
    

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    open_serial()
    thread = threading.Thread(target=serial_thread, daemon=True)
    thread.start()
    main_loop()