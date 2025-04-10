import sys
import serial
import time
import serial.tools.list_ports  # Import untuk deteksi port serial

def control_relay(port, baudrate, slave_id, channel, state):
    """Fungsi baru untuk mengontrol relay dengan format sederhana"""
    try:
        # Handle slave ID
        if slave_id.startswith('0x'):
            slave_id_hex = int(slave_id, 16)
        elif all(c in '0123456789ABCDEFabcdef' for c in slave_id):
            slave_id_hex = int(slave_id, 16)
        else:
            slave_id_hex = int(slave_id)
            
        if not (0 <= slave_id_hex <= 255):
            raise ValueError("Slave ID harus antara 0-255")
        
        # Validasi channel (0-7 untuk relay 1-8)
        channel_num = int(channel) - 1  # Convert ke 0-based index
        if not (0 <= channel_num <= 7):
            raise ValueError("Channel harus antara 1-8")
            
        # Validasi state (0 atau 1)
        state_val = int(state)
        if state_val not in [0, 1]:
            raise ValueError("State harus 0 (OFF) atau 1 (ON)")
            
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Format payload Modbus (Function Code 0x05)
    value = 0xFF00 if state_val == 1 else 0x0000
    payload = bytearray([
        slave_id_hex, 
        0x05, 
        0x00, 
        channel_num, 
        (value >> 8) & 0xFF, 
        value & 0xFF
    ])
    crc = calculate_crc(payload)
    payload += crc
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(payload)
        print(f"[TX] {' '.join(f'{b:02X}' for b in payload)}")
        response = ser.read(8)
        ser.close()
        
        if response:
            print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
            if len(response) >= 6 and response[1] == 0x05:
                print(f"\nRelay {channel_num+1} berhasil di-set ke {'ON 🟢' if state_val else 'OFF 🔴'}")
            else:
                print("⚠️ Format respons tidak valid")
        else:
            print("⚠️ Tidak ada respon dari perangkat.")
    except serial.SerialException as e:
        print(f"⚠️ Gagal membuka port {port}: {e}")
        if "The parameter is incorrect" in str(e):
            print("💡 Mungkin port salah atau sedang dipakai.")

def check_relay_status(port, baudrate, slave_id):
    """Fungsi untuk membaca status relay dengan format sederhana"""
    try:
        # Handle berbagai format slave ID
        if slave_id.startswith('0x'):
            slave_id_hex = int(slave_id, 16)
        elif all(c in '0123456789ABCDEFabcdef' for c in slave_id):
            slave_id_hex = int(slave_id, 16)
        else:
            slave_id_hex = int(slave_id)
            
        if not (0 <= slave_id_hex <= 255):
            raise ValueError("Slave ID harus antara 0-255")
    except ValueError:
        print("❌ Error: Slave ID tidak valid. Harus antara 0-255 atau format hex (misal: FF, 0FF, 0xFF)")
        sys.exit(1)

    # Format payload Modbus untuk membaca relay (Function Code 0x01)
    payload = bytearray([slave_id_hex, 0x01, 0x00, 0x00, 0x00, 0x08])
    crc = calculate_crc(payload)
    payload += crc
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(payload)
        print(f"[TX] {' '.join(f'{b:02X}' for b in payload)}")
        response = ser.read(8)
        ser.close()
        
        if response:
            print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
            if len(response) >= 4 and response[1] == 0x01:
                print("\nStatus Relay:")
                print_bit_status("Relay ", response[3])
            else:
                print("⚠️ Format respons tidak valid untuk pengecekan relay")
        else:
            print("⚠️ Tidak ada respon dari perangkat.")
    except serial.SerialException as e:
        print(f"⚠️ Gagal membuka port {port}: {e}")
        if "The parameter is incorrect" in str(e):
            print("💡 Mungkin port salah atau sedang dipakai.")

