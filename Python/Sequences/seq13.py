import serial
import time
import threading

PORT = 'COM3'
BAUDRATE = 9600

def main(stop_event: threading.Event = None):
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(1)  # Wait for Arduino to reset
        ser.reset_input_buffer()

        # Clear any initial data
        while ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                print(line)
            except UnicodeDecodeError:
                print("[Warning] Could not decode serial line.")

        start_time = time.time()
        
        # +90 around x (theta) from "1"
        ser.write(b'0,0,0,-1.5\n')
        print("Sent: 0,0,0,-1.5")
        time.sleep(0.5)
            
        ser.write(b'0,0,0,0\n')
        print("Sent: 0,0,0,0")
        time.sleep(0.5)

        while time.time() - start_time < 15:
            if stop_event and stop_event.is_set():
                print("Sequence interrupted by user.")
                break
            
            # +90 around z (alpha) from "1"
            ser.write(b'0,0.5,0,0\n')
            print("Sent: 0,0.5,0,0")
            time.sleep(0.5)
            if stop_event and stop_event.is_set():
                break
            
            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)

            # +90 around z (alpha) from "1"
            ser.write(b'0,0,0,1.5\n')
            print("Sent: 0,0,0,1.5")
            time.sleep(0.5)
            if stop_event and stop_event.is_set():
                break

            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)
            
            # +90 around z (alpha) from "1"
            ser.write(b'0,-0.5,0,0\n')
            print("Sent: 0,-0.5,0,0")
            time.sleep(0.5)
            if stop_event and stop_event.is_set():
                break

            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)
            
            # +90 around z (alpha) from "1"
            ser.write(b'0,0,0,-1.5\n')
            print("Sent: 0,0,0,-1.5")
            time.sleep(0.5)
            if stop_event and stop_event.is_set():
                break

            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)