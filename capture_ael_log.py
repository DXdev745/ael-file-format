import struct
import os
import time
import random # For generating dummy sensor data

# --- AEL File Format Constants (from specification) ---
AEL_MAGIC_NUMBER = b'AEL_LOG\0'
AEL_VERSION = 1

# Header size
AEL_HEADER_SIZE = 64

# Data Block Header size
AEL_DATA_BLOCK_HEADER_SIZE = 16

# Fixed size of the Data Block Content
# 4 (Light) + 4 (Sound) + 4 (Temp) + 4 (Humidity) + 2 (CO2) +
# 1 (Light Brightness) + 4 (HVAC Setpoint) + 1 (HVAC Fan Speed) + 1 (Blinds) + 1 (User Override)
AEL_DATA_BLOCK_CONTENT_SIZE = 4 + 4 + 4 + 4 + 2 + 1 + 4 + 1 + 1 + 1 # = 26 bytes

# Total size of a fixed-size data block (Header + Content)
AEL_FIXED_DATA_BLOCK_TOTAL_SIZE = AEL_DATA_BLOCK_HEADER_SIZE + AEL_DATA_BLOCK_CONTENT_SIZE

# User Override Flags (can be combined using bitwise OR)
USER_OVERRIDE_NONE = 0x00
USER_OVERRIDE_LIGHT = 0x01
USER_OVERRIDE_HVAC = 0x02
USER_OVERRIDE_BLINDS = 0x04
# Add more as needed


def generate_dummy_sensor_data(last_data=None):
    """Generates realistic-looking dummy sensor and device state data."""
    if last_data is None:
        last_data = {
            'light': 300.0, 'sound': 50.0, 'temp': 22.0, 'humidity': 50.0, 'co2': 400,
            'light_brightness': 50, 'hvac_setpoint': 22.0, 'hvac_fan_speed': 50,
            'blinds_position': 50, 'user_override': USER_OVERRIDE_NONE
        }

    # Simulate slight fluctuations for sensor data
    light = max(0.0, last_data['light'] + random.uniform(-10.0, 10.0))
    sound = max(30.0, min(90.0, last_data['sound'] + random.uniform(-1.0, 1.0)))
    temp = max(18.0, min(30.0, last_data['temp'] + random.uniform(-0.5, 0.5)))
    humidity = max(30.0, min(80.0, last_data['humidity'] + random.uniform(-1.0, 1.0)))
    co2 = max(350, min(1500, last_data['co2'] + random.randint(-5, 5)))

    # Simulate device states (can be random or follow a pattern)
    light_brightness = last_data['light_brightness'] # For now, keep constant unless overridden
    hvac_setpoint = last_data['hvac_setpoint']
    hvac_fan_speed = last_data['hvac_fan_speed']
    blinds_position = last_data['blinds_position']
    user_override = USER_OVERRIDE_NONE

    # Introduce random user overrides occasionally
    if random.random() < 0.05: # 5% chance of an override
        override_type = random.choice([USER_OVERRIDE_LIGHT, USER_OVERRIDE_HVAC, USER_OVERRIDE_BLINDS])
        user_override |= override_type # Add to flags

        if USER_OVERRIDE_LIGHT & override_type:
            light_brightness = random.randint(0, 100)
            print(f"  Simulating user override: Light to {light_brightness}%")
        if USER_OVERRIDE_HVAC & override_type:
            hvac_setpoint = round(random.uniform(20.0, 25.0), 1)
            print(f"  Simulating user override: HVAC setpoint to {hvac_setpoint}°C")
        if USER_OVERRIDE_BLINDS & override_type:
            blinds_position = random.randint(0, 100)
            print(f"  Simulating user override: Blinds to {blinds_position}% open")

    return {
        'light': light, 'sound': sound, 'temp': temp, 'humidity': humidity, 'co2': co2,
        'light_brightness': light_brightness, 'hvac_setpoint': hvac_setpoint,
        'hvac_fan_speed': hvac_fan_speed, 'blinds_position': blinds_position,
        'user_override': user_override
    }


def capture_ael_log(output_filename, num_snapshots=10, interval_seconds=1):
    """
    Captures simulated environmental data and writes it to an AEL log file.
    """
    print(f"Creating AEL log: {output_filename}")
    print(f"Capturing {num_snapshots} snapshots with {interval_seconds}-second interval...")

    # --- 1. Prepare Header Data ---
    creation_timestamp = int(time.time()) # Unix timestamp in seconds

    # --- 2. Open File and Write Header ---
    with open(output_filename, 'wb') as f:
        header_data = struct.pack(
            '<8s H Q 46s', # Magic (8s), Version (H), Creation Timestamp (Q), Reserved (46s)
            AEL_MAGIC_NUMBER,
            AEL_VERSION,
            creation_timestamp,
            b'\0' * 46 # Fill reserved bytes with nulls
        )
        f.write(header_data)

        # --- 3. Capture and Write Data Blocks ---
        last_data = None
        for i in range(num_snapshots):
            current_time_ms = int(time.time() * 1000) # Unix timestamp in milliseconds

            # Generate dummy data
            current_data = generate_dummy_sensor_data(last_data)
            last_data = current_data # Update last_data for next iteration's fluctuations

            # Pack Data Block Content
            content_data = struct.pack(
                '<f f f f H B f B B B', # Float (f), Unsigned Short (H), Unsigned Char (B)
                current_data['light'],
                current_data['sound'],
                current_data['temp'],
                current_data['humidity'],
                current_data['co2'],
                current_data['light_brightness'],
                current_data['hvac_setpoint'],
                current_data['hvac_fan_speed'],
                current_data['blinds_position'],
                current_data['user_override']
            )

            # Pack Data Block Header
            # Block Length = Header Size + Content Size
            block_length = AEL_DATA_BLOCK_HEADER_SIZE + len(content_data)
            block_header_data = struct.pack(
                '<I Q H H', # Block Length (I), Block Timestamp (Q), Flags (H), Reserved (H)
                block_length,
                current_time_ms,
                current_data['user_override'], # Using user_override as the flag for now
                0x0000 # Reserved
            )

            # Write Block Header and Content
            f.write(block_header_data)
            f.write(content_data)

            print(f"  Snapshot {i+1}/{num_snapshots} captured at {time.ctime(current_time_ms / 1000.0)}")
            time.sleep(interval_seconds) # Wait for the next snapshot

    print(f"Successfully created '{output_filename}' with {num_snapshots} snapshots.")


# --- Main Execution Block ---
if __name__ == "__main__":
    output_ael_file = "environment_log.ael"
    num_snapshots_to_capture = 10 # Capture 10 snapshots
    capture_interval_seconds = 2 # Every 2 seconds

    capture_ael_log(output_ael_file, num_snapshots_to_capture, capture_interval_seconds)
