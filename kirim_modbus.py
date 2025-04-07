import sys
import serial

# Cek minimal argumen (harus minimal: port + 1 hex)
if len(sys.argv) < 3:
    print("Usage:")
    print("  python kirim_modbus.py COMx [baudrate] HEX1 HEX2 ...")
    print("Contoh:")
    print("  python kirim_modbus.py COM3 9600 FF 05 00 00 00 00 D8 14")
    print("  python kirim_modbus.py COM3 FF 05 00 00 00 00 D8 14  (baudrate default 9600)")
    sys.exit(1)

# Default baudrate
baudrate = 9600

# Cek apakah argumen ke-2 adalah baudrate atau hex
try:
    # Coba parse baudrate
    int(sys.argv[2])
    port = sys.argv[1]
    baudrate = int(sys.argv[2])
    hex_values = sys.argv[3:]
except ValueError:
    # Jika gagal parse int, berarti baudrate tidak disebut
    port = sys.argv[1]
    hex_values = sys.argv[2:]

# Konversi HEX ke byte
try:
    byte_data = bytes(int(h, 16) for h in hex_values)
except ValueError:
    print("Error: Pastikan HEX dalam format benar (contoh: FF 05 00 00 ...)")
    sys.exit(1)

# Kirim data
try:
    ser = serial.Serial(port, baudrate, timeout=1)
    ser.write(byte_data)
    ser.close()
    print(f"Sukses kirim ke {port} @ {baudrate} baud:")
    print(' '.join(hex_values))
except serial.SerialException as e:
    print(f"Gagal membuka port {port}: {e}")
