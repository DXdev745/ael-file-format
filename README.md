
Adaptive Environment Log File Format (.ael) Project
## Description

Welcome to the Adaptive Environment Log File Format (`.ael`) project!

This project introduces a novel binary file format designed to capture a continuous, synchronized stream of **environmental sensor data** and **associated human interaction/device state changes** within a specific physical space (e.g., an office, a smart home room).

The unique purpose of the `.ael` format isn't merely to log data, but to enable an AI or adaptive system to **learn and predict human comfort, preference, and behavior patterns** to proactively optimize the environment. It facilitates "environmental fingerprinting" for hyper-personalization and contextual anomaly detection for efficiency and safety.

---

## File Format Specification

The `.ael` file format is structured as a fixed-size header followed by a sequence of variable-length data blocks, each representing a "snapshot" or "event" at a specific timestamp.

### 1. File Header (64 bytes)

The header provides general information about the log file.

| Field | Data Type | Size (Bytes) | Description |
| :--- | :--- | :--- | :--- |
| Magic Number | `char[8]` | 8 | A string of `AEL_LOG\0` |
| Version | `unsigned short` | 2 | The format version (currently `1`) |
| Creation Timestamp | `unsigned long long` | 8 | Unix timestamp (seconds since epoch) when the log file was created |
| Reserved | `char[46]` | 46 | Reserved for future use (fill with `\0`) |

### 2. Data Block Structure (Variable Size)

Following the header, the file contains a series of data blocks. Each block represents a single snapshot of the environment and interactions.

#### Data Block Header (16 bytes)

| Field | Data Type | Size (Bytes) | Description |
| :--- | :--- | :--- | :--- |
| Block Length | `unsigned int` | 4 | Total length of this data block *including* its own header (in bytes) |
| Block Timestamp | `unsigned long long` | 8 | Unix timestamp (milliseconds since epoch) for this specific data snapshot |
| Flags / Event Type | `unsigned short` | 2 | Bitmask for special events (e.g., `0x01` for User Override Light, `0x02` for User Override HVAC, `0x04` for User Override Blinds) |
| Reserved | `unsigned short` | 2 | Reserved for future use (fill with `\0`) |

#### Data Block Content (26 bytes, follows Block Header)

This section stores the actual sensor readings and device states.

| Field | Data Type | Size (Bytes) | Description |
| :--- | :--- | :--- | :--- |
| **Environmental Sensors:** | | | |
| Light Intensity | `float` | 4 | Ambient light in Lux |
| Sound Level | `float` | 4 | Ambient sound in dB |
| Air Temperature | `float` | 4 | Temperature in Celsius |
| Humidity | `float` | 4 | Relative humidity percentage |
| CO2 Level | `unsigned short` | 2 | CO2 in PPM (parts per million) |
| **Device States / Interactions:** | | | |
| Lighting Brightness | `unsigned char` | 1 | 0-100% brightness |
| HVAC Thermostat Setpoint | `float` | 4 | Desired temperature setting |
| HVAC Fan Speed | `unsigned char` | 1 | 0-100% fan speed |
| Blinds Position | `unsigned char` | 1 | 0-100% open |
| User Override Flag | `unsigned char` | 1 | `0`=None, `1`=Light, `2`=HVAC, `4`=Blinds (can be combined) |

---

## Tools

* **`capture_ael_log.py`**: A Python script that simulates capturing environmental sensor data and device states, then packages this information into a `.ael` log file according to the specified format.
* **`view_ael_log.py`**: A Python script that reads an existing `.ael` log file, parses its binary structure, and displays the captured environmental information in a human-readable format.

---

## How to Use

### 0. Prerequisites

Ensure you have Python 3 installed. You'll need the `psutil` library (for potential future expansion with real system data, currently used for dummy data generation). It's highly recommended to use a virtual environment:

