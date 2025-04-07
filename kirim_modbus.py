import sys
import serial

def print_bit_status(label, byte_val):
    for i in range(8):
        bit = (byte_val >> i) & 0x01
        print(f"  {label} {i+1}: {'ON' if bit else 'OFF'}")

# Cek argumen minimal
if len(sys.argv) < 3:
    print("Usage:")
    print("  python kirim_modbus.py COMx [baudrate] HEX1 HEX2 ...")
    print("Contoh:")
    print("  python kirim_modbus.py COM3 9600 FF 01 00 00 00 08 28 12")
    print("  python kirim_modbus.py COM3 FF 01 00 00 00 08 28 12  (default baudrate 9600)")
    sys.exit(1)

# Default baudrate
baudrate = 9600

# Parsing argumen
try:
    int(sys.argv[2])
    port = sys.argv[1]
    baudrate = int(sys.argv[2])
    hex_values = sys.argv[3:]
except ValueError:
    port = sys.argv[1]
    hex_values = sys.argv[2:]

# Konversi HEX ke bytes
try:
    byte_data = bytes(int(h, 16) for h in hex_values)
except ValueError:
    print("❌ Error: HEX tidak valid.")
    sys.exit(1)

# Kirim dan baca
try:
    ser = serial.Serial(port, baudrate, timeout=1)
    ser.write(byte_data)
    print(f"[TX] {' '.join(hex_values)}")

    response = ser.read(8)
    ser.close()

    if response:
        hex_resp = ' '.join(f"{b:02X}" for b in response)
        print(f"[RX] {hex_resp}")

        # Deteksi berdasarkan fungsi
        if len(response) >= 4:
            slave_addr = response[0]
            func_code = response[1]

            if func_code == 0x01:
                print("Status Relay:")
                print_bit_status("Relay", response[3])

            elif func_code == 0x02:
                print("Status Input Optocoupler:")
                print_bit_status("Input", response[3])

            elif func_code == 0x03 and len(response) >= 5:
                slave_id = response[4]
                print(f"Alamat Slave ID: {slave_id} (0x{slave_id:02X})")

    else:
        print("⚠️ Tidak ada respon dari perangkat.")

except serial.SerialException as e:
    print(f"⚠️ Gagal membuka port {port}: {e}")
    if "The parameter is incorrect" in str(e):
        print("💡 Kemungkinan penyebab:")
        print("   - Kamu lupa menuliskan baudrate dan byte pertama adalah angka (misalnya '00')")
        print("   - Port COM tidak tersedia / sedang dipakai program lain")
        print("   - Nama port salah (misal 'COM33' padahal tidak ada)")
