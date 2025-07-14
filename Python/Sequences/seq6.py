# Change
import serial
import time

PORT = 'COM3'
BAUDRATE = 9600

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(2)  # Wait for Arduino reset

        # Define rotation steps (HX, HY currents)
        steps = [
            (0, 1.0),
            (0.7, 0.7),
            (1.0, 0),
            (0.7, -0.7),
            (0, -1.0),
            (-0.7, -0.7),
            (-1.0, 0),
            (-0.7, 0.7)
        ]

        # Repeat rotation for 5 seconds
        start_time = time.time()
        delay = 0.15

        while time.time() - start_time < 5:
            for hx, hy in steps:
                command = f"0,{hx},0,{hy}\n"
                ser.write(command.encode())
                print(f"Sent: {command.strip()}")
                time.sleep(delay)

        # Stop currents
        ser.write(b"0,0,0,0\n")
        print("Sent: 0,0,0,0")

if __name__ == "__main__":
    main()
