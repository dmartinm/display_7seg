"""
mydisplay.py - 7-segment display simulator and hardware interface.

Supports simulation using Tkinter or real Adafruit HT16K33 hardware.
Provides functions to display single or multiple sensor errors and
show a no-error state.
"""

USE_SIM = True  # Set False for Raspberry Pi hardware

if USE_SIM:
    import tkinter as tk
    import threading
    import time

    # -----------------------------
    # Segment shapes relative to each digit canvas
    # -----------------------------
    SEGMENTS = {
        "a": [(10, 5, 90, 5, 80, 15, 20, 15)],
        "b": [(90, 5, 100, 15, 100, 65, 90, 75)],
        "c": [(90, 85, 100, 95, 100, 145, 90, 155)],
        "d": [(10, 145, 90, 145, 80, 135, 20, 135)],
        "e": [(0, 85, 10, 95, 10, 145, 0, 135)],
        "f": [(0, 5, 10, 15, 10, 65, 0, 75)],
        "g": [(10, 75, 20, 65, 80, 65, 90, 75, 80, 85, 20, 85)],
    }

    DIGITS = {
        "0": "abcdef",
        "1": "bc",
        "2": "abged",
        "3": "abgcd",
        "4": "fgbc",
        "5": "afgcd",
        "6": "afgcde",
        "7": "abc",
        "8": "abcdefg",
        "9": "abcfgd",
        " ": "",
        "-": "g",
    }

    # -----------------------------
    # Single 7-segment digit class
    # -----------------------------
    class SevenSegDigit:
        """Represents a single 7-segment digit in the simulator."""

        def __init__(self, root, x_offset=0):
            """Initialize a digit on the given Tk root at x_offset."""
            self.canvas = tk.Canvas(root, width=110, height=160, bg="black", highlightthickness=0)
            self.canvas.place(x=x_offset, y=0)
            self.segs = {}
            for name, coords in SEGMENTS.items():
                self.segs[name] = self.canvas.create_polygon(coords, fill="gray20", outline="")
            self.dp = self.canvas.create_oval(95, 145, 105, 155, fill="gray20", outline="")

        def set_char(self, char, show_dp=False):
            """Set the character to display on this digit; optionally show decimal point."""
            active = DIGITS.get(char, "")
            for name, seg_id in self.segs.items():
                self.canvas.itemconfig(seg_id, fill="red" if name in active else "gray20")
            self.canvas.itemconfig(self.dp, fill="red" if show_dp else "gray20")

    # -----------------------------
    # 4-digit 7-segment display class
    # -----------------------------
    class Seg7x4:
        """Simulator for a 4-digit 7-segment display with optional colon."""

        def __init__(self, i2c=None, address=0x70):
            """Initialize simulator window and digits."""
            self.root = tk.Tk()
            self.root.title("7-Segment Display Simulator")
            self.root.geometry(f"{20 + 4*115 + 20}x200")  # Increase width for spacing
            self.digits = [SevenSegDigit(self.root, x_offset=20 + i*115) for i in range(4)]

            # Colon in center
            self.colon_canvas = tk.Canvas(self.root, width=20, height=160, bg="black", highlightthickness=0)
            self.colon_canvas.place(x=230, y=0)
            self.colon1 = self.colon_canvas.create_oval(5, 50, 15, 60, fill="gray20", outline="")
            self.colon2 = self.colon_canvas.create_oval(5, 100, 15, 110, fill="gray20", outline="")
            self._colon = False

        def print(self, text):
            """Display a string of up to 4 digits on the display."""
            text = str(text).rjust(4, "0")[-4:]
            for i, ch in enumerate(text):
                self.digits[i].set_char(ch)

        @property
        def colon(self):
            """Return current colon state (True/False)."""
            return self._colon

        @colon.setter
        def colon(self, state: bool):
            """Set colon visibility on the display."""
            self._colon = state
            color = "red" if state else "gray20"
            self.colon_canvas.itemconfig(self.colon1, fill=color)
            self.colon_canvas.itemconfig(self.colon2, fill=color)

        def run(self):
            """Run the Tk main loop for the simulator."""
            self.root.mainloop()

    display = Seg7x4()

    # -----------------------------
    # Text → numeric error mapping
    # -----------------------------
    TEXT_TO_NUMERIC_ERROR = {
        "lidar_com":    "101",
        "lidar_fail":   "201",
        "emi_com":      "102",
        "emi_fail":     "202",
        "imu_com":      "103",
        "imu_fail":     "203",
        "raspberry_com":"104",
        "raspberry_fail":"204",
        "camera_com":   "105",
        "camera_fail":  "205",
        "ip_mesh_com":  "106",
        "ip_mesh_fail": "206",
        "gps_com":      "107",
        "gps_fail":     "207",
        "general_fail": "999"  # Catch-all unknown error
    }

    # -----------------------------
    # Display a single error repeatedly
    # -----------------------------
    def show_error_loop(error_number, error_text, display, delay=0.5):
        """
        Display a single error continuously on the display.

        Args:
            error_number (int): First digit to indicate error number.
            error_text (str): Key for TEXT_TO_NUMERIC_ERROR.
            display (Seg7x4): Display object.
            delay (float): Delay in seconds between updates.
        """
        error_number = str(error_number)[0]
        code = TEXT_TO_NUMERIC_ERROR.get(error_text.lower(), "999")

        def loop():
            while True:
                display.print(error_number + code)
                display.colon = False
                time.sleep(delay)

        threading.Thread(target=loop, daemon=True).start()

    # -----------------------------
    # Display multiple errors in a loop
    # -----------------------------
    def show_multiple_text_errors(error_text_list, display, delay=1.0, loop_start_code="---", loop_start_delay=0.3):
        """
        Display multiple errors sequentially, showing loop restart briefly.

        Args:
            error_text_list (list of str): List of error keys.
            display (Seg7x4): Display object.
            delay (float): Delay in seconds per error.
            loop_start_code (str): Temporary code to show loop restart.
            loop_start_delay (float): Duration to show loop_start_code.
        """
        numeric_codes = []
        for txt in error_text_list:
            numeric_codes.append(TEXT_TO_NUMERIC_ERROR.get(txt.lower(), "999"))

        num_errors = str(len(numeric_codes))[:1]

        def loop():
            while True:
                # Show the loop start code briefly
                display.print(num_errors + loop_start_code)
                display.colon = False
                time.sleep(loop_start_delay)

                # Cycle through the actual errors
                for code in numeric_codes:
                    code_str = str(code).rjust(3, "0")[-3:]
                    display.print(num_errors + code_str)
                    display.colon = False
                    time.sleep(delay)

        threading.Thread(target=loop, daemon=True).start()

    # -----------------------------
    # Show no errors
    # -----------------------------
    def show_no_errors(display):
        """Display '0000' to indicate no errors."""
        display.print("0000")
        display.colon = False