def check_input_status(port, baudrate, slave_id):
    """Fungsi baru untuk mengecek status input dengan format yang lebih sederhana"""
    try:
        # Handle berbagai format slave ID:
        if slave_id.startswith('0x'):
            # Format 0xFF
            slave_id_hex = int(slave_id, 16)
        elif all(c in '0123456789ABCDEFabcdef' for c in slave_id):
            # Format FF (hex tanpa prefix)
            slave_id_hex = int(slave_id, 16)
        else:
            # Format decimal
            slave_id_hex = int(slave_id)
            
        if not (0 <= slave_id_hex <= 255):
            raise ValueError("Slave ID harus antara 0-255")
    except ValueError:
        print("❌ Error: Slave ID tidak valid. Harus antara 0-255 atau format hex (misal: FF, 0FF, 0xFF)")
        sys.exit(1)

    # Format payload Modbus untuk membaca input (Function Code 0x02)
    payload = bytearray([slave_id_hex, 0x02, 0x00, 0x00, 0x00, 0x08])
    crc = calculate_crc(payload)
    payload += crc
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(payload)
        print(f"[TX] {' '.join(f'{b:02X}' for b in payload)}")
        response = ser.read(8)
        ser.close()
        
        if response:
            print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
            if len(response) >= 4 and response[1] == 0x02:
                print("\nStatus Input Optocoupler:")
                print_bit_status("Input", response[3])
            else:
                print("⚠️ Format respons tidak valid untuk pengecekan input")
        else:
            print("⚠️ Tidak ada respon dari perangkat.")
    except serial.SerialException as e:
        print(f"⚠️ Gagal membuka port {port}: {e}")
        if "The parameter is incorrect" in str(e):
            print("💡 Mungkin port salah atau sedang dipakai.")

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
    """Fungsi modifikasi untuk menampilkan status dengan emoji dan alignment rapi"""
    for i in range(8):
        bit = (byte_val >> i) & 0x01
        status = "ON  🟢" if bit else "OFF 🔴"  # Tambah spasi ekstra setelah ON
        print(f"  {label}{i+1}: {status}")

