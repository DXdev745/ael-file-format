<h1>Adaptive Environment Log File Format (.ael) Project</h1>
<p>Welcome to the Adaptive Environment Log File Format (.ael) project!</p>

This project introduces a novel binary file format designed to capture a continuous, synchronized stream of environmental sensor data and associated human interaction/device state changes within a specific physical space (e.g., an office, a smart home room).

The unique purpose of the .ael format isn't merely to log data, but to enable an AI or adaptive system to learn and predict human comfort, preference, and behavior patterns to proactively optimize the environment. It facilitates "environmental fingerprinting" for hyper-personalization and contextual anomaly detection for efficiency and safety.

File Format Specification
The .ael file format is structured as a fixed-size header followed by a sequence of variable-length data blocks, each representing a "snapshot" or "event" at a specific timestamp.

1. File Header (64 bytes)
The header provides general information about the log file.
<pre>
<code>
Field

Data Type

Size (Bytes)

Description

Magic Number

char[8]

8
</code>
</pre>
<pre>
<code>
A string of AEL_LOG\0

Version

unsigned short

2

The format version (currently 1)

Creation Timestamp

unsigned long long

8

Unix timestamp (seconds since epoch) when the log file was created

Reserved

char[46]

46

Reserved for future use (fill with \0)

2. Data Block Structure (Variable Size)
Following the header, the file contains a series of data blocks. Each block represents a single snapshot of the environment and interactions.

Data Block Header (16 bytes)
Field

Data Type

Size (Bytes)

Description

Block Length

unsigned int

4

Total length of this data block including its own header (in bytes)

Block Timestamp

unsigned long long

8

Unix timestamp (milliseconds since epoch) for this specific data snapshot

Flags / Event Type

unsigned short

2

Bitmask for special events (e.g., 0x01 for User Override Light, 0x02 for User Override HVAC, 0x04 for User Override Blinds)

Reserved

unsigned short

2

Reserved for future use (fill with \0)

Data Block Content (26 bytes, follows Block Header)
This section stores the actual sensor readings and device states.

Field

Data Type

Size (Bytes)

Description

Environmental Sensors:







Light Intensity

float

4

Ambient light in Lux

Sound Level

float

4

Ambient sound in dB

Air Temperature

float

4

Temperature in Celsius

Humidity

float

4

Relative humidity percentage

CO2 Level

unsigned short

2

CO2 in PPM (parts per million)

Device States / Interactions:







Lighting Brightness

unsigned char

1

0-100% brightness

HVAC Thermostat Setpoint

float

4

Desired temperature setting

HVAC Fan Speed

unsigned char

1

0-100% fan speed

Blinds Position

unsigned char

1

0-100% open

User Override Flag

unsigned char

1

0=None, 1=Light, 2=HVAC, 4=Blinds (can be combined)
</code>
</pre>

Tools
capture_ael_log.py: A Python script that simulates capturing environmental sensor data and device states, then packages this information into a .ael log file according to the specified format.

view_ael_log.py: A Python script that reads an existing .ael log file, parses its binary structure, and displays the captured environmental information in a human-readable format.

How to Use
0. Prerequisites
Ensure you have Python 3 installed. You'll need the psutil library (for potential future expansion with real system data, currently used for dummy data generation). It's highly recommended to use a virtual environment:
<pre>
<code>
# Create a virtual environment (if you haven't already)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install psutil
pip install psutil
</code>
</pre>



1. Capture an AEL Log
To create an environment_log.ael file with simulated data (e.g., 10 snapshots, every 2 seconds):

python3 capture_ael_log.py



(You can modify num_snapshots_to_capture and capture_interval_seconds in the script's if __name__ == "__main__": block.)

2. View an AEL Log
To read and display the contents of environment_log.ael:

python3 view_ael_log.py
