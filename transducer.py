import time
import serial
arduino = serial.Serial(port='COM8', baudrate=115200)
readings=[0,0,0]
message = "5000000000000"

for i in range(20):
    arduino.write(message.encode())
    time.sleep(0.3)
    response = arduino.read(12)
    readings[0] = int.from_bytes(response[0:4], byteorder='big')
    readings[1] = int.from_bytes(response[4:8], byteorder='big')
    readings[2] = int.from_bytes(response[8:12], byteorder='big')

    print("1: ", readings[0])
    print("2: ", readings[1])
    print("3: ", readings[2])