```bash
=======
GME File Format Project
Description
Welcome to the Game Manifest Engine (GME) file format project!

This repository contains a simple, custom binary container format designed to archive one or more files into a single .gme file. It's similar in concept to a .zip file but with a custom, simple manifest. This format is ideal for packaging game assets like levels, textures, and audio into a single, easily distributable file.

This version of the GME format now supports zlib compression and AES-256-CBC encryption for enhanced security and efficiency.

File Format Specification
The .gme file format is structured as follows:

1. File Header (46 bytes)
The header is always 46 bytes long and contains core information for the archive, including a unique salt for encryption key derivation.

Field

Data Type

Size (Bytes)

Description

Magic Number

char[8]

8

A string of GME_ARC\0

Version

unsigned short

2

The version number (currently 1)

Number of Files

unsigned int

4

The total number of files in the archive

Manifest Offset

unsigned long long

8

The offset to the manifest (table of contents) from the beginning of the file

File Data Offset

unsigned long long

8

The offset to the actual file data section

Salt

char[16]

16

Unique 16-byte salt for password-based key derivation (PBKDF2HMAC)

2. File Manifest (Variable Size)
This section serves as the table of contents, containing an entry for each file in the archive. Each entry now includes details about its original size, stored size, compression status, encryption status, and a unique Initialization Vector (IV) for encryption.

Field

Data Type

Size (Bytes)

Description

Filename Length

unsigned short

2

The length of the filename string

Filename

char[Filename Length]

Variable

The actual filename (e.g., level_1.bin, player_texture.png)

Original File Size

unsigned long long

8

The size of the file data before compression/encryption

Stored File Size

unsigned long long

8

The size of the file data after compression/encryption (actual size in archive)

Compression Flag

unsigned char

1

0 for no compression, 1 for zlib compression

Encryption Flag

unsigned char

1

0 for no encryption, 1 for AES-256-CBC encryption

IV (Initialization Vector)

char[16]

16

Unique 16-byte IV for AES-CBC encryption of this file's data

File Offset

unsigned long long

8

The offset of the file data from the start of the .gme file

3. File Data (Variable Size)
This section contains the raw binary data of all the archived files, stored consecutively. Their sizes and locations are determined by the manifest entries. Data here will be compressed and/or encrypted if those flags are set in the manifest.

Tools
create_gme_archive.py: A Python script that takes a list of input files and archives them into a single .gme file. It supports optional zlib compression and AES-256-CBC encryption.

read_gme_archive.py: A Python script that reads a .gme archive, extracts its manifest, and reconstructs the original files into a specified output directory. It automatically detects and handles zlib decompression and AES-256-CBC decryption.

How to Use
0. Prerequisites
Ensure you have Python 3 installed. For encryption, you'll need the cryptography library. It's recommended to use a virtual environment:


# Create a virtual environment (if you haven't already)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

D
# Install psutil
pip install psutil
```

### 1. Capture an AEL Log

To create an `environment_log.ael` file with simulated data (e.g., 10 snapshots, every 2 seconds):

```bash
python3 capture_ael_log.py
```

*(You can modify `num_snapshots_to_capture` and `capture_interval_seconds` in the script's `if __name__ == "__main__":` block.)*

### 2. View an AEL Log

To read and display the contents of `environment_log.ael`:

```bash
python3 view_ael_log.py
```
=======
# Install the cryptography library
pip install cryptography

1. Create Sample Files (if needed)
To create some sample text files for archiving:

echo "This is the content of the first file." > file1.txt
echo "This is the content of the second file." > file2.txt
echo "This is the third file, it's a bit longer to show different sizes." > file3.txt

2. Create a GME Archive (with Compression and Encryption)
To create an archive_encrypted_compressed.gme file containing file1.txt, file2.txt, and file3.txt with both compression and encryption enabled:

python3 create_gme_archive.py

(The script will prompt you to enter a password for encryption.)

3. Read and Extract from a GME Archive
To extract the contents of archive_encrypted_compressed.gme into the extracted_files directory:

mkdir -p extracted_files # Create the output directory if it doesn't exist
python3 read_gme_archive.py

(The script will prompt you to enter the password used during encryption.)
7