# -----------------------------
# Hardware version (Raspberry Pi)
# -----------------------------
else:
    import board
    import busio
    from adafruit_ht16k33.segments import Seg7x4
    import threading
    import time

    i2c = busio.I2C(board.SCL, board.SDA)
    display = Seg7x4(i2c)

    # Dummy run() for hardware
    def _dummy_run():
        pass
    display.run = _dummy_run

    TEXT_TO_NUMERIC_ERROR = {
        "general": "999",
        "overflow": "888",
        "underflow": "001",
        "sensor_fail": "123",
        "invalid_input": "432",
    }

    def show_error_loop(error_number, error_text, display, delay=0.5):
        """Display a single error continuously on hardware."""
        error_number = str(error_number)[0]
        code = TEXT_TO_NUMERIC_ERROR.get(error_text.lower(), "999")

        def loop():
            while True:
                display.print(error_number + code)
                display.colon = False
                time.sleep(delay)

        threading.Thread(target=loop, daemon=True).start()

    def show_multiple_text_errors(error_text_list, display, delay=1.0):
        """Display multiple errors sequentially on hardware."""
        numeric_codes = []
        for txt in error_text_list:
            numeric_codes.append(TEXT_TO_NUMERIC_ERROR.get(txt.lower(), "999"))

        num_errors = str(len(numeric_codes))[:1]

        def loop():
            while True:
                for code in numeric_codes:
                    code_str = str(code).rjust(3, "0")[-3:]
                    display.print(num_errors + code_str)
                    display.colon = False
                    time.sleep(delay)

        threading.Thread(target=loop, daemon=True).start()
