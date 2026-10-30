#!/usr/bin/env python3
"""
SAHARA-AI Multi-ESP32 Hardware Bridge
====================================
Direct integration for:
1. Fall Detection Pendant (ADXL345 + SOS GPIO 26 + OK GPIO 27)
2. Home Hub & Motion System (Bathroom PIR 32 + Kitchen PIR 33 + Door Sensor 19)
3. Smart Pill Box (Reed Switch Pin 27 + Buzzer 26 + LED 25)

Automatically detects any ESP32 connected via USB, reads Serial lines,
and immediately syncs live telemetry into Harshit Thakur's (SEN_001) dashboard.
"""

import sys
import time
import glob
import threading
import requests

BACKEND_URL = "http://localhost:8000/api/v1/hardware/event"
TARGET_SENIOR_ID = "SEN_001"
DEFAULT_BAUDRATE = 115200


def send_hardware_event(event_name: str, message: str = ""):
    """Dispatches parsed hardware event to SAHARA-AI backend."""
    payload = {
        "senior_id": TARGET_SENIOR_ID,
        "event": event_name,
        "message": message,
        "timestamp": time.time()
    }
    try:
        res = requests.post(BACKEND_URL, json=payload, timeout=2.5)
        if res.ok:
            data = res.json()
            action = data.get("action") or data.get("action_taken") or data.get("status")
            print(f"  ⚡ [SAHARA-AI SYNC] Event: {event_name:<16} -> Action: {action} ({data.get('time', '')})")
        else:
            print(f"  ⚠️ [SAHARA-AI] Server returned {res.status_code}: {res.text}")
    except Exception as e:
        print(f"  ❌ [SAHARA-AI] Failed to connect to backend: {e}")


def parse_serial_line(line: str, port_name: str):
    """Matches the exact Serial.println() statements from user's Arduino code."""
    line = line.strip()
    if not line:
        return

    # 1. SMART PILL BOX
    if "BOX OPENED!" in line:
        print(f"\n💊 [SMART PILL BOX] Lid Opened! (Dose Taken)")
        send_hardware_event("BOX_OPENED", line)
    elif "BOX CLOSED!" in line:
        print(f"\n💊 [SMART PILL BOX] Lid Closed.")
        send_hardware_event("BOX_CLOSED", line)

    # 2. FALL DETECTION PENDANT
    elif "MANUAL SOS" in line or "MANUAL_SOS" in line:
        print(f"\n🚨 [PENDANT] !!! MANUAL SOS EMERGENCY BUTTON ACTIVATED !!!")
        send_hardware_event("MANUAL_SOS", line)
    elif "USER CONFIRMED SAFE" in line or "USER_OK" in line or "Fall alert cancelled" in line:
        print(f"\n✅ [PENDANT] Senior pressed 'I AM OK' button. Fall dismissed.")
        send_hardware_event("USER_OK", line)
    elif "POSSIBLE FALL" in line or "POSSIBLE_FALL" in line:
        print(f"\n⚠️ [PENDANT] Possible Fall detected! 30-second confirmation started...")
        send_hardware_event("POSSIBLE_FALL", line)
    elif "NO RESPONSE" in line or "NO_RESPONSE" in line:
        print(f"\n🚨 [PENDANT] !!! NO RESPONSE FOR 30s -> ACUTE FALL ALARM DISPATCHED !!!")
        send_hardware_event("NO_RESPONSE", line)

    # 3. HOME MOTION DETECTION & DOOR
    elif "MAIN DOOR: OPENED!" in line or "Main Door: OPEN" in line:
        print(f"\n🚪 [HOME HUB] Main Front Door OPENED!")
        send_hardware_event("DOOR_OPEN", line)
    elif "MAIN DOOR: CLOSED!" in line or "Main Door: CLOSED" in line:
        print(f"\n🚪 [HOME HUB] Main Front Door CLOSED.")
        send_hardware_event("DOOR_CLOSED", line)
    elif "BATHROOM: MOTION DETECTED!" in line:
        print(f"🚿 [HOME HUB] Bathroom Motion Detected!")
        send_hardware_event("BATHROOM_DETECTED", line)
    elif "BATHROOM: MOTION STOPPED" in line:
        send_hardware_event("BATHROOM_STOPPED", line)
    elif "KITCHEN: MOTION DETECTED!" in line:
        print(f"🍳 [HOME HUB] Kitchen Motion Detected!")
        send_hardware_event("KITCHEN_DETECTED", line)
    elif "KITCHEN: MOTION STOPPED" in line:
        send_hardware_event("KITCHEN_STOPPED", line)
    elif "FALL DETECTION PENDANT READY" in line or "HOME MOTION DETECTION SYSTEM" in line or "SMART PILL BOX STARTED" in line:
        print(f"🟢 [HARDWARE INITIALIZED] {line}")
        send_hardware_event("HEARTBEAT", line)


