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

# Setup
PORT = 'COM3'
BAUDRATE = 9600
CAMERA_INDEX = 1
desired_fps = 30

# Globals
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
recording = False
out = None
temp_filename = "temp_recording.avi"
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


def run_seq_name(seq_name):
    global recording, out, final_filename, waiting_for_input

    try:
        module = importlib.import_module(seq_name)
        print(f"Running sequence: {seq_name}")
        module.main()
        print(f"Sequence '{seq_name}' finished running.")
        
        # Stop recording when sequence finishes
        if recording:
            print("Stopping recording after sequence completion.")
            recording = False
            print(f"Press 'Q' or 'ESC' to play the recording.")
            
            if out:
                out.release()
                out = None   
            final_filename = temp_filename  # Set final filename to temp recording
            auto_playback_filename = temp_filename
            
            # After stopping, start playback interaction automatically
            waiting_for_input = False

    except ModuleNotFoundError:
        print(f"Sequence '{seq_name}' not found.")
    except AttributeError:
        print(f"'{seq_name}' does not have a 'main()' function.")

def serial_thread():
    global ser, current_input_string, waiting_for_input, pwm_zeroed

    ser = serial.Serial(PORT, BAUDRATE, timeout=2)
    time.sleep(0.5)
    print(f"Opened serial port {PORT} at {BAUDRATE} baud.")

    while True:
        if waiting_for_input:
            print("\nInput sequence to run:")
            print("  - Enter sequence number/name (1, 2, 3, seq1, seq2, seq3)")
            print("  - Or enter currents as comma-separated values (e.g. 3.0,1.5,-2.0,0.5) for manual PWM input")
            
            choice = input("Enter sequence number: ").strip()
            
            # Detect manual PWM input (comma-separated floats)
            if ',' in choice:
                parts = choice.split(',')
                try:
                    floats = [float(p.strip()) for p in parts]
                    # If floats parsed successfully, accept manual input directly
                    current_input_string = choice
                    input_queue.put(choice)
                    waiting_for_input = False

                    if ser and ser.is_open:
                        ser.write((choice + '\n').encode())
                        pwm_zeroed = False
                except ValueError:
                    print("Invalid manual input format. Please enter comma-separated numbers.")
            
            # Detect sequence input
            elif choice in {"1", "2", "3", "seq1", "seq2", "seq3"}:
                seq_name = choice if choice.startswith("seq") else f"seq{choice}"

                current_input_string = seq_name
                input_queue.put(seq_name)
                if ser and ser.is_open:
                    ser.close()
                run_seq_name(seq_name)
                ser = serial.Serial(PORT, BAUDRATE, timeout=2)

                waiting_for_input = False

            else:
                print("Invalid choice. Please enter a valid sequence number/name or manual currents.")
        else:
            time.sleep(0.1)
            
            
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


def send_zero_pwm():
    global ser
    if ser and ser.is_open:
        zero_pwm = "0,0,0,0\n"
        ser.write(zero_pwm.encode())


# Playback Functionalities
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

        # Overlay Texts
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

        # Play/Pause
        if key in [ord(' '), ord('p')]:
            if not playing and current_frame == total_frames - 1:
                cap_play.set(cv2.CAP_PROP_POS_FRAMES, 0)
                current_frame = 0
            playing = not playing
            
        # Save Recording    
        elif key == ord('s') and not already_saved:
            cap_play.release()
            cv2.destroyAllWindows()
            
            # Save filename based on the currents input
            safe_input = current_input_string.replace(' ', '')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"[{safe_input}]_{timestamp}.avi"
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
            already_saved = True
            in_replay = False
            waiting_for_input = True
            
            # Clear input queue
            with input_queue.mutex:
                input_queue.queue.clear()
            
            return
        
        elif key in [ord('q'), 27]:
            break

    cap_play.release()
    cv2.destroyAllWindows()
    in_replay = False
    
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
            elif choice == 'n':
                os.remove(filename)
                print("Recording discarded.")
                final_filename = None
                break
            else:
                print("Invalid input, please enter 'y' or 'n'.")

    waiting_for_input = True


def main_loop():
    global recording, out, final_filename, last_record_time, waiting_for_input
    global pwm_zeroed, last_pwm_send_time, auto_playback_filename

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

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
            if now - last_record_time >= 1.0 / desired_fps:
                out.write(frame)
                last_record_time = now
            cv2.putText(frame, "REC", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display frame
        cv2.imshow('USB Camera Feed', frame)
        key = cv2.waitKey(1) & 0xFF

        # Start recording on new input
        if not recording and not input_queue.empty():
            input_queue.get()
            print("Recording started. Press 'R' to stop recording.")
            out = cv2.VideoWriter(temp_filename, cv2.VideoWriter_fourcc(*'XVID'), desired_fps, (frame_width, frame_height))
            recording = True
            last_record_time = time.time()
            waiting_for_input = False
            
        # Automated playback after sequence finishes
        if auto_playback_filename:
            filename_to_play = auto_playback_filename
            auto_playback_filename = None  # Reset before playing
            play_recording(filename_to_play)
            final_filename = None  # It will be reset in playback if saved/discarded
            with input_queue.mutex:
                input_queue.queue.clear()
            waiting_for_input = True

        # Press 'Q' or 'ESC' to see playback; after playback, to return to live feedback
        elif key in [ord('q'), 27]:
            if final_filename and os.path.exists(final_filename) and not in_replay:
                play_recording(final_filename)
                final_filename = None
                # Clear queue until new input
                with input_queue.mutex:
                    input_queue.queue.clear()
                waiting_for_input = True
            else:
                break
        
        # Press 'X' to return to live feedback
        elif key == ord('x'):
            break
        
        # Press 'R' to stop recording
        elif key == ord('r'):
            if not recording:
                print("Press Enter after inputting currents to start recording.")
            else:
                print(f"Recording stopped.")
                recording = False
                if out:
                    out.release()
                    out = None
                final_filename = temp_filename

                send_zero_pwm()
                pwm_zeroed = True
                last_pwm_send_time = 0

    cleanup_and_exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    thread = threading.Thread(target=serial_thread, daemon=True)
    thread.start()
    main_loop()