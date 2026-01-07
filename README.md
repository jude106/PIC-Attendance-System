# PIC16F877A Automated Attendance System

## 📌 Project Overview
This project is an automated classroom access and attendance tracking system. It integrates a **PIC16F877A microcontroller** with a **Python-based PC application** to verify student identities in real-time.

Instead of manual sign-ins, students enter a 6-digit code via a keypad. The system cross-references the ID and current timestamp with a database, granting access only if the student is authorized and within the allowed time window.

## 🚀 Key Features
* **Dual-Layer Verification:** Checks both **Student ID** (Security) and **Arrival Time** (Punctuality).
* **Hardware-Software Bridge:** Implements bidirectional **UART Communication** between the microcontroller and PC.
* **Status Feedback:** Real-time feedback via LCD ("Access Granted", "Late", "Denied") and GUI logs.
* **Digital Logging:** Automatically exports attendance records to CSV for administrative use.

## 🛠️ Tech Stack & Hardware

### Software
* **Host Application:** Python (Tkinter for GUI, PySerial for communication).
* **Firmware:** PIC Assembly Language (MPASM).

### Hardware Components
* **Microcontroller:** PIC16F877A.
* **Input:** 4x4 Matrix Keypad (74922 Encoder).
* **Display:** 16x2 LCD.
* **Interface:** PL2303 USB-to-UART Converter.

## ⚙️ How It Works (The Logic)
1. **Input:** User enters a 6-digit code on the Keypad.
2. **Transmission:** PIC sends the code to the PC via UART (9600 Baud).
3. **Verification (Python):** * The app checks the code against a dictionary of valid students.
   * It checks if the current time is within the configured window (e.g., 7:00 PM - 7:05 PM).
4. **Response:** The PC sends a single-byte status code back to the PIC:
   * `'2'` → **On Time** (Access Granted)
   * `'1'` → **Early** (Access Granted)
   * `'0'` → **Late/Invalid** (Access Denied).
5. **Actuation:** The PIC displays the status on the LCD and triggers the door lock (simulated).

## 💻 How to Run

### 1. Hardware Setup
Connect the PL2303 RX/TX pins to the PIC's TX/RX pins (RC6/RC7). Ensure common ground between the PIC and the USB converter.

### 2. Python Setup
```bash
# Clone the repository
git clone [https://github.com/jude106/PIC-Attendance-System.git](https://github.com/YOUR_USERNAME/PIC-Attendance-System.git)

# Install dependencies
pip install -r requirements.txt

# Run the tracker
python src/attendance_gui.py
