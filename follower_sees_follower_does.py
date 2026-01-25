import serial
import time

# --- CONFIGURATION ---
LEADER_PORT = 'COM8'  # Check port
FOLLOWER_PORT = 'COM6'  # Check port
BAUDRATE = 1000000

LEADER_IDS = [7, 8, 9, 10, 11, 12]
FOLLOWER_IDS = [1, 2, 3, 4, 6, 5]

DIRECTIONS = [1, 1, 1, 1, 1, 1]
# --- END CONFIGURATION ---

# --- REGISTERS ---
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42
ADDR_PRESENT_POSITION = 56


def calculate_checksum(packet):
    s = sum(packet[2:])
    return (~s) & 0xFF


def write_byte(ser, servo_id, address, value):
    packet = [0xFF, 0xFF, servo_id, 4, 0x03, address, value]
    packet.append(calculate_checksum(packet))
    ser.write(bytearray(packet))


def read_position_robust(ser, servo_id):
    ser.reset_input_buffer()
    # Fast read: 1 attempt only to keep loop speed high.
    # If missed, we skip this frame (better than lagging).
    packet = [0xFF, 0xFF, servo_id, 4, 0x02, ADDR_PRESENT_POSITION, 2]
    packet.append(calculate_checksum(packet))
    ser.write(bytearray(packet))
    try:
        r = ser.read(8)
        if len(r) == 8 and r[0] == 0xFF:
            val = (r[6] << 8) | r[5]
            return val % 4096  # Normalize for Delta Calculation
    except:
        pass
    return None


def sync_write_positions(ser, ids, targets):
    """
    Sends ONE packet to move ALL motors instantly.
    Structure: [Header, ID=0xFE, Len, Instr=0x83, Addr, DataLen, ID1, P1L, P1H, ID2, P2L, P2H...]
    """
    # 0x83 is SYNC WRITE
    # Data Length per motor = 2 bytes (Position L, Position H)
    data_len = 2

    # Calculate total packet length:
    # (ID + Data) * N_Motors + 4 bytes (Addr + Len)
    total_len = ((1 + data_len) * len(ids)) + 4

    packet = [0xFF, 0xFF, 0xFE, total_len, 0x83, ADDR_GOAL_POSITION, data_len]

    for i in range(len(ids)):
        sid = ids[i]
        pos = int(targets[i])

        # Handle negative/large numbers for Infinite Mode
        if pos < 0: pos += 65536

        pL = pos & 0xFF
        pH = (pos >> 8) & 0xFF

        packet.extend([sid, pL, pH])

    packet.append(calculate_checksum(packet))
    ser.write(bytearray(packet))


try:
    print("Opening High-Speed Ports...")
    l_ser = serial.Serial(LEADER_PORT, BAUDRATE, timeout=0.01)  # Ultra low timeout
    f_ser = serial.Serial(FOLLOWER_PORT, BAUDRATE, timeout=0.01)

    print("\n--- HIGH SPEED SYNC TELEOP ---")

    # 1. Relax
    for sid in LEADER_IDS: write_byte(l_ser, sid, ADDR_TORQUE_ENABLE, 0)
    for sid in FOLLOWER_IDS: write_byte(f_ser, sid, ADDR_TORQUE_ENABLE, 0)

    print("Move to Sync Position. Press ENTER.")
    input()

    # 2. Init
    prev_leader_pos = [0] * 6
    follower_targets = [0] * 6

    print("Locking...")
    # Initial lock must be individual to read positions safely
    for i in range(6):
        lid = LEADER_IDS[i]
        fid = FOLLOWER_IDS[i]

        lp = read_position_robust(l_ser, lid)
        while lp is None: lp = read_position_robust(l_ser, lid)
        prev_leader_pos[i] = lp

        fp = read_position_robust(f_ser, fid)
        while fp is None: fp = read_position_robust(f_ser, fid)
        follower_targets[i] = fp

        write_byte(f_ser, fid, ADDR_TORQUE_ENABLE, 1)  # Lock

    # Send one initial Sync Write to stiffen them all
    sync_write_positions(f_ser, FOLLOWER_IDS, follower_targets)

    print(">> Active. Running Sync Write Mode.")

    while True:
        # Loop Variables
        update_needed = False

        # 1. READ PHASE (Loop through Leader)
        # We still read individually (unless you want to implement Bulk Read later)
        # But we do it fast.
        for i in range(6):
            lid = LEADER_IDS[i]
            curr_l = read_position_robust(l_ser, lid)

            if curr_l is not None:
                # Calculate Delta
                delta = curr_l - prev_leader_pos[i]

                # Wrap-Around Logic
                if delta > 2048:  delta -= 4096
                if delta < -2048: delta += 4096

                if delta != 0:
                    # Update Target
                    prev_leader_pos[i] = curr_l
                    follower_targets[i] += (delta * DIRECTIONS[i])
                    update_needed = True

        # 2. WRITE PHASE (One Packet for All)
        if update_needed:
            sync_write_positions(f_ser, FOLLOWER_IDS, follower_targets)

        # Small delay not needed because read_robust acts as a throttle
        # but a tiny sleep yields CPU to USB driver
        time.sleep(0.002)

except KeyboardInterrupt:
    print("\nStopping...")
    for sid in FOLLOWER_IDS: write_byte(f_ser, sid, ADDR_TORQUE_ENABLE, 0)
    l_ser.close()
    f_ser.close()
