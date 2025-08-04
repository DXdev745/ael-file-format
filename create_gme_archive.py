import struct
import os
import zlib
from getpass import getpass # For securely getting password input

# For encryption
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding # For PKCS7 padding


def derive_key(password, salt, iterations=100000):
    """Derives a 32-byte (256-bit) AES key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32, # AES-256 key length
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_data(key, data):
    """Encrypts data using AES-256 in CBC mode."""
    iv = os.urandom(16) # AES block size is 16 bytes (128 bits)

    # Pad the data to be a multiple of the block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    return iv, encrypted_data


def create_gme_archive(input_files, output_filename, compress_files=True, encrypt_files=False, password=None):
    """
    Creates a GME archive from a list of files, with optional zlib compression and AES-256 encryption.
    """
    print(f"Creating GME archive: {output_filename}")
    print(f"Compression enabled: {compress_files}")
    print(f"Encryption enabled: {encrypt_files}")

    encryption_salt = None
    encryption_key = None
    if encrypt_files:
        if password is None:
            print("Error: Password is required for encryption.")
            return
        encryption_salt = os.urandom(16) # Generate a unique salt for this archive
        encryption_key = derive_key(password, encryption_salt)
        print("Encryption key derived.")
    else:
        # If no encryption, still need a placeholder salt in header to maintain size
        encryption_salt = b'\0' * 16 

    # We need to gather all the file data first to calculate offsets
    files_info = []
    for filename in input_files:
        try:
            with open(filename, 'rb') as f:
                original_data = f.read()
                original_size = len(original_data)

                processed_data = original_data # Data after optional compression
                compression_flag = 0 # 0 = no compression

                if compress_files:
                    compressed_data = zlib.compress(original_data)
                    if len(compressed_data) < original_size: # Only use compressed if smaller
                        processed_data = compressed_data
                        compression_flag = 1
                        print(f"  '{filename}': Compressed by {original_size - len(compressed_data)} bytes.")
                    else:
                        print(f"  '{filename}': Compression did not reduce size. Storing uncompressed.")

                encrypted_data = processed_data # Data after optional encryption
                encryption_flag = 0 # 0 = no encryption
                iv = b'\0' * 16 # Placeholder IV if not encrypted

                if encrypt_files:
                    iv, encrypted_data = encrypt_data(encryption_key, processed_data)
                    encryption_flag = 1
                    print(f"  '{filename}': Encrypted.")

                files_info.append({
                    "filename": filename,
                    "original_size": original_size,
                    "stored_size": len(encrypted_data), # This is the size actually written to file
                    "compression_flag": compression_flag,
                    "encryption_flag": encryption_flag,
                    "iv": iv,
                    "data_to_write": encrypted_data # This is the final data (compressed and/or encrypted)
                })
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found. Skipping.")
            return

    # Calculate offsets
    num_files = len(files_info)
    header_size = 46 # Header is now 46 bytes (30 + 16 for salt)
    manifest_offset = header_size
    file_data_offset = manifest_offset

    # The manifest size depends on the number of files and filename lengths
    # Each manifest entry (excluding filename) is now 44 bytes:
    # 2 (filename_len) + 8 (orig_size) + 8 (stored_size) + 1 (comp_flag) + 1 (enc_flag) + 16 (IV) + 8 (file_offset) = 44 bytes
    for file_entry in files_info:
        filename_bytes = file_entry["filename"].encode('utf-8')
        file_data_offset += 2 + len(filename_bytes) + 8 + 8 + 1 + 1 + 16 + 8 # Add 44 bytes for metadata + filename length

    # Open the output file for writing in binary mode
    with open(output_filename, 'wb') as f:
        # --- Write Header (46 bytes) ---
        magic_number = b'GME_ARC\0'
        version = 1
        header_data = struct.pack('<8s H I Q Q 16s', magic_number, version, num_files, manifest_offset, file_data_offset, encryption_salt)
        f.write(header_data)

        # --- Write Manifest ---
        current_file_data_offset = file_data_offset
        for file_entry in files_info:
            filename_bytes = file_entry["filename"].encode('utf-8')
            filename_len = len(filename_bytes)

            # Write filename length and the filename itself
            f.write(struct.pack('<H', filename_len))
            f.write(filename_bytes)

            # Write original size, stored size, compression flag, encryption flag, IV, and file offset
            manifest_entry_data = struct.pack(
                '<Q Q B B 16s Q', # Q=unsigned long long (8 bytes), B=unsigned char (1 byte), 16s=16-byte string (for IV)
                file_entry["original_size"],
                file_entry["stored_size"],
                file_entry["compression_flag"],
                file_entry["encryption_flag"],
                file_entry["iv"],
                current_file_data_offset
            )
            f.write(manifest_entry_data)

            # Update the offset for the next file's data
            current_file_data_offset += file_entry["stored_size"]

        # --- Write File Data (compressed and/or encrypted) ---
        for file_entry in files_info:
            f.write(file_entry["data_to_write"])

    print(f"Successfully created '{output_filename}' containing {num_files} files.")


# --- MAIN EXECUTION ---
# Define the input and output filenames
input_files_list = ["file1.txt", "file2.txt", "file3.txt"]
output_filename = "archive_encrypted_compressed.gme" # New name to differentiate

# Prompt for password if encryption is enabled
user_password = None
if True: # Set to True to enable encryption for this run
    user_password = getpass("Enter a password for encryption (will not be displayed): ")
    if not user_password:
        print("No password entered. Encryption will be skipped.")
        # If no password, force encrypt_files to False
        create_gme_archive(input_files_list, "archive_unencrypted_compressed.gme", compress_files=True, encrypt_files=False)
    else:
        create_gme_archive(input_files_list, output_filename, compress_files=True, encrypt_files=True, password=user_password)
else:
    # Example of creating an unencrypted archive (for testing)
    create_gme_archive(input_files_list, "archive_unencrypted_compressed.gme", compress_files=True, encrypt_files=False)
