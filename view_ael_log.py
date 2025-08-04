import struct
import os
import time

# --- AEL File Format Constants (from specification) ---
AEL_MAGIC_NUMBER = b'AEL_LOG\0'
AEL_VERSION = 1

# Header size
AEL_HEADER_SIZE = 64

# Data Block Header size
AEL_DATA_BLOCK_HEADER_SIZE = 16

# Fixed size of the Data Block Content
AEL_DATA_BLOCK_CONTENT_SIZE = 4 + 4 + 4 + 4 + 2 + 1 + 4 + 1 + 1 + 1 # = 26 bytes

# Total size of a fixed-size data block (Header + Content)
AEL_FIXED_DATA_BLOCK_TOTAL_SIZE = AEL_DATA_BLOCK_HEADER_SIZE + AEL_DATA_BLOCK_CONTENT_SIZE

# User Override Flags (must match encoder)
USER_OVERRIDE_NONE = 0x00
USER_OVERRIDE_LIGHT = 0x01
USER_OVERRIDE_HVAC = 0x02
USER_OVERRIDE_BLINDS = 0x04

def parse_user_override_flags(flags):
    """Converts the integer flags into a human-readable list of overrides."""
    overrides = []
    if flags & USER_OVERRIDE_LIGHT:
        overrides.append("Light")
    if flags & USER_OVERRIDE_HVAC:
        overrides.append("HVAC")
    if flags & USER_OVERRIDE_BLINDS:
        overrides.append("Blinds")

    if not overrides:
        return "None"
    return ", ".join(overrides)


def view_ael_log(input_filename):
    """
    Reads and displays the contents of an AEL log file.
    """
    print(f"Reading AEL log: {input_filename}")

    if not os.path.exists(input_filename):
        print(f"Error: AEL log file '{input_filename}' not found.")
        return

    with open(input_filename, 'rb') as f:
        # --- 1. Read File Header ---
        header_data = f.read(AEL_HEADER_SIZE)
        if len(header_data) < AEL_HEADER_SIZE:
            print("Error: Incomplete file header.")
            return

        magic_number, version, creation_timestamp, reserved_header = \
            struct.unpack('<8s H Q 46s', header_data)

        if magic_number != AEL_MAGIC_NUMBER:
            print(f"Error: Invalid magic number. Expected '{AEL_MAGIC_NUMBER.decode()}', got '{magic_number.decode().strip()}'")
            return
        if version != AEL_VERSION:
            print(f"Warning: File version mismatch. Expected {AEL_VERSION}, got {version}.")

        print("\n--- AEL Log Header ---")
        print(f"Magic Number: {magic_number.decode().strip()}")
        print(f"Version: {version}")
        print(f"Creation Time: {time.ctime(creation_timestamp)}")
        print("-" * 30)

        # --- 2. Read Data Blocks ---
        snapshot_count = 0
        while True:
            block_header_data = f.read(AEL_DATA_BLOCK_HEADER_SIZE)
            if not block_header_data: # End of file
                break
            if len(block_header_data) < AEL_DATA_BLOCK_HEADER_SIZE:
                print("Warning: Incomplete data block header at end of file. Stopping.")
                break

            block_length, block_timestamp_ms, flags, reserved_block = \
                struct.unpack('<I Q H H', block_header_data)

            # Read Data Block Content
            content_data_size = block_length - AEL_DATA_BLOCK_HEADER_SIZE
            if content_data_size != AEL_DATA_BLOCK_CONTENT_SIZE:
                print(f"Error: Mismatched content size. Expected {AEL_DATA_BLOCK_CONTENT_SIZE}, got {content_data_size}. Data might be corrupt. Stopping.")
                break

            content_data = f.read(content_data_size)
            if len(content_data) < content_data_size:
                print("Warning: Incomplete data block content at end of file. Stopping.")
                break

            # Unpack Data Block Content
            light, sound, temp, humidity, co2, \
            light_brightness, hvac_setpoint, hvac_fan_speed, blinds_position, user_override_flags = \
                struct.unpack('<f f f f H B f B B B', content_data)

            snapshot_count += 1
            print(f"\n--- Snapshot {snapshot_count} ---")
            print(f"Timestamp: {time.ctime(block_timestamp_ms / 1000.0)}")
            print(f"  Light: {light:.2f} Lux")
            print(f"  Sound: {sound:.2f} dB")
            print(f"  Temp: {temp:.2f} °C")
            print(f"  Humidity: {humidity:.2f} %")
            print(f"  CO2: {co2} PPM")
            print(f"  Light Brightness: {light_brightness}%")
            print(f"  HVAC Setpoint: {hvac_setpoint:.1f} °C")
            print(f"  HVAC Fan Speed: {hvac_fan_speed}%")
            print(f"  Blinds Position: {blinds_position}% open")
            print(f"  User Override: {parse_user_override_flags(user_override_flags)}")

        print(f"\nSuccessfully read {snapshot_count} snapshots from '{input_filename}'.")


# --- Main Execution Block ---
if __name__ == "__main__":
    input_ael_file = "environment_log.ael"
    view_ael_log(input_ael_file)
