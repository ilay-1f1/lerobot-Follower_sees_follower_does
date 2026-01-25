import serial
import time
import sys

# --- CONFIGURATION ---
SERIAL_PORT = 'COM8'
BAUD_RATE = 1000000
SERVO_ID = 1
try:
  NEW_ID = int(sys.argv[1])
except:
  sys.exit("Invalid input of new ID.")


# ---------------------

def send_write(ser, id, addr, val):
    checksum = (~(id + 4 + 0x03 + addr + val)) & 0xFF
    packet = [0xFF, 0xFF, id, 4, 0x03, addr, val, checksum]
    ser.write(bytes(packet))
    time.sleep(0.05)


try:
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5) as ser:
        print(f"--- 'DOUBLE LOCK' REPAIR ATTEMPT (ID {SERVO_ID}) ---")

        # 1. UNLOCK EVERYTHING (48 AND 55)
        print("1. Unlocking (Addr 48 & 55)...")
        send_write(ser, SERVO_ID, 48, 0)  # STS Standard
        send_write(ser, SERVO_ID, 55, 0)  # SCS Standard

        # 2. DISABLE TORQUE
        print("2. Disabling Torque...")
        send_write(ser, SERVO_ID, 40, 0)

        # 3. WRITE VOLTAGE LIMIT (4.5V)
        print("3. Writing Voltage Limit 4.5V...")
        send_write(ser, SERVO_ID, 11, 45)

        #4. WRITE ID (Just in case, let's do it now too)
        print(f"4. Writing Target ID {NEW_ID}")
        send_write(ser, SERVO_ID, 5, NEW_ID)

        # 5. LOCK EVERYTHING (The "Burn")
        print("5. LOCKING... (Do not unplug!)")

        # Try locking ID 1 (Old) and ID 2 (New) just to be sure
        for target in [1, 2]:
            send_write(ser, target, 48, 1)  # Lock STS
            time.sleep(0.1)
            send_write(ser, target, 55, 1)  # Lock SCS
            time.sleep(0.1)

        # 6. WAIT EXTRA LONG
        print("   Waiting for flash write cycle...")
        time.sleep(1.0)

        print("Done. Unplug and pray.")

except Exception as e:
    print(f"Error: {e}")
