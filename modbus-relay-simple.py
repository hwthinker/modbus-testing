# kirim_modbus.py
# by HwThinker

import sys
import serial
import serial.tools.list_ports

def calculate_crc(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if (crc & 0x0001):
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')  # LSB first

def print_bit_status(label, byte_val):
    for i in range(8):
        bit = (byte_val >> i) & 0x01
        print(f"  {label} {i+1}: {'ON' if bit else 'OFF'}")

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("⚠️ Tidak ada port serial yang terdeteksi.")
    else:
        print("📟 Port serial yang tersedia:")
        for port in ports:
            print(f"  - {port.device}")

def print_banner():
    print("\n\033[1;36m╔═══════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║    Modbus Relay Testing by HwThinker  V1.0    ║\033[0m")
    print("\033[1;36m╚═══════════════════════════════════════════════╝\033[0m\n")
    print("💡 Contoh penggunaan:")
    print("  python kirim_modbus.py -r COMx [baudrate] HEX1 HEX2 ...   # manual CRC")
    print("  python kirim_modbus.py -a COMx [baudrate] HEX1 HEX2 ...   # auto CRC")
    print("")
    list_serial_ports()

if len(sys.argv) < 5:
    print_banner()
    sys.exit(1)

mode = sys.argv[1]
port = sys.argv[2]

try:
    baudrate = int(sys.argv[3])
    hex_values = sys.argv[4:]
except ValueError:
    print("❌ Error: Baudrate harus berupa angka.")
    sys.exit(1)

# Ubah HEX ke bytes
try:
    data = bytearray(int(h, 16) for h in hex_values)
except ValueError:
    print("❌ Error: Input HEX tidak valid.")
    sys.exit(1)

# Tambah CRC jika -a
if mode == '-a':
    crc = calculate_crc(data)
    data += crc

elif mode != '-r':
    print("❌ Error: Mode harus -a (auto CRC) atau -r (raw/manual CRC).")
    sys.exit(1)

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    ser.write(data)
    print(f"[TX] {' '.join(f'{b:02X}' for b in data)}")

    response = ser.read(8)
    ser.close()

    if response:
        hex_resp = ' '.join(f"{b:02X}" for b in response)
        print(f"[RX] {hex_resp}")

        if len(response) >= 4:
            slave = response[0]
            function = response[1]

            if function == 0x01:
                print("Status Relay:")
                print_bit_status("Relay", response[3])
            elif function == 0x02:
                print("Status Input Optocoupler:")
                print_bit_status("Input", response[3])
            elif function == 0x03 and len(response) >= 5:
                print(f"Alamat Slave ID: {response[4]} (0x{response[4]:02X})")
    else:
        print("⚠️ Tidak ada respon dari perangkat.")

except serial.SerialException as e:
    print(f"⚠️ Gagal membuka port {port}: {e}")
    if "The parameter is incorrect" in str(e):
        print("💡 Mungkin kamu lupa nulis baudrate atau port salah / sedang dipakai.")
