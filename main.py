# -*- coding: utf-8 -*-
"""
Created on Thu May  2 16:02:19 2024
@author: 14438
"""

import tkinter as tk
import numpy as np
from serial import Serial
from serial import SerialException
import serial
import customtkinter
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import pandas as pd 
from datetime import datetime
import time
from tkinter.messagebox import askyesno
from numpad import Numpad
from keyboard import Keyboard
import threading
import queue
from movingaverage import MovingAverage
import struct


matplotlib.rcParams['interactive'] == True
plt.ioff()

customtkinter.set_appearance_mode("Dark") 
customtkinter.set_default_color_theme("blue")

arduino = serial.Serial(port='COM8', baudrate=115200)
time.sleep(0.5)

class App(customtkinter.CTk):
    def __init__(self):

        super().__init__()
        self.is_on = True

        self.stm32_lock=threading.Lock()
        self.flow_lock=threading.Lock()

        self.data_queue = queue.Queue()
        self.motor_queue=queue.Queue()

        self.running=True

        self.sensor_thread=threading.Thread(target=self.read_sensor_data)
        self.sonotec_thread=threading.Thread(target=self.read_sonotec_data)
        self.motor_thread=threading.Thread(target=self.send_motor_command)

        self.sensor_thread.daemon=True
        self.sonotec_thread.daemon=True
        self.motor_thread.daemon=True

        self.sensor_thread.start()
        self.sonotec_thread.start()
        self.motor_thread.start()

        self.command = bytes.fromhex('010300080005040B')
        self.moving_avg = MovingAverage(window_size=50)

        # Removes any focus from entries and buttons when the main window is clicked
        self.bind("<Button-1>", self.on_click)

        # Establish serial connections
        

        # Setup csv file
        self.df = pd.DataFrame(columns=['TIME','PRESSURE PRE (mmHg)','PRESSURE MID (mmHg)','PRESSURE POST (mmHg)'])
        self.timeThen = time.time()
        self.timeFive = time.time()

        # Transducer calibration constants
        self.hx_cal=0.00007165
        self.hx2_cal=0.00006999
        self.hx3_cal=0.000069212
        self.readings=[0,0,0]

        # Flow sensor
        self.data_buffer = []
        self.buffer_length = 20
        
        # Initialize window title   
        self.title("XCOR Pump Control")
        
        #self.d1Speed_var=tk.IntVar(value=0)
        #self.d2Speed_var=tk.IntVar(value=0)
        #self.bloodSpeed_var=tk.IntVar(value=0)
        #self.rSpeed_var=tk.IntVar(value=0)

        # Setup ctk variables
        self.d1Switch_var=customtkinter.StringVar(value="CW")
        self.d2Switch_var=customtkinter.StringVar(value="CW")
        self.repSwitch_var=customtkinter.StringVar(value="CW")
        self.bloodSwitch_var=customtkinter.StringVar(value="CW")
        
        self.pre_val=customtkinter.StringVar()
        self.mid_val=customtkinter.StringVar()
        self.post_val=customtkinter.StringVar()
        self.flow_val=customtkinter.StringVar()
        self.csv_title=customtkinter.StringVar()

        # Make all columns equal size        
        self.columnconfigure(list(range(5)), weight = 1, uniform="Silent_Creme")
        
        self.calibration_factor1=0
        self.calibration_factor2=0
        self.calibration_factor3=0
        
        self.d1_frame = customtkinter.CTkFrame(self)
        self.d1_frame.grid(row=0, column=0, rowspan=1, padx=(10, 5), pady=(10, 10), sticky="ew")
        
        self.d2_frame = customtkinter.CTkFrame(self)
        self.d2_frame.grid(row=0, column=1, rowspan=1, padx=(5, 5), pady=(10, 10), sticky="ew")
        
        self.blood_frame = customtkinter.CTkFrame(self)
        self.blood_frame.grid(row=0, column=2, rowspan=1, padx=(5, 5), pady=(10, 10), sticky="ew")
        
        self.rep_frame = customtkinter.CTkFrame(self)
        self.rep_frame.grid(row=0, column=3, rowspan=1, padx=(5, 5), pady=(10, 10), sticky="ew")
        
        self.start_frame = customtkinter.CTkFrame(self)
        self.start_frame.grid(row=0, column=4, rowspan=3, columnspan=1, padx=(5, 10), pady=(10, 10), sticky="new")
        
        self.readings_frame = customtkinter.CTkFrame(self)
        self.readings_frame.grid(row=1, column=4, rowspan=3, columnspan=1, padx=(5, 5), pady=(195, 10), sticky="n")

        self.flow_frame = customtkinter.CTkFrame(self)
        self.flow_frame.grid(row=1, column=4, rowspan=1, columnspan=1, padx=(5, 5), pady=(350, 10), sticky="n")
        
        self.plot_frame = customtkinter.CTkFrame(self)
        self.plot_frame.grid(row=1, column=0, rowspan=1, columnspan=4, padx=(5, 5), pady=(10, 10), sticky="n")
        
        self.screen_height = self.winfo_screenmmheight()*0.055
        self.screen_width = self.winfo_screenmmwidth()*0.074

        self.fig, self.ax = plt.subplots()
        #self.fig.set_size_inches(self.screen_width,self.screen_height)
        self.fig.set_size_inches(14.5,5.75)
        self.plotbuffer = np.zeros(500)
        self.plotbuffer2 = np.zeros(500)
        self.plotbuffer3 = np.zeros(500)
        self.line, = self.ax.plot(self.plotbuffer, color="green")
        self.line2, = self.ax.plot(self.plotbuffer2, color = "blue")
        self.line3, = self.ax.plot(self.plotbuffer3, color = "orange")
        self.ax.set_ylabel("Pressure (mmHg)", fontname="Segoe UI", fontsize=20, weight='bold')
        #self.ax.set_xticklabels(fontsize=14)
        self.ax.tick_params(axis='x', labelsize=15)
        self.ax.tick_params(axis='y', which='both', labelleft=True, labelright=True, labelsize=15)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0,column=0,padx=(20,20),pady=(20,20))
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=200, cache_frame_data=False)
        
        # LABELS AND BUTTONS
        # D1
        self.d1_label = customtkinter.CTkLabel(master=self.d1_frame, text = 'D1 FLOW:', font=('arial',20, 'bold'))
        self.d1_label.grid(row=0,column=0, columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.d1_entry = customtkinter.CTkEntry(master=self.d1_frame, placeholder_text="0", font=('arial',20,'normal'), width=75)
        self.d1_entry.grid(row=1,column=0, padx=(50,5), pady=10, sticky="e")
        self.numpad1 = Numpad(self, self.d1_entry, x_offset=-130, y_offset=100)
        
        self.d1_lph = customtkinter.CTkLabel(master=self.d1_frame, text = 'LPH', font=('arial',20, 'bold'))  
        self.d1_lph.grid(row=1,column=1, padx=(0,5), pady=10, sticky="w")
        
        self.d1_submit_btn=customtkinter.CTkButton(master=self.d1_frame,text = 'SUBMIT', command = self.d1Submit, font=('arial',20, 'bold'))
        self.d1_submit_btn.grid(row=2,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.d1_stop_btn=customtkinter.CTkButton(master=self.d1_frame,text = 'STOP', command = self.d1Stop, font=('arial',20, 'bold'), fg_color='red')
        self.d1_stop_btn.grid(row=3,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.d1_switch=customtkinter.CTkSwitch(master = self.d1_frame, textvariable = self.d1Switch_var, variable = self.d1Switch_var, onvalue = "CW", offvalue = "CCW")
        self.d1_switch.grid(row=4,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        # D2
        self.d2_label = customtkinter.CTkLabel(master=self.d2_frame, text = 'D2 FLOW:', font=('arial',20, 'bold'))
        self.d2_label.grid(row=0,column=0, columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.d2_entry = customtkinter.CTkEntry(master=self.d2_frame, placeholder_text="0", font=('arial',20,'normal'), width=75)
        self.d2_entry.grid(row=1,column=0, padx=(50,5), pady=10, sticky="e")
        self.numpad2 = Numpad(self, self.d2_entry, x_offset=-130, y_offset=100)
        
        self.d2_lph = customtkinter.CTkLabel(master=self.d2_frame, text = 'LPH', font=('arial',20, 'bold'))  
        self.d2_lph.grid(row=1,column=1, padx=(0,5), pady=10, sticky="w")
        
        self.d2_submit_btn=customtkinter.CTkButton(master=self.d2_frame,text = 'SUBMIT', command = self.d2Submit, font=('arial',20, 'bold'))
        self.d2_submit_btn.grid(row=2,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.d2_stop_btn=customtkinter.CTkButton(master=self.d2_frame,text = 'STOP', command = self.d2Stop, font=('arial',20, 'bold'), fg_color='red')
        self.d2_stop_btn.grid(row=3,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")        
        
        self.d2_switch=customtkinter.CTkSwitch(master = self.d2_frame, textvariable = self.d2Switch_var, variable = self.d2Switch_var, onvalue = "CW", offvalue = "CCW")
        self.d2_switch.grid(row=4,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        # Replacement Fluid
        self.rep_label = customtkinter.CTkLabel(master=self.rep_frame, text = 'REP FLOW:', font=('arial',20, 'bold'))
        self.rep_label.grid(row=0,column=0, columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.rep_entry = customtkinter.CTkEntry(master=self.rep_frame, placeholder_text="0", font=('arial',20,'normal'), width=75)
        self.rep_entry.grid(row=1,column=0, padx=(50,5), pady=10, sticky="")
        self.numpad3 = Numpad(self, self.rep_entry, x_offset=-130, y_offset=100)
        
        self.rep_mlmin = customtkinter.CTkLabel(master=self.rep_frame, text = 'mL/min', font=('arial',20, 'bold'))  
        self.rep_mlmin.grid(row=1,column=1, padx=(0,5), pady=10, sticky="w")
        
        self.rep_submit_btn=customtkinter.CTkButton(master=self.rep_frame,text = 'SUBMIT', command = self.repSubmit, font=('arial',20, 'bold'))
        self.rep_submit_btn.grid(row=2,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.rep_stop_btn=customtkinter.CTkButton(master=self.rep_frame,text = 'STOP', command = self.repStop, font=('arial',20, 'bold'), fg_color='red')
        self.rep_stop_btn.grid(row=3,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.rep_switch=customtkinter.CTkSwitch(master = self.rep_frame, textvariable = self.repSwitch_var, variable = self.repSwitch_var, onvalue = "CW", offvalue = "CCW")
        self.rep_switch.grid(row=4,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        # Blood
        self.blood_label = customtkinter.CTkLabel(master=self.blood_frame, text = 'BLOOD FLOW:', font=('arial',20, 'bold'))
        self.blood_label.grid(row=0,column=0, columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.blood_entry = customtkinter.CTkEntry(master=self.blood_frame, placeholder_text="0", font=('arial',20,'normal'), width=75)
        self.blood_entry.grid(row=1,column=0, padx=(50,5), pady=10, sticky="")
        self.numpad4 = Numpad(self, self.blood_entry, x_offset=-130, y_offset=100)
               
        self.blood_mlmin = customtkinter.CTkLabel(master=self.blood_frame, text = 'mL/min', font=('arial',20, 'bold'))  
        self.blood_mlmin.grid(row=1,column=1, padx=(0,5), pady=10, sticky="w")
        
        self.blood_submit_btn=customtkinter.CTkButton(master=self.blood_frame,text = 'SUBMIT', command = self.bloodSubmit, font=('arial',20, 'bold'))
        self.blood_submit_btn.grid(row=2,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.blood_stop_btn=customtkinter.CTkButton(master=self.blood_frame,text = 'STOP', command = self.bloodStop, font=('arial',20, 'bold'), fg_color='red')
        self.blood_stop_btn.grid(row=3,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        self.blood_switch=customtkinter.CTkSwitch(master = self.blood_frame, textvariable = self.bloodSwitch_var, variable = self.bloodSwitch_var, onvalue = "CW", offvalue = "CCW")
        self.blood_switch.grid(row=4,column=0,columnspan=2, padx=(50,0), pady=10, sticky="")
        
        # START STOP BUTTON
        self.start_btn=customtkinter.CTkButton(master=self.start_frame,text = 'START ALL', command = self.startSubmit, font=('arial',20, 'bold'), height=75, width=220)
        self.start_btn.grid(row=0,column=0,columnspan=2, padx=(10,10), pady=10, sticky="")
        
        self.stop_btn=customtkinter.CTkButton(master=self.start_frame,text = 'STOP ALL', command = self.stopSubmit, font=('arial',20, 'bold'), height=75, fg_color='red', width=220)
        self.stop_btn.grid(row=1,column=0,columnspan=2, padx=(10,10), pady=10, sticky="")
        
        self.csv_entry = customtkinter.CTkEntry(master=self.start_frame, placeholder_text="filename", font=('arial',20,'normal'), width=150)
        self.csv_entry.grid(row=3,column=1,columnspan=1, padx=(0,10), pady=10, sticky="")
        self.osk = Keyboard(self, self.csv_entry)
        
        self.csv_label = customtkinter.CTkLabel(master=self.start_frame,text = 'FILE:', font=('arial',20, 'bold'))
        self.csv_label.grid(row=3,column=0, columnspan=1, padx=(10,0), pady=10, sticky="")
        
        self.calibrate_btn=customtkinter.CTkButton(master=self.start_frame,text = 'CALIBRATE', command = self.calibrate, font=('arial',20, 'bold'), height=75, fg_color='green', width=220)
        self.calibrate_btn.grid(row=2,column=0,columnspan=2, padx=(10,10), pady=10, sticky="")

        self.save_btn=customtkinter.CTkButton(master=self.start_frame,text = 'SAVE', command = self.populateCSV, font=('arial',20, 'bold'), height=75, fg_color='orange', width=220)
        self.save_btn.grid(row=4,column=0,columnspan=2, padx=(10,10), pady=10, sticky="")
        
        # PRESSURE READINGS
        self.pre_label = customtkinter.CTkLabel(master=self.readings_frame,text = 'PRE: ', font=('arial',20, 'bold'))
        self.pre_label.grid(row=0,column=0, columnspan=1, padx=(10,0), pady=10, sticky="")
        
        self.pre_val_label = customtkinter.CTkLabel(master=self.readings_frame,textvariable = self.pre_val, font=('arial',20, 'bold'), text_color="green")
        self.pre_val_label.grid(row=0,column=1, columnspan=1, padx=(0,10), pady=10, sticky="")
        
        self.mid_label = customtkinter.CTkLabel(master=self.readings_frame,text = 'MID: ', font=('arial',20, 'bold'))
        self.mid_label.grid(row=1,column=0, columnspan=1, padx=(10,0), pady=10, sticky="")
        
        self.mid_val_label = customtkinter.CTkLabel(master=self.readings_frame,textvariable = self.mid_val, font=('arial',20, 'bold'), text_color="blue")
        self.mid_val_label.grid(row=1,column=1, columnspan=1, padx=(0,10), pady=10, sticky="")
        
        self.post_label = customtkinter.CTkLabel(master=self.readings_frame,text = 'POST:   ', font=('arial',20, 'bold'))
        self.post_label.grid(row=2,column=0, columnspan=1, padx=(10,0), pady=10, sticky="")
        
        self.post_val_label = customtkinter.CTkLabel(master=self.readings_frame,textvariable = self.post_val, font=('arial',20, 'bold'), text_color="orange")
        self.post_val_label.grid(row=2,column=1, columnspan=1, padx=(0,10), pady=10, sticky="")

        #FLOW SENSOR READINGS
        self.flow_label = customtkinter.CTkLabel(master=self.flow_frame,text = 'FLOW: ', font=('arial',20, 'bold'))
        self.flow_label.grid(row=0,column=0, columnspan=1, padx=(10,0), pady=10, sticky="")
        
        self.flow_val_label = customtkinter.CTkLabel(master=self.flow_frame,textvariable = self.flow_val, font=('arial',20, 'bold'), text_color="green")
        self.flow_val_label.grid(row=0,column=1, columnspan=1, padx=(0,10), pady=10, sticky="")
    
    def send_motor_command(self):
        while self.running:
            self.motor_command = self.motor_queue.get()
            if self.motor_command:
                arduino.write(self.motor_command)
                #arduino.flush()
                self.motor_queue.task_done()

    def read_sensor_data(self):
        while self.running:
            with self.stm32_lock:
            #with Serial("COM6", 115200, timeout=1) as ser: 
                # Send a request for data
            #arduino.write(b"5000000000000")  # Ensure newline character for proper termination
                self.message = "5000000000000"
                arduino.write(self.message.encode())
                #arduino.flush()
                
                # Wait for a response
                time.sleep(0.3)  # Allow time for Pico to respond
                #self.response = ser.readline().decode('utf-8').strip()  # Read and decode the response
                self.response = arduino.read(12)
                self.readings[0] = int.from_bytes(self.response[0:4], byteorder='big')
                self.readings[1] = int.from_bytes(self.response[4:8], byteorder='big')
                self.readings[2] = int.from_bytes(self.response[8:12], byteorder='big')
                #self.readings=self.response.split(",")

                self.data_queue.put(('transducers',self.readings))
    
    def calculate_crc(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    def calculate_rms(self, data):
        return np.sqrt(np.mean(np.square(data)))

    def read_sonotec_data(self):
        while self.running:
            with self.flow_lock:
                try:
                    with Serial("COM7", 38400,bytesize=serial.EIGHTBITS,parity=serial.PARITY_EVEN,stopbits=serial.STOPBITS_ONE, timeout=1) as ser2: 
                        # Send a request for data
                        ser2.write(self.command)
                        ser2.flush()
                        # Wait for a response (sensor response times may vary; adjust if needed)
                        time.sleep(0.2)
                        self.response2=ser2.read(15)
                        if len(self.response2) >= 5:
                            # Validate CRC
                            data = self.response2[:-2]
                            received_crc = int.from_bytes(self.response2[-2:], byteorder='little')
                            calculated_crc = self.calculate_crc(data)
                            if received_crc != calculated_crc:
                                raise ValueError("CRC mismatch - Data corrupted!")
                            
                            # Extract data bytes and decode flow
                            data_bytes = self.response2[5:9]  # Adjust indices based on protocol
                            flow_value = struct.unpack('>f', data_bytes)[0]  # Use '<f' if Little Endian
                            
                            # Apply noise threshold
                            if abs(flow_value) < 1e-3:
                                flow_value = 0.0
                            
                            #print(f"Flow: {moving_avg2.add(flow_value)} mL/min")
                            #print(f"Zero Adjust: {adjust_value}")
                            #print(f"Moving Average: {self.moving_avg.add((flow_value-120)/15.36)} mL/min")-
                            self.data_buffer.append(flow_value/17.126)
                            if(len(self.data_buffer)>self.buffer_length):
                                self.data_buffer.pop(0)
                            if(len(self.data_buffer)>0):
                                self.flow = max(self.data_buffer)
                            else:
                                self.flow=0
                                self.data_buffer.append(flow_value)
                            #self.flow=round(self.moving_avg.add((abs(flow_value)-120)/15.05), 3) #add some code to make values like 8 zero 
                        else:
                            raise ValueError("Incomplete or no response received")
                        #self.response = ser2.read(ser2.in_waiting or 1)  # Read all available bytes
                        #self.hex_response = self.response.hex()[12:14]
                        #self.decimal_response = int(self.hex_response, 16)
                        
                        #self.data_queue.put(('sonotec',self.moving_avg.add(self.decimal_response)))
                    
                        self.data_queue.put(('sonotec',round(abs(self.flow), 3)))
                except serial.SerialException as e:
                    print(f"Connection failed: {e}")
                    time.sleep(5)
                except Exception as e:
                    print(f"Unnexpected error: {e}")
                    time.sleep(5)

    # updates the plot
    def update(self, data):
        # add new data to the 
        if not self.data_queue.empty():
            sensor, readings = self.data_queue.get()
            #print(readings)
            if sensor=='transducers':
                if readings[0] == "":
                    pass
                else:
                    self.reading=int(readings[0])
                    self.reading2=int(readings[1])
                    self.reading3=int(readings[2])

                    if (self.reading!=False or self.reading!=None):# and self.reading<16000000:
                        if self.reading > 16770000:
                            self.reading = self.reading - 16770000
                        self.reading = self.reading*self.hx_cal+self.calibration_factor1
                        self.plotbuffer = np.append(self.plotbuffer, self.reading)
                        self.plotbuffer = self.plotbuffer[-500:]

                    if (self.reading2!=False or self.reading2!=None):# and self.reading2<16000000:
                        self.reading2=0 #temporary
                        if self.reading2 > 16770000:
                            self.reading2 = self.reading2 - 16770000
                        self.reading2 = self.reading2*self.hx2_cal+self.calibration_factor2
                        self.plotbuffer2 = np.append(self.plotbuffer2, self.reading2)
                        self.plotbuffer2 = self.plotbuffer2[-500:]
            
                    if (self.reading3!=False or self.reading3!=None):# and self.reading3<16000000:
                        if self.reading3 > 16770000:
                            self.reading3 = self.reading3 - 16770000
                        self.reading3 = self.reading3*self.hx3_cal+self.calibration_factor3
                        self.plotbuffer3 = np.append(self.plotbuffer3, self.reading3)
                        self.plotbuffer3 = self.plotbuffer3[-500:]
            
                    self.timeStamp=datetime.now()
                    self.timeNow=time.time()
                    if self.timeNow>(self.timeThen+1):
                        self.df.loc[len(self.df.index)] = [self.timeStamp, self.plotbuffer[-1], self.plotbuffer2[-1], self.plotbuffer3[-1]] 
                        self.timeThen=time.time()
            
                    if self.timeNow>(self.timeFive+3):
                        if self.reading<16770000:
                            self.pre_str = str(round(self.reading,2))
                            self.pre_val.set(self.pre_str + " mmHg")
                        if self.reading2<16770000:
                            self.mid_str = str(round(self.reading2,2))
                            self.mid_val.set(self.mid_str + " mmHg")
                        if self.reading3<16770000:
                            self.post_str = str(round(self.reading3,2))
                            self.post_val.set(self.post_str + " mmHg")
                        
                        self.timeFive=time.time()
            elif sensor=='sonotec':
                self.flow_val.set(str(readings) + " mL/min")
            self.data_queue.task_done()

        self.line.set_ydata(self.plotbuffer)
        self.line2.set_ydata(self.plotbuffer2)
        self.line3.set_ydata(self.plotbuffer3)
        self.ax.relim()
        self.ax.autoscale_view()
        return self.line,self.line2,self.line3,
    
    def d1Submit(self):
        self.after(200, lambda: self.d1_submit_btn.configure(state="normal"))
        self.motorID="0"
        self.d1Speed_var = self.d1_entry.get()
        if(len(self.d1Speed_var)==0):
           self.d1Speed_var="000"
        elif(len(self.d1Speed_var)==1):
           self.d1Speed_var="00"+self.d1Speed_var
        elif(len(self.d1Speed_var)==2):
           self.d1Speed_var="0"+self.d1Speed_var
        
        if(self.d1Switch_var.get()=="CW"):
            self.d1Direction="1"
        elif(self.d1Switch_var.get()=="CCW"):
            self.d1Direction="0"
        self.arduino_input=self.motorID+self.d1Speed_var+self.d1Direction+"00000000"
        self.motor_queue.put(bytes(self.arduino_input, 'utf-8'))
        
    def d2Submit(self):
        self.after(200, lambda: self.d2_submit_btn.configure(state="normal"))
        self.motorID="1"
        self.d2Speed_var = self.d2_entry.get()
        if(len(self.d2Speed_var)==0):
           self.d2Speed_var="000"
        elif(len(self.d2Speed_var)==1):
           self.d2Speed_var="00"+self.d2Speed_var
        elif(len(self.d2Speed_var)==2):
           self.d2Speed_var="0"+self.d2Speed_var
        
        if(self.d2Switch_var.get()=="CW"):
            self.d2Direction="1"
        elif(self.d2Switch_var.get()=="CCW"):
            self.d2Direction="0"
        self.arduino_input=self.motorID+self.d2Speed_var+self.d2Direction+"00000000"
        self.motor_queue.put(bytes(self.arduino_input, 'utf-8'))
        
    def repSubmit(self):
        self.after(200, lambda: self.rep_submit_btn.configure(state="normal"))
        # not added to system yet
        pass
    def bloodSubmit(self):
        self.after(200, lambda: self.blood_submit_btn.configure(state="normal"))
        self.motorID="2"
        self.bloodSpeed_var = self.blood_entry.get()
        if(len(self.bloodSpeed_var)==0):
           self.bloodSpeed_var="000"
        elif(len(self.bloodSpeed_var)==1):
           self.bloodSpeed_var="00"+self.bloodSpeed_var
        elif(len(self.bloodSpeed_var)==2):
           self.bloodSpeed_var="0"+self.bloodSpeed_var
        
        if(self.bloodSwitch_var.get()=="CW"):
            self.bloodDirection="1"
        elif(self.bloodSwitch_var.get()=="CCW"):
            self.bloodDirection="0"
        self.arduino_input=self.motorID+self.bloodSpeed_var+self.bloodDirection+"00000000"
        self.motor_queue.put(bytes(self.arduino_input, 'utf-8'))
        #arduino.write(bytes(self.arduino_input, 'utf-8'))
        #time.sleep(0.25)
    
    def d1Stop(self):
        self.after(200, lambda: self.d1_stop_btn.configure(state="normal"))
        self.num="0000000000000"
        self.motor_queue.put(bytes(self.num, 'utf-8'))
        #arduino.write(bytes(self.num, 'utf-8'))
        #time.sleep(0.25)
    def d2Stop(self):
        self.after(200, lambda: self.d2_stop_btn.configure(state="normal"))
        self.num="1000000000000"
        self.motor_queue.put(bytes(self.num, 'utf-8'))
        #arduino.write(bytes(self.num, 'utf-8'))
        #time.sleep(0.25)
    def repStop(self):
        self.after(200, lambda: self.rep_stop_btn.configure(state="normal"))
        # not added to system yet
        pass
    def bloodStop(self):
        self.after(200, lambda: self.blood_stop_btn.configure(state="normal"))
        self.num="2000000000000"
        self.motor_queue.put(bytes(self.num, 'utf-8'))
        #arduino.write(bytes(self.num, 'utf-8'))
        #time.sleep(0.25)
    
    def startSubmit(self):
        self.after(200, lambda: self.start_btn.configure(state="normal"))
        self.motorID="4"
        self.d1Speed_var = self.d1_entry.get()
        if(len(self.d1Speed_var)==0):
           self.d1Speed_var="000"
        elif(len(self.d1Speed_var)==1):
           self.d1Speed_var="00"+self.d1Speed_var
        elif(len(self.d1Speed_var)==2):
           self.d1Speed_var="0"+self.d1Speed_var
        
        if(self.d1Switch_var.get()=="CW"):
            self.d1Direction="1"
        elif(self.d1Switch_var.get()=="CCW"):
            self.d1Direction="0"

        self.d2Speed_var = self.d2_entry.get()
        if(len(self.d2Speed_var)==0):
           self.d2Speed_var="000"
        elif(len(self.d2Speed_var)==1):
           self.d2Speed_var="00"+self.d2Speed_var
        elif(len(self.d2Speed_var)==2):
           self.d2Speed_var="0"+self.d2Speed_var
        
        if(self.d2Switch_var.get()=="CW"):
            self.d2Direction="1"
        elif(self.d2Switch_var.get()=="CCW"):
            self.d2Direction="0"

        self.bloodSpeed_var = self.blood_entry.get()
        if(len(self.bloodSpeed_var)==0):
           self.bloodSpeed_var="000"
        elif(len(self.bloodSpeed_var)==1):
           self.bloodSpeed_var="00"+self.bloodSpeed_var
        elif(len(self.bloodSpeed_var)==2):
           self.bloodSpeed_var="0"+self.bloodSpeed_var
        
        if(self.bloodSwitch_var.get()=="CW"):
            self.bloodDirection="1"
        elif(self.bloodSwitch_var.get()=="CCW"):
            self.bloodDirection="0"

        self.arduino_input=self.motorID+self.d1Speed_var+self.d1Direction+self.d2Speed_var+self.d2Direction+self.bloodSpeed_var+self.bloodDirection
        self.motor_queue.put(bytes(self.arduino_input, 'utf-8'))
        #arduino.write(bytes(self.arduino_input, 'utf-8'))
        #time.sleep(0.25)
        
    def stopSubmit(self):
        self.after(200, lambda: self.stop_btn.configure(state="normal"))
        self.num="3000000000000"
        self.motor_queue.put(bytes(self.num, 'utf-8'))
        #arduino.write(bytes(self.num, 'utf-8'))
        #time.sleep(0.25)
        
    def populateCSV(self):
        self.after(200, lambda: self.save_btn.configure(state="normal"))
        self.file_name=self.csv_title.get()
        self.file_name+=".csv"
        self.df.to_csv(self.file_name, index=False)
        
    def calibrate(self):
        self.after(200, lambda: self.calibrate_btn.configure(state="normal"))

        while not self.data_queue.empty():
            sensor, readings = self.data_queue.get()
            if sensor=='transducers':
                if readings[0] == "":
                    pass
                else:
                    self.reading=readings[0]
                    self.reading2=readings[1]
                    self.reading3=readings[2]

                    if self.reading!=False or self.reading!=None:
                        self.reading=int(self.readings[0])
                        if self.reading > 16000000:
                            self.reading = self.reading - 16000000

                    if self.reading2!=False or self.reading2!=None:
                        self.reading2=int(self.readings[1])
                        self.reading2=0 #temporary
                        if self.reading2 > 16000000:
                            self.reading2 = self.reading2 - 16000000
            
                    if self.reading3!=False or self.reading3!=None:
                        self.reading3=int(self.readings[2])
                        if self.reading3 > 16000000:
                            self.reading3 = self.reading3 - 16000000

                    self.calibration_factor1=0-self.reading*self.hx_cal
                    self.calibration_factor2=0-self.reading2*self.hx2_cal
                    self.calibration_factor3=0-self.reading3*self.hx3_cal
    
    def on_click(self, event):
        if not isinstance(event.widget, tk.Entry):
            self.focus()

    def confirm(self):
        self.running=False
        ans=askyesno(title='Exit', message='Do you want to exit?')
        if ans:
            self.running=False
            self.sensor_thread.join()
            #self.sonotec_thread.join()
            #self.motor_thread.join()
            #self.destroy()
            self.withdraw()
            self.quit()
        else:
            self.running=True

if __name__ == "__main__":
    app = App()
    app.after(20, lambda: app.wm_state('zoomed'))
    app.protocol("WM_DELETE_WINDOW", app.confirm)
    app.mainloop()
