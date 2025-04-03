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
    if readings[0]>16770000:
        print("1: ", readings[0]-16770000)
    else:
        print("1: ", readings[0])
    if readings[1]>16770000:
        print("2: ", readings[1]-16770000)
    else:
        print("2: ", readings[1])
    
    if readings[2]>16770000:
        print("3: ", readings[2]-16770000)
    else:
        print("3: ", readings[2])