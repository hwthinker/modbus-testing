#!/usr/bin/env python3
import sys
import crcmod

def main():
    if len(sys.argv) < 2:
        print("Usage: python crc-gen.py <hex_command_without_crc>")
        print("Example: python crc-gen.py FF 0F 00 00 00 08 01 03")
        sys.exit(1)

    # Parse input hex bytes (skip 'python crc-gen.py' and join arguments)
    hex_str = ' '.join(sys.argv[1:])
    try:
        data = bytes.fromhex(hex_str)
    except ValueError:
        print("Error: Invalid hex string. Ensure spaces separate bytes.")
        sys.exit(1)

    # Calculate Modbus CRC-16
    crc_func = crcmod.predefined.Crc("modbus")
    crc_func.update(data)
    crc = crc_func.crcValue  # Returns CRC as integer (e.g., 0x305C)

    # Split CRC into low and high bytes (little-endian)
    crc_bytes = crc.to_bytes(2, byteorder='little')  # [0x5C, 0x30] for 0x305C
    crc_hex = crc_bytes.hex().upper()  # '5C30'

    # Construct full command
    full_command = hex_str + ' ' + crc_hex[:2] + ' ' + crc_hex[2:]
    print(f"Full Modbus Command: {full_command}")

if __name__ == "__main__":
    main()