def port_listener_worker(port: str, baudrate: int = DEFAULT_BAUDRATE):
    """Worker thread listening to a single USB serial port."""
    import serial
    print(f"🔌 [PORT {port}] Connecting at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(1.5)
        print(f"🟢 [PORT {port}] Connected and active! Streaming telemetry...\n")
        
        while True:
            if ser.in_waiting > 0:
                raw_bytes = ser.readline()
                try:
                    line = raw_bytes.decode("utf-8", errors="ignore").strip()
                    if line:
                        parse_serial_line(line, port)
                except Exception:
                    pass
            time.sleep(0.01)
    except Exception as e:
        print(f"⚠️ [PORT {port}] Disconnected or error: {e}")


def get_all_usb_ports():
    """Finds all connected ESP32 / Arduino serial ports on macOS."""
    patterns = [
        "/dev/cu.usbserial*",
        "/dev/cu.wchusbserial*",
        "/dev/cu.SLAB_USBtoUART*",
        "/dev/cu.usbmodem*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*"
    ]
    found = []
    for p in patterns:
        found.extend(glob.glob(p))
    return sorted(list(set(found)))


def run_interactive_simulator():
    """Interactive testing tool allowing user/judges to trigger exact hardware events on demand."""
    print("\n" + "=" * 70)
    print("🕹️  SAHARA-AI ESP32 HARDWARE CONTROLLER (Harshit Thakur - SEN_001)")
    print("=" * 70)
    print("Directly trigger your 3 hardware devices into the website live:")
    print("  [1] 💊 Smart Pill Box: BOX OPENED (Dose Verified Taken)")
    print("  [2] 💊 Smart Pill Box: BOX CLOSED")
    print("  [3] 🚨 Fall Pendant: MANUAL SOS Button Pressed (Critical Alert)")
    print("  [4] ⚠️ Fall Pendant: POSSIBLE FALL Detected (30s Timer)")
    print("  [5] 🚨 Fall Pendant: NO RESPONSE After 30s (Urgent Dispatch)")
    print("  [6] ✅ Fall Pendant: USER CONFIRMED SAFE (OK Button)")
    print("  [7] 🚪 Home Hub: MAIN DOOR OPENED")
    print("  [8] 🚪 Home Hub: MAIN DOOR CLOSED")
    print("  [9] 🚿 Home Hub: BATHROOM MOTION DETECTED")
    print("  [0] 🍳 Home Hub: KITCHEN MOTION DETECTED")
    print("  [q] Quit")
    print("=" * 70)

    while True:
        try:
            choice = input("\n👉 Press (0-9/q): ").strip().lower()
            if choice == "1":
                parse_serial_line("BOX OPENED!", "SIM")
            elif choice == "2":
                parse_serial_line("BOX CLOSED!", "SIM")
            elif choice == "3":
                parse_serial_line("!!! MANUAL SOS ACTIVATED !!!", "SIM")
            elif choice == "4":
                parse_serial_line("!!! POSSIBLE FALL DETECTED !!!", "SIM")
            elif choice == "5":
                parse_serial_line("!!! NO RESPONSE FROM USER !!!", "SIM")
            elif choice == "6":
                parse_serial_line("USER CONFIRMED SAFE", "SIM")
            elif choice == "7":
                parse_serial_line("MAIN DOOR: OPENED!", "SIM")
            elif choice == "8":
                parse_serial_line("MAIN DOOR: CLOSED!", "SIM")
            elif choice == "9":
                parse_serial_line("BATHROOM: MOTION DETECTED!", "SIM")
            elif choice == "0":
                parse_serial_line("KITCHEN: MOTION DETECTED!", "SIM")
            elif choice == "q":
                break
        except (KeyboardInterrupt, EOFError):
            break


def main():
    print("=" * 70)
    print("🛰️  SAHARA-AI ESP32 REAL-TIME HARDWARE BRIDGE")
    print("=" * 70)
    
    ports = get_all_usb_ports()
    if ports:
        print(f"🔍 Found {len(ports)} connected USB device(s): {', '.join(ports)}")
        for port in ports:
            t = threading.Thread(target=port_listener_worker, args=(port,), daemon=True)
            t.start()
        print("\nAll USB listeners running in background.")
        print("You can also use the menu below to trigger events manually:\n")
        run_interactive_simulator()
    else:
        print("⚠️ No USB ESP32 detected on your Mac ports right now.")
        print("Plugging in your ESP32 USB cable will stream automatically.")
        print("In the meantime, you can test all 3 devices via this live menu:\n")
        run_interactive_simulator()


if __name__ == "__main__":
    main()
