import serial
import time

PORT = 'COM3'
BAUDRATE = 9600

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(1)  # Wait for Arduino to reset
        
        # Clear any initial data
        while ser.in_waiting:
            print(ser.readline().decode().strip())

        start_time = time.time()

        while time.time() - start_time < 5:
            ser.write(b'0,0.4,0,0\n')
            print("Sent: 0,0.4,0,0")
            time.sleep(0.2)

            ser.write(b'0,0,0,2\n')
            print("Sent: 0,0,0,2")
            time.sleep(0.3)

            # Reset to 0,0,0,0
            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.3)

if __name__ == "__main__":
    main()