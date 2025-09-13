"""
Finite State Machine (FSM) simulator for 3D rotational command sequences.

- Simulates rotations along three axes: Theta (X-axis), Beta (Y-axis), and Alpha (Z-axis).
- Processes sequential movement commands: 'UP', 'DOWN', 'LEFT', and 'RIGHT', including diagonal interactions.
- Tracks command history, first command type, and last Alpha-modifying command to determine subsequent rotations.
- Automatically wraps Alpha rotations to stay within [-180°, 180°].
- Provides textual feedback for each command, showing updated angles and reasoning behind adjustments.
- Supports live user interaction with reset and exit options.
- Includes move feedback functionality to report distances travelled versus goal position.
"""

class FiniteStateMachine:
    def __init__(self):
        self.theta_degrees = 0
        self.beta_degrees = 0
        self.alpha_degrees = 0
        self.command_count = 0
        self.first_command_type = None
        self.last_alpha_command = None
        self.history = []

    def reset(self):
        self.__init__()
        print("\n--- Simulator Reset ---")
        self._print_current_state()

    def _print_current_state(self):
        print(f"Current State (Command Count: {self.command_count}):")
        print(f"  Theta (X-axis): {self.theta_degrees}°")
        print(f"  Beta (Y-axis): {self.beta_degrees}°")
        print(f"  Alpha (Z-axis): {self.alpha_degrees}°")
        print("-----------------------")

    def _wrap_alpha(self):
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

    # Modify to add diagonal moves
    def process_command(self, command):
        command = command.upper()
        if command not in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            print(f"Invalid command: '{command}'. Use UP, DOWN, LEFT, or RIGHT.")
            return

        self.command_count += 1
        self.history.append(command)
        print(f"\nProcessing Command #{self.command_count}: {command}")

        if self.command_count == 1:
            self.first_command_type = command
            self._handle_initial_command(command)
            self._print_current_state()
            return

        self._handle_subsequent_command(command)
        self._print_current_state()

    def _handle_initial_command(self, command):
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

    def _handle_subsequent_command(self, command):
        """FSM transitions stored in dictionaries to remove redundancy."""
        update = None
        table = {
            'LEFT': {
                'DOWN': ('set', lambda: 180 if self.alpha_degrees > 0 else -180, "LEFT followed by DOWN"),
                'UP': ('add', -90, "LEFT followed by UP"),
            },
            'RIGHT': {
                'DOWN': ('set', -180, "RIGHT followed by DOWN"),
                'UP': ('add', 90, "RIGHT followed by UP"),
            },
            'DOWN': {
                'LEFT': ('add', -90, "DOWN followed by LEFT"),
                'RIGHT': ('add', 90, "DOWN followed by RIGHT"),
            },
            'UP': {
                'LEFT': ('add', 90, "UP followed by LEFT"),
                'RIGHT': ('add', -90, "UP followed by RIGHT"),
            }
        }

        # Special case: after first command, no alpha command yet
        if self.last_alpha_command is None:
            if self.first_command_type in ['UP', 'DOWN'] and command in ['LEFT', 'RIGHT']:
                self._set_alpha(90 if command == 'LEFT' else -90,
                                f"first {command} after {self.first_command_type}",
                                command)
            elif self.first_command_type in ['LEFT', 'RIGHT'] and command in ['UP', 'DOWN']:
                delta = 90 if (command, self.first_command_type) in [('DOWN', 'LEFT'), ('UP', 'RIGHT')] else -90
                self._add_alpha(delta,
                                f"first {command} after {self.first_command_type}",
                                command)
            else:
                print("  No alpha change (irrelevant command after initial rotation).")
            return

        if self.last_alpha_command in table and command in table[self.last_alpha_command]:
            mode, val, reason = table[self.last_alpha_command][command]
            if callable(val):
                val = val()
            if mode == 'set':
                self._set_alpha(val, reason, command)
            else:
                self._add_alpha(val, reason, command)
        else:
            print(f"  No alpha change ({self.last_alpha_command} followed by {command})")
            
    def apply_move_feedback(self, distance_travelled_px, distance_to_goal_px):
        print(f"[FSM] Move feedback — travelled {distance_travelled_px:.1f} px, {distance_travelled_px / (271/32):.2f} mm")
        print(f"[FSM] Remaining straight-line to goal: {distance_to_goal_px:.1f} px, {distance_to_goal_px / (271/32):.2f} mm")
        goal_threshold_px = 1
        reached = distance_to_goal_px <= goal_threshold_px
        if reached:
            print("[FSM] Goal considered reached by FSM threshold.")
        return reached
    

if __name__ == "__main__":
    simulator = FiniteStateMachine()
    print("Available commands: UP, DOWN, LEFT, RIGHT")
    print("Type 'EXIT' to quit or 'RESET' to reset.")
    while True:
        user_input = input("\nEnter command (e.g., UP, LEFT): ").strip().upper()
        if user_input == 'EXIT':
            break
        elif user_input == 'RESET':
            simulator.reset()
        else:
            simulator.process_command(user_input)