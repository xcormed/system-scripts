import serial
import time
from collections import deque
from movingaverage import MovingAverage
import struct

# Configure the serial connection with MODBUS parameters
ser = serial.Serial(
    port='COM7',          
    baudrate=38400,       # Set to 38400 as required
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1             # Timeout for read operations
)

def crc16(data: bytes) -> bytes:
    """Calculate MODBUS RTU CRC-16."""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def send_modbus_command(command):
    """
    Send a MODBUS command to the SONOTEC sensor, adding the necessary CRC,
    and read the response.
    """
    # Calculate CRC and append it to the command
    command_with_crc = command + crc16(command)
    #print(f"Sending: {command_with_crc.hex()}")

    # Send the command with CRC
    ser.write(command_with_crc)

    # Wait for a response (sensor response times may vary; adjust if needed)
    time.sleep(0.1)
    response = ser.read(ser.in_waiting or 1)  # Read all available bytes

    return response

# This command reads 2 registers starting from register 0 for device address 1
command = bytes.fromhex('010300080005040B')

moving_avg = MovingAverage(window_size=5)
# Send command and receive response

for i in range(10):
    response = send_modbus_command(command)
    hex_response = response.hex()[12:16]
    #decimal_response = int(hex_response, 16)
    flow_val=struct.unpack('>f', response[5:9])[0]
    print(f"Received: {flow_val}")
    #print(f"Decimal: {decimal_response}")
    #print(f"Moving Average: {moving_avg.add(decimal_response)}")
    time.sleep(0.2)

# Close the serial connection
ser.close()
