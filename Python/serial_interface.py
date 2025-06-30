import serial
import time

PORT = 'COM3'
BAUDRATE = 9600

def main():
    try:
        # Open serial connection
        with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:
            time.sleep(2)  # Wait for Arduino to reset
            
            # Read initial message
            while ser.in_waiting:
                print(ser.readline().decode().strip())

            while True:
                try:
                    # Get user input
                    user_input = input("Enter currents (e.g. 3.0, 1.5, -2.0, 0.5): ").strip()
                    
                    # Send to Arduino
                    ser.write((user_input + '\n').encode())

                    # Read response
                    time.sleep(0.2)
                    while ser.in_waiting:
                        line = ser.readline().decode().strip()
                        print("Arduino:", line)

                except KeyboardInterrupt:
                    print("\nExiting.")
                    break
                except Exception as e:
                    print("Error:", e)

    except serial.SerialException as e:
        print(f"Failed to connect on {PORT}: {e}")

if __name__ == "__main__":
    main()