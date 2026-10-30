#!/usr/bin/env python3
"""
ESP32 Hardware Bridge for SAHARA-AI
==================================
Connects ESP32 microcontroller connected via USB to SAHARA-AI backend.
Receives telemetry from:
1. Fall Detection Sensor (Accelerometer / mmWave)
2. Smart Pill Box (Lid Opened / Dose Taken)
3. Home Hub Gateway (Heartbeat / Presence)

All hardware events are routed directly to Harshit Thakur (SEN_001).
"""

import sys
import time
import json
import requests
import glob

BACKEND_URL = "http://localhost:8000/api/v1/hardware/event"
TARGET_SENIOR_ID = "SEN_001"
DEFAULT_BAUDRATE = 115200


def send_hardware_event(device_type: str, event_name: str, message: str = ""):
    """Dispatches hardware event to SAHARA-AI backend."""
    payload = {
        "senior_id": TARGET_SENIOR_ID,
        "device_type": device_type,
        "event": event_name,
        "message": message,
        "timestamp": time.time()
    }
    try:
        res = requests.post(BACKEND_URL, json=payload, timeout=3)
        if res.ok:
            data = res.json()
            print(f"✅ [SAHARA-AI] {device_type.upper()} event synced -> {data.get('action_taken')} for {data.get('senior_name')}")
        else:
            print(f"⚠️ [SAHARA-AI] Server returned {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ [SAHARA-AI] Failed to connect to {BACKEND_URL}: {e}")


def find_esp32_port():
    """Auto-detects ESP32 USB serial port on macOS/Linux."""
    patterns = [
        "/dev/cu.usbserial*",
        "/dev/cu.wchusbserial*",
        "/dev/cu.SLAB_USBtoUART*",
        "/dev/cu.usbmodem*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*"
    ]
    for p in patterns:
        ports = glob.glob(p)
        if ports:
            return ports[0]
    return None


def run_serial_listener(port: str, baudrate: int = DEFAULT_BAUDRATE):
    """Listens to USB serial output from ESP32."""
    import serial
    print(f"🔌 Connecting to ESP32 on {port} at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        print(f"🟢 Connected to ESP32! Listening for sensor events...\n")
        
        while True:
            if ser.in_waiting > 0:
                raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw_line:
                    continue
                
                print(f"📥 [ESP32 RAW]: {raw_line}")
                line_lower = raw_line.lower()

                # Check JSON payload format
                if line_lower.startswith("{") and line_lower.endswith("}"):
                    try:
                        parsed = json.loads(raw_line)
                        send_hardware_event(
                            device_type=parsed.get("type", "hub"),
                            event_name=parsed.get("event", "status"),
                            message=parsed.get("msg", raw_line)
                        )
                        continue
                    except:
                        pass

                # Check string keyword triggers
                if "fall" in line_lower:
                    send_hardware_event("fall", "fall_detected", raw_line)
                elif "pill" in line_lower or "open" in line_lower or "dose" in line_lower:
                    send_hardware_event("pillbox", "lid_opened", raw_line)
                elif "hub" in line_lower or "alive" in line_lower or "heartbeat" in line_lower:
                    send_hardware_event("hub", "heartbeat", raw_line)

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopping ESP32 serial bridge.")
    except Exception as e:
        print(f"❌ Serial error: {e}")


def run_interactive_simulator():
    """Keyboard simulator for instant hardware testing without physical cable."""
    print("=" * 60)
    print("🕹️ SAHARA-AI ESP32 Hardware Simulator (Harshit Thakur - SEN_001)")
    print("=" * 60)
    print("Press a number to trigger live telemetry on the website:")
    print(" [1] 🚨 Fall Detection Sensor (Sudden Acute Fall Detected)")
    print(" [2] 💊 Smart Pill Box (Lid Opened -> Dose Verified Taken)")
    print(" [3] 🏠 Home Hub Gateway (Heartbeat & Status ONLINE)")
    print(" [q] Exit")
    print("=" * 60)

    while True:
        try:
            choice = input("\nEnter choice (1/2/3/q): ").strip().lower()
            if choice == "1":
                print("💥 Sending ESP32 Fall Sensor Trigger...")
                send_hardware_event("fall", "fall_detected", "ESP32 Accelerometer Peak Acceleration > 3.2G")
            elif choice == "2":
                print("💊 Sending Smart Pill Box Open Trigger...")
                send_hardware_event("pillbox", "lid_opened", "ESP32 Magnetic Reed Switch Open")
            elif choice == "3":
                print("🏠 Sending Home Hub Heartbeat...")
                send_hardware_event("hub", "heartbeat", "ESP32 WiFi Gateway Ping")
            elif choice == "q":
                break
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sim":
        run_interactive_simulator()
    else:
        detected_port = find_esp32_port()
        if detected_port:
            run_serial_listener(detected_port)
        else:
            print("⚠️ No ESP32 USB serial port detected on laptop.")
            print("Starting interactive hardware simulator mode (Press 1/2/3 to test)...\n")
            run_interactive_simulator()
