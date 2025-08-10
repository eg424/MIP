class MagneticModuleSimulator:
    def __init__(self):
        self.theta_degrees = 0
        self.beta_degrees = 0
        self.alpha_degrees = 0

        self.command_count = 0
        self.first_command_type = None
        self.last_alpha_command = None
        self.history = []

    def reset(self):
        self.theta_degrees = 0
        self.beta_degrees = 0
        self.alpha_degrees = 0
        self.command_count = 0
        self.first_command_type = None
        self.last_alpha_command = None
        self.history = []
        print("\n--- Simulator Reset ---")
        self._print_current_state()

    def _print_current_state(self):
        print(f"Current State (Command Count: {self.command_count}):")
        print(f"  Theta (X-axis): {self.theta_degrees}°")
        print(f"  Beta (Y-axis): {self.beta_degrees}°")
        print(f"  Alpha (Z-axis): {self.alpha_degrees}°")
        print("-----------------------")

    def _wrap_alpha(self):
        # Wrap alpha to be within [-180, 180]
        while self.alpha_degrees > 180:
            self.alpha_degrees -= 360
            print(f"  Alpha wrapped to {self.alpha_degrees}° (above +180°)")

        while self.alpha_degrees < -180:
            self.alpha_degrees += 360
            print(f"  Alpha wrapped to {self.alpha_degrees}° (below -180°)")

    def _set_alpha(self, value, reason, caused_by):
        self.alpha_degrees = value
        self.last_alpha_command = caused_by
        print(f"  Alpha set to {self.alpha_degrees}° ({reason}).")
        self._wrap_alpha()

    def _add_alpha(self, delta, reason, caused_by):
        self.alpha_degrees += delta
        self.last_alpha_command = caused_by
        print(f"  Alpha adjusted by {delta:+}° ({reason}).")
        self._wrap_alpha()

    def process_command(self, command):
        command = command.upper()
        if command not in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            print(f"Invalid command: '{command}'. Use UP, DOWN, LEFT, or RIGHT.")
            return

        self.command_count += 1
        self.history.append(command)
        print(f"\nProcessing Command #{self.command_count}: {command}")

        # Initial (first) command behaviour
        if self.command_count == 1:
            self.first_command_type = command
            # rotate around X (theta) for UP/DOWN, Y (beta) for LEFT/RIGHT
            if command == 'UP':
                self.theta_degrees = 90
                print("  Initial rotation: +90° around X-axis (Theta).")
            elif command == 'DOWN':
                self.theta_degrees = -90
                self.alpha_degrees = 180
                print("  Initial rotation: -90° around X-axis (Theta).")
                print("  Alpha set to -180° (initial DOWN command).")
            elif command == 'LEFT':
                self.beta_degrees = 90
                self.alpha_degrees = 90
                print("  Initial rotation: +90° around Y-axis (Beta).")
                print("  Alpha set to +90° (initial LEFT command).")
            elif command == 'RIGHT':
                self.beta_degrees = -90
                self.alpha_degrees = -90
                print("  Initial rotation: -90° around Y-axis (Beta).")
                print("  Alpha set to -90° (initial RIGHT command).")

            self._print_current_state()
            return

        # Helpers
        update_alpha = lambda deg, reason: self._add_alpha(deg, reason, command)
        set_alpha = lambda val, reason: self._set_alpha(val, reason, command)

        # Logic when the first command rotated around X-axis (theta)
        if self.first_command_type in ['UP', 'DOWN']:
            # After an UP/DOWN initial rotation, the next meaningful commands are LEFT/RIGHT
            if self.last_alpha_command is None:
                if command == 'LEFT':
                    self.alpha_degrees = 90
                    self.last_alpha_command = command
                elif command == 'RIGHT':
                    self.alpha_degrees = -90
                    self.last_alpha_command = command
                else:
                    print("  No alpha change (irrelevant command after initial rotation).")
            else:
                if self.last_alpha_command == 'LEFT':
                    if command == 'DOWN':
                        if self.alpha_degrees > 0:
                            self.alpha_degrees = 180
                        else:
                            self.alpha_degrees = -180
                        print(f"  Alpha set to {self.alpha_degrees}° (LEFT followed by DOWN).")
                        self.last_alpha_command = command
                    elif command == 'UP':
                        update_alpha(-90, "LEFT followed by UP")
                    elif command in ['LEFT', 'RIGHT']:
                        print("  No alpha change (LEFT followed by LEFT/RIGHT)")
                    else:
                        print("  No alpha change (irrelevant command after LEFT)")
                elif self.last_alpha_command == 'RIGHT':
                    if command == 'DOWN':
                        self.alpha_degrees = -180
                        print(f"  Alpha set to -180° (RIGHT followed by DOWN).")
                        self.last_alpha_command = command
                    elif command == 'UP':
                        update_alpha(90, "RIGHT followed by UP")
                    elif command in ['LEFT', 'RIGHT']:
                        print(f"  No alpha change (RIGHT followed by {command})")
                    else:
                        print(f"  No alpha change (irrelevant command after RIGHT)")

                elif self.last_alpha_command == 'DOWN':
                    if command == 'LEFT':
                        update_alpha(-90, "DOWN followed by LEFT")
                    elif command == 'RIGHT':
                        update_alpha(90, "DOWN followed by RIGHT")
                    elif command in ['UP', 'DOWN']:
                        print("  No alpha change (DOWN followed by UP/DOWN)")
                    else:
                        print("  No alpha change (irrelevant command after DOWN)")
                elif self.last_alpha_command == 'UP':
                    if command == 'LEFT':
                        update_alpha(90, "UP followed by LEFT")
                    elif command == 'RIGHT':
                        update_alpha(-90, "UP followed by RIGHT")
                    elif command in ['UP', 'DOWN']:
                        print("  No alpha change (UP followed by UP/DOWN)")
                    else:
                        print("  No alpha change (irrelevant command after UP)")
                else:
                    print("  No alpha change (unexpected last alpha command)")

        # Logic when the first command rotated around y-axis (beta)
        elif self.first_command_type in ['LEFT', 'RIGHT']:
            if self.last_alpha_command is None:
                # After a LEFT/RIGHT initial rotation, the next meaningful commands are DOWN/UP
                if command in ['LEFT', 'RIGHT']:
                    print("  No alpha change (irrelevant command after initial rotation).")
                elif command == 'DOWN':
                    if self.first_command_type == 'LEFT':
                        update_alpha(90, 'first DOWN after LEFT')
                    else:
                        update_alpha(-90, 'first DOWN after RIGHT')
                elif command == 'UP':
                    if self.first_command_type == 'LEFT':
                        update_alpha(-90, 'first UP after LEFT')
                    else:
                        update_alpha(90, 'first UP after RIGHT')
            else:
                if self.last_alpha_command == 'DOWN':
                    if command == 'LEFT':
                        update_alpha(-90, 'DOWN followed by LEFT')
                    elif command == 'RIGHT':
                        update_alpha(90, 'DOWN followed by RIGHT')
                    elif command in ['UP', 'DOWN']:
                        print('  No alpha change (DOWN followed by UP/DOWN)')
                    else:
                        print('  No alpha change (irrelevant command after DOWN)')
                elif self.last_alpha_command == 'UP':
                    if command == 'LEFT':
                        update_alpha(90, 'UP followed by LEFT')
                    elif command == 'RIGHT':
                        update_alpha(-90, 'UP followed by RIGHT')
                    elif command in ['UP', 'DOWN']:
                        print('  No alpha change (UP followed by UP/DOWN)')
                    else:
                        print('  No alpha change (irrelevant command after UP)')
                elif self.last_alpha_command == 'LEFT':
                    if command == 'DOWN':
                        if self.alpha_degrees > 0:
                            self.alpha_degrees = 180
                        else:
                            self.alpha_degrees = -180
                        print(f"  Alpha set to {self.alpha_degrees}° (LEFT followed by DOWN).")
                        self.last_alpha_command = command
                    elif command == 'UP':
                        update_alpha(-90, 'LEFT followed by UP')
                    elif command in ['LEFT', 'RIGHT']:
                        print('  No alpha change (LEFT followed by LEFT/RIGHT)')
                    else:
                        print('  No alpha change (irrelevant command after LEFT)')
                elif self.last_alpha_command == 'RIGHT':
                    if command == 'DOWN':
                        self.alpha_degrees = -180
                        print(f"  Alpha set to -180° (RIGHT followed by DOWN).")
                        self.last_alpha_command = command
                    elif command == 'UP':
                        update_alpha(90, 'RIGHT followed by UP')
                    elif command in ['LEFT', 'RIGHT']:
                        print(f"  No alpha change (RIGHT followed by {command})")
                    else:
                        print('  No alpha change (irrelevant command after RIGHT)')
                else:
                    print('  No alpha change (unexpected last alpha command)')
                    
        else:
            print("  Unexpected state: no initial rotation set.")

        self._print_current_state()


if __name__ == "__main__":
    simulator = MagneticModuleSimulator()

    print("Available commands: UP, DOWN, LEFT, RIGHT")
    print("Type 'EXIT' to quit or 'RESET' to reset.")

    while True:
        user_input = input("\nEnter command (e.g., UP, LEFT): ").strip().upper()

        if user_input == 'EXIT':
            print("Exiting simulator. Goodbye!")
            break
        elif user_input == 'RESET':
            simulator.reset()
        else:
            simulator.process_command(user_input)