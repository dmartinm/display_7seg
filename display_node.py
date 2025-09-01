#!/usr/bin/env python3
"""
ROS 2 node for 7-segment display with dynamic error updates.

Features:
- Default display shows no errors (0000)
- First digit shows number of errors
- Loop-start indicator '---' briefly displayed
- Cycles through multiple errors
- Updates dynamically with new messages
"""

import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from mydisplay import display, show_no_errors, TEXT_TO_NUMERIC_ERROR

class DisplayNode(Node):
    """ROS 2 node for 7-segment display with dynamic updates."""

    def __init__(self):
        super().__init__('display_node')
        self.subscription = self.create_subscription(
            String,
            'sensor_errors',
            self.listener_callback,
            10
        )

        # Thread-safe storage for current errors
        self.lock = threading.Lock()
        self.active_errors = []

        # Start display update loop in background thread
        self.display_thread = threading.Thread(target=self.display_loop, daemon=True)
        self.display_thread.start()

        # Initialize display with no errors
        show_no_errors(display)

    def listener_callback(self, msg):
        """Update error list dynamically when a new message arrives."""
        text = msg.data.strip()
        errors = [e.strip() for e in text.split(',') if e.strip()]
        with self.lock:
            self.active_errors = errors.copy()

    def display_loop(self):
        """Continuously update display based on current error list."""
        import time

        current_index = 0
        loop_start_code = "---"
        loop_start_delay = 0.3
        error_delay = 1.0

        while True:
            with self.lock:
                errors = self.active_errors.copy()

            if not errors:
                # No errors: show 0000
                show_no_errors(display)
                time.sleep(error_delay)
                continue

            num_errors = str(len(errors))[:1]

            # Show loop-start indicator briefly
            display.print(num_errors + loop_start_code)
            display.colon = False
            time.sleep(loop_start_delay)

            # Cycle through current errors
            for code_text in errors:
                code = TEXT_TO_NUMERIC_ERROR.get(code_text.lower(), "999")
                code_str = str(code).rjust(3, "0")[-3:]
                display.print(num_errors + code_str)
                display.colon = False
                time.sleep(error_delay)

def main(args=None):
    rclpy.init(args=args)
    node = DisplayNode()

    # Run ROS 2 in a background thread
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    # Run Tkinter GUI in the main thread
    try:
        display.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
