import serial
import time
import sys
import threading
import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, scrolledtext

# --- CONFIGURATION ---
COM_PORT: str = 'COM3'
BAUD_RATE: int = 9600
CODE_LENGTH: int = 6
# Time window configuration (24-hour format)
TIME_WINDOW_START = datetime.time(20, 0)  # 7:00 PM
TIME_WINDOW_END = datetime.time(20, 25)  # 7:05 PM (corrected from 7:55)


# ---------------------

# Data structure for student records
@dataclass
class StudentRecord:
    code: str
    name: str
    arrival_time: datetime.datetime
    status: str  # "On Time", "Early", "Late", "No Access"


class AttendanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance Tracker")
        self.root.geometry("1200x700")

        # Data storage
        self.records: List[StudentRecord] = []
        self.student_names = {
            "13579A": "Christopher El Sabbagh",
            "24680B": "Jude Hobeiche",
            "98765C": "Mark Khalife",
            "12345D": "Joseph Massoud",
        }

        # Serial setup
        self.ser = None
        self.input_buffer = ""
        self.buffer_lock = threading.Lock()

        # Setup GUI
        self.setup_gui()

        # Start serial communication
        self.start_serial()

    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="STUDENT ATTENDANCE TRACKER",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))

        # Status bar
        self.status_var = tk.StringVar(value="Waiting for serial connection...")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Time display
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=0, column=1, sticky=tk.E)

        self.time_var = tk.StringVar()
        time_label = ttk.Label(
            time_frame,
            textvariable=self.time_var,
            font=("Arial", 12)
        )
        time_label.pack()

        # Time window info
        time_info = ttk.Label(
            time_frame,
            text=f"Window: {TIME_WINDOW_START.strftime('%I:%M %p')} - {TIME_WINDOW_END.strftime('%I:%M %p')}",
            font=("Arial", 10)
        )
        time_info.pack(pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Tab 1: Attendance Table
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Attendance Records")

        # Create Treeview for table
        columns = ("ID", "Code", "Name", "Arrival Time", "Status", "Remarks")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        # Define headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Code", text="Code")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Arrival Time", text="Arrival Time")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Remarks", text="Remarks")

        # Define column widths
        self.tree.column("ID", width=50)
        self.tree.column("Code", width=80)
        self.tree.column("Name", width=150)
        self.tree.column("Arrival Time", width=150)
        self.tree.column("Status", width=100)
        self.tree.column("Remarks", width=200)

        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Tab 2: Statistics
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")

        # Statistics labels
        self.stats_vars = {
            "total": tk.StringVar(value="Total: 0"),
            "ontime": tk.StringVar(value="On Time: 0"),
            "early": tk.StringVar(value="Early: 0"),
            "late": tk.StringVar(value="Late: 0"),
            "noaccess": tk.StringVar(value="No Access: 0")
        }

        for i, (key, var) in enumerate(self.stats_vars.items()):
            label = ttk.Label(stats_frame, textvariable=var, font=("Arial", 14))
            label.grid(row=i, column=0, padx=20, pady=10, sticky=tk.W)

        # Tab 3: Log
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Event Log")

        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=80,
            height=25,
            font=("Courier", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 4: Response Codes
        codes_frame = ttk.Frame(notebook)
        notebook.add(codes_frame, text="Response Codes")

        # Response codes info
        codes_text = """
RESPONSE CODES SENT TO PIC:
'1' = Early (correct code but before 7:00 PM)
'0' = Late OR Invalid code (after 7:05 PM OR wrong code)
'2' = On Time (correct code + within 7:00-7:05 PM window)

TIME WINDOW:
Start: 7:00 PM
End: 7:05 PM

VALID STUDENT CODES:
13579A - John Smith
24680B - Sarah Johnson
98765C - Mike Williams
12345D - Emily Davis
54321E - David Brown
67890F - Lisa Miller
"""
        codes_label = scrolledtext.ScrolledText(
            codes_frame,
            width=60,
            height=20,
            font=("Courier", 10)
        )
        codes_label.insert(tk.END, codes_text)
        codes_label.config(state=tk.DISABLED)
        codes_label.pack(padx=10, pady=10)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        # Control buttons
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_table).pack(side=tk.LEFT, padx=5)

        # Start time updater
        self.update_time()

    def update_time(self):
        """Update current time display"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(f"Current Time: {current_time}")
        self.root.after(1000, self.update_time)

    def log_event(self, message: str):
        """Add message to log with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        print(log_entry.strip())

    def get_current_time_status(self):
        """
        Checks current time and returns status:
        - 1: Before 7:00 PM (Early)
        - 2: Between 7:00 PM and 7:05 PM (On Time)
        - 0: After 7:05 PM (Late)
        """
        now = datetime.datetime.now().time()

        if now < TIME_WINDOW_START:
            return 1  # Before 7:00 PM
        elif TIME_WINDOW_START <= now <= TIME_WINDOW_END:
            return 2  # Between 7:00 PM and 7:05 PM
        else:
            return 0  # After 7:05 PM

    def process_code(self, code: str):
        """Process received code and update interface"""
        arrival_time = datetime.datetime.now()
        time_status = self.get_current_time_status()

        # Get student name
        name = self.student_names.get(code, "Unknown Student")

        # Determine status using your logic
        if code in self.student_names:
            # Code is correct
            if time_status == 2:
                # On time
                status = "On Time"
                remarks = "ACCESS GRANTED (within time window)"
                response = '2'
                self.log_event(f"{name}: On time - Access granted")

            elif time_status == 1:
                # Early but NOW ALLOWED
                status = "Early"
                remarks = "ACCESS GRANTED (early, but allowed)"
                response = '1'
                self.log_event(f"{name}: Early - Access granted")

            else:  # time_status == 0
                # After window (late)
                status = "Late"
                remarks = "ACCESS DENIED (after allowed time)"
                response = '0'
                self.log_event(f"{name}: Late - Access denied")

        else:
            # Invalid code
            status = "No Access"
            remarks = "ACCESS DENIED (invalid code)"
            response = '0'
            self.log_event("Unknown: Invalid code")

        # Create record
        record = StudentRecord(
            code=code,
            name=name,
            arrival_time=arrival_time,
            status=status
        )

        # Add to records
        self.records.append(record)

        # Send response to PIC after 1 second
        if self.ser and self.ser.is_open:
            self.log_event(f"Waiting 1 second before sending response: '{response}'")
            time.sleep(1.0)
            self.ser.write(response.encode())
            self.ser.flush()
            self.log_event(f"Sent response '{response}' to PIC")

        # Update GUI
        self.add_to_table(record, remarks)
        self.update_statistics()

        # Update top status bar
        self.status_var.set(f"Last scan: {name} - {remarks}")

    def add_to_table(self, record: StudentRecord, remarks: str):
        """Add record to table"""
        row_id = len(self.records)
        arrival_str = record.arrival_time.strftime("%H:%M:%S")

        # Color coding based on status
        tags = ()
        if record.status == "On Time":
            tags = ("ontime",)
        elif record.status == "Early":
            tags = ("early",)
        elif record.status == "Late":
            tags = ("late",)
        elif record.status == "No Access":
            tags = ("noaccess",)

        self.tree.insert(
            "",
            tk.END,
            values=(row_id, record.code, record.name, arrival_str, record.status, remarks),
            tags=tags
        )

    def update_statistics(self):
        """Update statistics display"""
        total = len(self.records)
        ontime = sum(1 for r in self.records if r.status == "On Time")
        early = sum(1 for r in self.records if r.status == "Early")
        late = sum(1 for r in self.records if r.status == "Late")
        noaccess = sum(1 for r in self.records if r.status == "No Access")

        self.stats_vars["total"].set(f"Total Scans: {total}")
        self.stats_vars["ontime"].set(f"On Time: {ontime}")
        self.stats_vars["early"].set(f"Early: {early}")
        self.stats_vars["late"].set(f"Late: {late}")
        self.stats_vars["noaccess"].set(f"No Access: {noaccess}")

    def clear_all(self):
        """Clear all records"""
        self.records.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_statistics()
        self.log_event("All records cleared")

    def refresh_table(self):
        """Refresh table display"""
        # Clear and rebuild table
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, record in enumerate(self.records):
            self.add_to_table(record, "")

        self.update_statistics()

    def export_csv(self):
        """Export records to CSV file"""
        try:
            filename = f"attendance_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w') as f:
                f.write("ID,Code,Name,Arrival Time,Status\n")
                for i, record in enumerate(self.records):
                    f.write(f"{i},{record.code},{record.name},{record.arrival_time},{record.status}\n")
            self.log_event(f"Data exported to {filename}")
        except Exception as e:
            self.log_event(f"Export failed: {e}")

    def serial_reader_thread(self):
        """Thread to read serial data"""
        self.log_event("Serial reader thread started")

        while self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)

                    for byte_value in data:
                        # Printable characters
                        if 32 <= byte_value <= 126:
                            char = chr(byte_value)

                            with self.buffer_lock:
                                if len(self.input_buffer) < CODE_LENGTH:
                                    self.input_buffer += char
                                    self.log_event(f"Key received: {char} | Buffer: {self.input_buffer}")

                                    if len(self.input_buffer) == CODE_LENGTH:
                                        code = self.input_buffer
                                        self.input_buffer = ""
                                        self.log_event(f"Code complete: {code}")

                                        # Process in main thread
                                        self.root.after(0, lambda c=code: self.process_code(c))

                                elif char == '*':
                                    self.input_buffer = ""
                                    self.log_event("Buffer cleared by '*' key")

                        # Check for CR/LF
                        elif byte_value in (0x0D, 0x0A):
                            if len(self.input_buffer) == CODE_LENGTH:
                                code = self.input_buffer
                                self.input_buffer = ""
                                self.log_event(f"Code complete via CR/LF: {code}")
                                self.root.after(0, lambda c=code: self.process_code(c))
                            else:
                                self.input_buffer = ""
                                self.log_event("Incomplete code, resetting buffer")

                time.sleep(0.01)

            except Exception as e:
                self.log_event(f"Serial error: {e}")
                break

    def start_serial(self):
        """Initialize serial connection"""
        try:
            self.ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0)
            self.log_event(f"Serial port {COM_PORT} opened at {BAUD_RATE} baud")
            self.log_event(
                f"Time Window: {TIME_WINDOW_START.strftime('%I:%M %p')} - {TIME_WINDOW_END.strftime('%I:%M %p')}")
            self.log_event(f"Target code length: {CODE_LENGTH}")
            self.log_event("RESPONSE CODES: '1'=Early, '0'=Late/Invalid, '2'=On Time")
            self.status_var.set("Connected - Waiting for scans...")

            # Start reader thread
            reader_thread = threading.Thread(target=self.serial_reader_thread, daemon=True)
            reader_thread.start()

        except Exception as e:
            self.log_event(f"Failed to open serial port: {e}")
            self.status_var.set("Serial connection failed")


def main():
    root = tk.Tk()
    app = AttendanceTracker(root)

    # Configure treeview tags for colors
    app.tree.tag_configure("ontime", background="#d4edda")  # Green
    app.tree.tag_configure("early", background="#fff3cd")  # Yellow
    app.tree.tag_configure("late", background="#f8d7da")  # Red
    app.tree.tag_configure("noaccess", background="#d1ecf1")  # Blue

    root.mainloop()


if __name__ == "__main__":
    main()