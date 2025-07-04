import serial
import time
import random

PORT = 'COM3'
BAUDRATE = 9600

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
        time.sleep(1)
        while ser.in_waiting:
            print(ser.readline().decode().strip())

        for _ in range(20):
            hx = random.choice([-10, 0, 10])
            hy = random.choice([-10, 0, 10])
            cmd = f"0,{hx},0,{hy}\n"
            ser.write(cmd.encode())
            print(f"Sent: {cmd.strip()}")
            time.sleep(0.3)

        ser.write(b'0,0,0,0\n')
        print("Sent: 0,0,0,0")

if __name__ == "__main__":
    main()