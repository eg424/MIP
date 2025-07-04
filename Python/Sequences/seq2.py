import serial
import time

PORT = 'COM3'
BAUDRATE = 9600

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(1)
        while ser.in_waiting:
            print(ser.readline().decode().strip())

        start_time = time.time()

        while time.time() - start_time < 5:
            # Diagonal push
            ser.write(b'0,1,0,2.5\n')
            print("Sent: 0,1,0,2.5")
            time.sleep(0.5)

            # Zero
            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)

            # Opposite diagonal
            ser.write(b'0,-1,0,2.5\n')
            print("Sent: 0,-1,0,2.5")
            time.sleep(0.5)

            # Zero
            ser.write(b'0,0,0,0\n')
            print("Sent: 0,0,0,0")
            time.sleep(0.5)

if __name__ == "__main__":
    main()