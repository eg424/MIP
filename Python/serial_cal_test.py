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

            print("Connected to Arduino. Enter initial currents for MX, HX, MY, HY (comma-separated):")

            while True:
                try:
                    # Get user input from serial (e.g., "0,0,0,0")
                    user_input = input("Enter currents (e.g. 0, 0, 0, 0): ").strip()

                    # Parse the user input into MX, HX, MY, HY
                    try:
                        mx, hx, my, hy = map(float, user_input.split(','))
                    except ValueError:
                        print("Invalid input. Please enter four numbers separated by commas.")
                        continue

                    # Validate the input for Hy to make sure it's not above 10 already
                    #if hx > 10:
                    if hy > 10:
                        print("Current must start at a value less than or equal to 10.")
                        continue

                    print(f"Starting with currents: MX={mx}, HX={hx}, MY={my}, HY={hy}")

                    # Start the loop to send commands
                    #while hx <= 10.0:
                    while hy <= 10:
                        # Create the command string with current values
                        command = f"{mx},{hx},{my},{hy}"

                        # Send the command to Arduino
                        ser.write((command + '\n').encode())
                        print(f"Sent command: {command}")

                        # Read the response from Arduino
                        time.sleep(0.2)
                        while ser.in_waiting:
                            line = ser.readline().decode().strip()
                            print("Arduino:", line)

                        # Increment input by 0.5
                        #hx += 0.5
                        hy += 0.5

                        # Wait for 3 seconds before sending the next command
                        time.sleep(3)

                    ser.write("0,0,0,0\n".encode())                    
                    print("Reached 10A or higher. Stopping.")

                    # Wait for the next user input after the loop ends
                    print("Enter a new command or Ctrl+C to exit.")
                
                except KeyboardInterrupt:
                    ser.write("0,0,0,0\n".encode())
                    print("\nExiting.")
                    break
                except Exception as e:
                    print("Error:", e)

    except serial.SerialException as e:
        print(f"Failed to connect on {PORT}: {e}")

if __name__ == "__main__":
    main()
