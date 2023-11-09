import pyvjoy
import struct
import time
from threading import Thread
import serial.tools.list_ports

from config import CRC_TABLE, ARR_2A103_TABLE, SEEDS

def calc_checksum(packet, plength):
    v = SEEDS['P3/P4/Mavic']
    for i in range(0, plength):
        vv = v >> 8
        v = vv ^ CRC_TABLE[((packet[i] ^ v) & 0xFF)]
    return v

def calc_pkt55_hdr_checksum(seed, packet, plength):
    chksum = seed
    for i in range(0, plength):
        chksum = ARR_2A103_TABLE[((packet[i] ^ chksum) & 0xFF)]
    return chksum

def send_duml(serial: serial.Serial, source, target, cmd_type, cmd_set, cmd_id, payload = None):
    global sequence_number
    sequence_number = 0x34eb
    packet = bytearray.fromhex(u'55')
    length = 13
    if payload is not None:
        length = length + len(payload)

    if length > 0x3ff:
        print("Packet too large")
        exit(1)

    packet += struct.pack('B', length & 0xff)
    packet += struct.pack('B', (length >> 8) | 0x4) # MSB of length and protocol version
    hdr_crc = calc_pkt55_hdr_checksum(0x77, packet, 3)
    packet += struct.pack('B', hdr_crc)
    packet += struct.pack('B', source)
    packet += struct.pack('B', target)
    packet += struct.pack('<H', sequence_number)
    packet += struct.pack('B', cmd_type)
    packet += struct.pack('B', cmd_set)
    packet += struct.pack('B', cmd_id)

    if payload is not None:
        packet += payload

    crc = calc_checksum(packet, len(packet))
    packet += struct.pack('<H',crc)
    serial.write(packet)

    sequence_number += 1

def parseInput(input):
    # (min 364, center 1024, max 1684) -> (min 0, center 660, max 1320) -> (min 0x0000, center 0x4000, max 0x8000)
    return int((int.from_bytes(input, byteorder='little') - 364) / 1320 * 0x8000)

try:
    ports = serial.tools.list_ports.comports(True)

    for port in ports:
        try:
            print(port.description)
            if port.description.find("For Protocol") != -1:
                print("found DJI USB VCOM For Protocol")
                s = serial.Serial(port=port.name, baudrate=115200)
                print('Opened serial port:', s.name)
            else:
                print("skip")
        except (OSError, serial.SerialException):
            pass

except serial.SerialException as e:
    print('Could not open serial port:', e)
    exit(1)

st = {"rh": 0, "rv": 0, "lh": 0, "lv": 0}
camera = 0

def threaded_function():
    time.sleep(0.1)
    joystick = pyvjoy.VJoyDevice(1)

    while(True):
        sl0 = 0x4000 - camera if camera < 0x4000 - 0x1000 else 0
        sl1 = camera - 0x4000 if camera > 0x4000 + 0x1000  else 0

        joystick.set_axis(pyvjoy.HID_USAGE_X, st["lh"])
        joystick.set_axis(pyvjoy.HID_USAGE_Y, 0x8000 - st["lv"])
        joystick.set_axis(pyvjoy.HID_USAGE_RX, st["rh"])
        joystick.set_axis(pyvjoy.HID_USAGE_RY, 0x8000 - st["rv"])
        joystick.set_axis(pyvjoy.HID_USAGE_SL0, sl0)
        joystick.set_axis(pyvjoy.HID_USAGE_SL1, sl1)

        print(f'RH:{st["rh"]}, RV:{st["rv"]}, LV:{st["lv"]}, LH:{st["lh"]}, CAMERA:{camera} = (SL0:{sl0}, SL1:{sl1})')


thread = Thread(target = threaded_function, args = ())
thread.start()

try:
    # enable simulator mode for RC (without this stick positions are sent very slow by RC)
    send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x24, bytearray.fromhex('01'))

    while True:
        # read channel values
        send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x01, bytearray.fromhex(''))

        # read duml
        buffer = bytearray.fromhex('')
        while True:
            b = s.read(1)
            if b == bytearray.fromhex('55'):
                buffer.extend(b)
                ph = s.read(2)
                buffer.extend(ph)
                ph = struct.unpack('<H', ph)[0]
                pl = 0b0000001111111111 & ph
                pv = 0b1111110000000000 & ph
                pv = pv >> 10
                pc = s.read(1)
                buffer.extend(pc)
                pd = s.read(pl - 4)
                buffer.extend(pd)
                break
            else:
                break
        data = buffer

        # Reverse-engineered. Controller input seems to always be len 38.
        if len(data) == 38:
            # Reverse-engineered
            st["rh"] = parseInput(data[13:15])
            st["rv"] = parseInput(data[16:18])

            st["lv"] = parseInput(data[19:21])
            st["lh"] = parseInput(data[22:24])

            camera = parseInput(data[25:27])
            
except serial.SerialException as e:
    print('\n\nCould not read/write:', e)
except KeyboardInterrupt:
    print('\n\nDetected keyboard interrupt.')

print('Stopping.')