def detect_serial_ports():
    """Mendeteksi semua port serial yang tersedia"""
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("⚠️ Tidak ada port serial yang terdeteksi.")
        return
    
    print(f"📊 Port Serial yang Terdeteksi: {len(ports)}")
    print("=" * 50)
    for i, port in enumerate(ports, 1):
        print(f"Port #{i}: {port.device}")
        print(f"  Deskripsi: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        if hasattr(port, 'manufacturer') and port.manufacturer:
            print(f"  Manufacturer: {port.manufacturer}")
        print("-" * 50)
    
    print("💡 Gunakan salah satu port di atas untuk komunikasi Modbus")

def check_slave_id(port, baudrate):
    # Perintah untuk mengecek Slave ID: 00 03 00 00 00 01 + CRC
    payload = bytearray([0x00, 0x03, 0x00, 0x00, 0x00, 0x01])
    crc = calculate_crc(payload)
    payload += crc
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(payload)
        print(f"[TX] {' '.join(f'{b:02X}' for b in payload)}")
        response = ser.read(8)
        ser.close()
        
        if response:
            print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
            if len(response) >= 5 and response[1] == 0x03:
                print(f"Alamat Slave ID: {response[4]} (0x{response[4]:02X})")
            else:
                print("⚠️ Format respons tidak valid untuk pengecekan Slave ID")
        else:
            print("⚠️ Tidak ada respon dari perangkat.")
    except serial.SerialException as e:
        print(f"⚠️ Gagal membuka port {port}: {e}")
        if "The parameter is incorrect" in str(e):
            print("💡 Mungkin kamu lupa nulis baudrate atau port salah / sedang dipakai.")

def test_relays(port, baudrate, slave_id, bit_mode):
    ser = serial.Serial(port, baudrate, timeout=1)
    try:
        # ON bergantian
        for i in range(bit_mode):
            relay_state = 1 << i
            payload_on = bytearray([int(slave_id, 16), 0x05, 0x00, i, 0xFF, 0x00])
            crc_on = calculate_crc(payload_on)
            payload_on += crc_on
            ser.write(payload_on)
            print(f"[TX] {' '.join(f'{b:02X}' for b in payload_on)}")
            response = ser.read(8)
            if response:
                print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
                print(f"🟢 ON  Relay {i+1}")
            else:
                print(f"⚠️ Tidak ada respon untuk ON Relay {i+1}")
            time.sleep(0.5)

        # OFF bergantian
        for i in range(bit_mode):
            payload_off = bytearray([int(slave_id, 16), 0x05, 0x00, i, 0x00, 0x00])
            crc_off = calculate_crc(payload_off)
            payload_off += crc_off
            ser.write(payload_off)
            print(f"[TX] {' '.join(f'{b:02X}' for b in payload_off)}")
            response = ser.read(8)
            if response:
                print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
                print(f"🔴 OFF Relay {i+1}")
            else:
                print(f"⚠️ Tidak ada respon untuk OFF Relay {i+1}")
            time.sleep(0.5)

    finally:
        ser.close()

def set_slave_id(port, baudrate, new_slave_id):
    try:
        new_id = int(new_slave_id, 16)
        if not (0 <= new_id <= 255):
            raise ValueError("Slave ID harus antara 0-255")
        if new_id == 255:
            print("⚠️ Peringatan: 0xFF adalah alamat broadcast. Tidak semua perangkat menerima perintah pengubahan ID via 0xFF.")
    except ValueError:
        print("❌ Error: Slave ID tidak valid. Harus dalam format hex, misal: 0F atau FF")
        sys.exit(1)

    payload = bytearray([0x00, 0x10, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, new_id])
    crc = calculate_crc(payload)
    payload += crc

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(payload)
        print(f"[TX] {' '.join(f'{b:02X}' for b in payload)}")
        response = ser.read(8)
        ser.close()
        if response:
            print(f"[RX] {' '.join(f'{b:02X}' for b in response)}")
        else:
            print("⚠️ Tidak ada respon dari perangkat.")
    except serial.SerialException as e:
        print(f"⚠️ Gagal membuka port {port}: {e}")
        if "The parameter is incorrect" in str(e):
            print("💡 Mungkin kamu lupa nulis baudrate atau port salah / sedang dipakai.")

# Ganti semua opsi di bagian parser argumen dengan:
if len(sys.argv) < 2:
    print("Penggunaan:")
    print("  MODBUS Relay Controller")
    print("  Format umum: python kirim_modbus.py [OPTION] [PARAMETERS]")
    print("\nOpsi utama (MODBUS):")
    print("  -M atau --manual HEX1 HEX2 ...  # Kirim perintah manual (raw)")
    print("  -O atau --auto HEX1 HEX2 ...   # Kirim perintah dengan auto CRC")
    print("  -D atau --detect               # Deteksi port serial")
    print("  -B atau --relay-status         # Baca status relay")
    print("  -U atau --input-status         # Baca status input")
    print("  -S atau --set-slave            # Set slave address")
    print("  -C atau --check-slave          # Cek slave ID")
    print("  -T atau --test-relay           # Test relay otomatis")
    print("  -R atau --relay-control      # Kontrol relay per channel")
    print("\nContoh:")
    print("  python kirim_modbus.py -M COM3 9600 FF     #  Kirim perintah manual")
    print("  python kirim_modbus.py -O COM3 9600 FF     # Kirim perintah dengan auto CRC")
    print("  python kirim_modbus.py -D COM3 9600        # Cek Alamat Modbus Slave")
    print("  python kirim_modbus.py -B COM3 9600 FF     # Baca relay (Slave ID 255)")
    print("  python kirim_modbus.py -U COM3 9600 FF     # Baca input (Slave ID 255)")
    print("  python kirim_modbus.py -S COM3 9600 FF     # Set slave ID ke 255")
    print("  python kirim_modbus.py -C COM3 9600        # Cek Set slave ID ")
    print("  python kirim_modbus.py -T COM3 9600 FF -b 4 # Run Relay (Slave ID 255) B 4")
             
    print("\nContoh kontrol relay:")
    print("  python kirim_modbus.py -R COM3 9600 FF 1 1    # Relay 1 ON (Slave ID 255)")
    print("  python kirim_modbus.py -R COM3 9600 FF 1 0     # Relay 1 OFF (Slave ID 255)")
    sys.exit(1)

# Ambil opsi pertama (hilangkan '-' jika ada)
option = sys.argv[1].replace('-', '').upper()


mode = sys.argv[1]

# Opsi untuk deteksi port serial
if option in ['D', 'DETECT']:
    detect_serial_ports()
    sys.exit(0)

# Untuk semua opsi lain yang membutuhkan parameter port
if len(sys.argv) < 3:
    print("❌ Error: Parameter tidak cukup")
    sys.exit(1)

port = sys.argv[2]


if option in ['R', 'RELAYCONTROL']: 
    if len(sys.argv) != 7:
        print("❌ Error: Format kontrol relay salah. Contoh:")
        print("  python kirim_modbus.py -m COM3 9600 FF 1 1   # Relay 1 ON")
        print("  python kirim_modbus.py -m COM3 9600 02 4 0    # Relay 4 OFF")
        sys.exit(1)
    try:
        port = sys.argv[2]
        baudrate = int(sys.argv[3])
        slave_id = sys.argv[4]
        channel = sys.argv[5]
        state = sys.argv[6]
        control_relay(port, baudrate, slave_id, channel, state)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate harus berupa angka.")
        sys.exit(1)

if option in ['U', 'INPUTSTATUS']:
    if len(sys.argv) != 5:
        print("❌ Error: Format baca relay salah. Contoh: python kirim_modbus.py -b COM3 9600 FF")
        print("          atau: python kirim_modbus.py -b COM3 9600 1")
        sys.exit(1)
    try:
        port = sys.argv[2]
        baudrate = int(sys.argv[3])
        slave_id = sys.argv[4]
        check_relay_status(port, baudrate, slave_id)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate harus berupa angka.")
        sys.exit(1)

if option in ['U', 'INPUTSTATUS']:
    if len(sys.argv) != 5:
        print("❌ Error: Format cek input salah. Contoh: python kirim_modbus.py -i COM3 9600 FF")
        print("          atau: python kirim_modbus.py -i COM3 9600 1")
        sys.exit(1)
    try:
        port = sys.argv[2]
        baudrate = int(sys.argv[3])
        slave_id = sys.argv[4]
        check_input_status(port, baudrate, slave_id)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate harus berupa angka.")
        sys.exit(1)

# Tambahan untuk opsi -c (cek slave ID)
if option in ['C', 'CHECKSLAVE']:
    if len(sys.argv) != 4:
        print("❌ Error: Format cek slave ID salah. Contoh: python kirim_modbus.py -c COM3 9600")
        sys.exit(1)
    try:
        baudrate = int(sys.argv[3])
        check_slave_id(port, baudrate)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate harus berupa angka.")
        sys.exit(1)

if option in ['T', 'TESTRELAY']:
    if len(sys.argv) != 7 or sys.argv[5] != '-b' or sys.argv[6] not in ['4', '8']:
        print("❌ Error: Format test relay salah. Contoh: python kirim_modbus.py -T COM3 9600 0F -b 8")
        sys.exit(1)
    try:
        baudrate = int(sys.argv[3])
        slave_id = sys.argv[4]
        bit_mode = int(sys.argv[6])
        test_relays(port, baudrate, slave_id, bit_mode)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate atau bit_mode tidak valid.")
        sys.exit(1)

if option in ['S', 'SETSLAVE']:
    if len(sys.argv) != 5:
        print("❌ Error: Format set slave salah. Contoh: python kirim_modbus.py -s COM3 9600 0F")
        sys.exit(1)
    try:
        baudrate = int(sys.argv[3])
        slave_id = sys.argv[4]
        set_slave_id(port, baudrate, slave_id)
        sys.exit(0)
    except ValueError:
        print("❌ Error: Baudrate harus berupa angka.")
        sys.exit(1)

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
    print("❌ Error: Input HEX tidak valid. Gunakan format hex seperti 0F, FF, 1A.")
    sys.exit(1)

# Tambah CRC jika -O
if option in ['O', 'AUTO']:
    crc = calculate_crc(data)
    data += crc
elif option not in ['M', 'MANUAL']: 
    print("❌ Error: parameter tidak dikenal ")
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
                print("Status Relay: bb ")
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
