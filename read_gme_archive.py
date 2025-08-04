import struct
import os
import zlib
from getpass import getpass # For securely getting password input

# For encryption
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding # For PKCS7 unpadding


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

def decrypt_data(key, iv, encrypted_data, original_size):
    """Decrypts data using AES-256 in CBC mode."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad the data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    unpadded_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    
    # Verify unpadded size against original_size (optional but good practice)
    # This check is more about ensuring we don't return too much data if unpadding
    # resulted in more than the original_size due to block alignment.
    # The actual original_size from the manifest is the authoritative size.
    if len(unpadded_data) < original_size:
        # This case is unlikely if decryption and unpadding are correct,
        # unless original_size was misreported or data is corrupt.
        pass 
    
    return unpadded_data[:original_size] # Truncate to original size if unpadding was too aggressive


def read_gme_archive(archive_filename, output_folder, password=None):
    """
    Reads a GME archive and extracts its contents to a folder, handling zlib compression and AES-256 encryption.
    """
    print(f"Reading GME archive: {archive_filename}")

    if not os.path.exists(output_folder):
        print(f"Error: Output folder '{output_folder}' does not exist.")
        # Attempt to create the folder if it doesn't exist
        try:
            os.makedirs(output_folder)
            print(f"Created output folder: '{output_folder}'")
        except OSError as e:
            print(f"Error creating output folder '{output_folder}': {e}")
            return


    with open(archive_filename, 'rb') as f:
        # --- Read Header (46 bytes) ---
        header_data = f.read(46) # Header is now 46 bytes
        magic_number, version, num_files, manifest_offset, file_data_offset, encryption_salt = \
            struct.unpack('<8s H I Q Q 16s', header_data)

        # Check if this is a valid GME file
        if magic_number != b'GME_ARC\0':
            print(f"Error: Invalid magic number in file header.")
            return

        print(f"File version: {version}")
        print(f"Number of files in archive: {num_files}")
        print("-" * 20)

        encryption_key = None
        # Check if a real salt was stored (implies encryption was used)
        if encryption_salt != b'\0' * 16: 
            if password is None:
                print("Error: Archive is encrypted. Password is required for decryption.")
                return
            try:
                encryption_key = derive_key(password, encryption_salt)
                print("Encryption key derived from password and salt.")
            except Exception as e:
                print(f"Error deriving encryption key: {e}. Cannot decrypt. Check password.")
                return
        else:
            print("Archive is not encrypted (no salt found in header).")

        # --- Read Manifest ---
        f.seek(manifest_offset)
        
        for i in range(num_files):
            # Read filename length
            filename_len_data = f.read(2)
            filename_len = struct.unpack('<H', filename_len_data)[0]

            # Read filename
            filename_bytes = f.read(filename_len)
            filename = filename_bytes.decode('utf-8')

            # Read original size, stored size, compression flag, encryption flag, IV, and file offset
            # Corrected from 41 to 42 bytes
            file_metadata_data = f.read(42) # 8 (orig_size) + 8 (stored_size) + 1 (comp_flag) + 1 (enc_flag) + 16 (IV) + 8 (file_offset) = 42 bytes
            original_size, stored_size, compression_flag, encryption_flag, iv, file_offset = \
                struct.unpack('<Q Q B B 16s Q', file_metadata_data)

            print(f"Found file: {filename}")
            print(f"  Original Size: {original_size} bytes")
            print(f"  Stored Size: {stored_size} bytes")
            print(f"  Compression: {'zlib' if compression_flag == 1 else 'None'}")
            print(f"  Encryption: {'AES-256-CBC' if encryption_flag == 1 else 'None'}")

            # --- Read and Process File Data ---
            # Save the current position (after reading manifest entry)
            current_position = f.tell()

            # Seek to the file's data
            f.seek(file_offset)
            
            # Read the data (this will be encrypted and/or compressed)
            file_data = f.read(stored_size)
            
            # Decrypt if necessary (first operation after reading)
            if encryption_flag == 1:
                if encryption_key is None:
                    print(f"  Error: Cannot decrypt '{filename}'. No encryption key available or password incorrect.")
                    f.seek(current_position) # Return to manifest position
                    continue # Skip this file
                try:
                    file_data = decrypt_data(encryption_key, iv, file_data, original_size)
                    print(f"  '{filename}': Decrypted.")
                except Exception as e:
                    print(f"  Error decrypting '{filename}': {e}. Data might be corrupt or password incorrect.")
                    f.seek(current_position) # Return to manifest position
                    continue # Skip this file
            
            # Decompress if necessary (after decryption)
            if compression_flag == 1:
                try:
                    decompressed_data = zlib.decompress(file_data)
                    # Verify decompressed size matches original size
                    if len(decompressed_data) != original_size:
                        print(f"  Warning: Decompressed size mismatch for '{filename}'. Expected {original_size}, got {len(decompressed_data)}.")
                    file_data = decompressed_data
                    print(f"  '{filename}': Decompressed.")
                except zlib.error as e:
                    print(f"  Error decompressing '{filename}': {e}. Storing raw data (might be encrypted/compressed incorrectly).")
            
            # Write the (possibly decrypted and/or decompressed) data to a new file
            output_path = os.path.join(output_folder, filename)
            with open(output_path, 'wb') as out_f:
                out_f.write(file_data)
            
            print(f"Extracted file to: {output_path}")

            # Return to the previous position to read the next manifest entry
            f.seek(current_position)
    
    print("\nAll files have been successfully extracted.")


# --- MAIN EXECUTION ---
# Define the archive to read and the folder to extract to
archive_to_read = "archive_encrypted_compressed.gme" # Read the encrypted/compressed archive
extraction_folder = "extracted_files"

# Prompt for password if the archive is encrypted
user_password = None
# A simple heuristic: if the filename implies encryption, ask for password.
# A more robust solution would read the header's salt first to determine if encrypted.
if os.path.exists(archive_to_read):
    # Read the header just to check the salt for encryption status
    with open(archive_to_read, 'rb') as f_check:
        try:
            f_check.seek(30) # Salt starts at byte 30 in header
            header_salt = f_check.read(16)
            if header_salt != b'\0' * 16:
                user_password = getpass("Enter password to decrypt archive (will not be displayed): ")
                if not user_password:
                    print("No password entered. Decryption will likely fail if archive is encrypted.")
        except Exception as e:
            print(f"Could not check archive header for encryption status: {e}")

read_gme_archive(archive_to_read, extraction_folder, password=user_password)
