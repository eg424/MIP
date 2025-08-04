import serial
import time
import threading

PORT = 'COM3'
BAUDRATE = 9600

def main(stop_event: threading.Event = None):
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(1)  # Wait for Arduino to reset

        # Clear any initial data
        while ser.in_waiting:
            print(ser.readline().decode().strip())

        # Run positive commands for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            if stop_event and stop_event.is_set():
                print("Sequence interrupted by user.")
                return

            ser.write(b'0,1,0,0\n')  # positive 1
            print("Sent: 0,1,0,0")
            time.sleep(0.2)
            if stop_event and stop_event.is_set():
                return

            ser.write(b'0,0,0,2.5\n')  # positive 2.5
            print("Sent: 0,0,0,2.5")
            time.sleep(0.2)
            if stop_event and stop_event.is_set():
                return

            ser.write(b'0,0,0,0\n')  # reset
            print("Sent: 0,0,0,0")
            time.sleep(0.1)

        # Pause for 1 second
        print("Pausing for 1 second...")
        time.sleep(1)

        # Run negative commands for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            if stop_event and stop_event.is_set():
                print("Sequence interrupted by user.")
                return

            ser.write(b'0,-1,0,0\n')  # negative -1
            print("Sent: 0,-1,0,0")
            time.sleep(0.2)
            if stop_event and stop_event.is_set():
                return

            ser.write(b'0,0,0,-2.5\n')  # negative -2.5
            print("Sent: 0,0,0,-2.5")
            time.sleep(0.2)
            if stop_event and stop_event.is_set():
                return

            ser.write(b'0,0,0,0\n')  # reset
            print("Sent: 0,0,0,0")
            time.sleep(0.1)

        print("Sequence complete.")