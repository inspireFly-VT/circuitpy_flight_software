'''
This is the class that contains all of the functions for our CubeSat. 
We pass the cubesat object to it for the definitions and then it executes 
our will.
Authors: Nicole Maggard, Michael Pham, and Rachel Sarmiento
'''
import time
import alarm
import gc
import traceback
import random
from debugcolor import co

class functions:
    
    def send_joke(self, msg):
        #add ax25
        self.send(b'\x11'+msg)        
    def send_beacon(self):
        #add ax25
        self.send(b'\x21'+f"PM:{self.cubesat.power_mode}"+ " " + f"VB:{self.cubesat.battery_voltage}")
        
    def send_beaconP(self):
        #add ax25
        self.send(b'\x22'+ f"PM:{self.cubesat.power_mode}"+ " " + f"VB:{self.cubesat.battery_voltage}") #+ number of picture packets
    
    def send_SOH(self,msg):
        #add ax25
        self.send(b'\x25'+msg)
        
    def send_SOHP(self,msg):
        #add ax25
        self.send(b'\x26')# + state of health + number of picture packets
    
    def send_selfie(self,msg):
        #add ax25
        return
    
        

    def debug_print(self,statement):
        if self.debug:
            print(co("[Functions]" + str(statement), 'green', 'bold'))
    def __init__(self,cubesat):
        self.cubesat = cubesat
        self.debug = cubesat.debug
        self.debug_print("Initializing Functionalities")
        self.Errorcount=0
        self.facestring=[]
        self.jokes=["Hey Its pretty cold up here, did someone forget to pay the electric bill?"]
        self.last_battery_temp = 20
        #self.callsign="KQ4LFD"
        self.callsign=""
        self.state_bool=False
        self.face_data_baton = False
        self.detumble_enable_z = True
        self.detumble_enable_x = True
        self.detumble_enable_y = True
        try:
            self.cubesat.all_faces_on()
        except Exception as e:
            self.debug_print("Couldn't turn faces on: " + ''.join(traceback.format_exception(e)))
    
    '''
    Satellite Management Functions
    '''
    def battery_heater(self):
        """
        Battery Heater Function reads temperature at the end of the thermocouple and tries to 
        warm the batteries until they are roughly +4C above what the batteries should normally sit(this 
        creates a band stop in which the battery heater never turns off) The battery heater should not run
        forever, so a time based stop is implemented
        """
        try:
            try:
                import Big_Data
                a = Big_Data.AllFaces(self.debug,self.cubesat.tca)
                
                self.last_battery_temp = a.Get_Thermo_Data()
            except Exception as e:
                self.debug_print("[ERROR] couldn't get thermocouple data!" + ''.join(traceback.format_exception(e)))
                raise Exception("Thermocouple failure!")

            if self.last_battery_temp < self.cubesat.NORMAL_BATT_TEMP:
                end_time=0
                self.cubesat.heater_on()
                while self.last_battery_temp < self.cubesat.NORMAL_BATT_TEMP+4 and end_time<5:
                    time.sleep(1)
                    self.last_battery_temp = a.Get_Thermo_Data()
                    end_time+=1
                    self.debug_print(str(f"Heater has been on for {end_time} seconds and the battery temp is {self.last_battery_temp}C"))
                self.cubesat.heater_off()
                del a
                del Big_Data
                return True
            else: 
                self.debug_print("Battery is already warm enough")
                del a
                del Big_Data
                return False
        except Exception as e:
            self.cubesat.heater_off()
            self.debug_print("Error Initiating Battery Heater" + ''.join(traceback.format_exception(e)))
            del a
            del Big_Data
            return False
        finally:
            self.cubesat.heater_off()
    
    def current_check(self):
        return self.cubesat.current_draw

    '''
    Radio Functions
    '''  
    def send(self,msg):
        """Calls the RFM9x to send a message. Currently only sends with default settings.
        
        Args:
            msg (String,Byte Array): Pass the String or Byte Array to be sent. 
        """
        import Field
        self.field = Field.Field(self.cubesat,self.debug)
        message=f"{self.callsign} " + str(msg) + f" {self.callsign}"
        self.field.Beacon(message)
#         if self.cubesat.f_fsk:
#             self.cubesat.radio1.cw(message)
        if self.cubesat.is_licensed:
            self.debug_print(f"Sent Packet: " + message)
        else:
            self.debug_print("Failed to send packet")
        del self.field
        del Field

    def beacon(self):
        """Calls the RFM9x to send a beacon. """
        import Field
        try:
            lora_beacon = f"{self.callsign} Hello I am Yearling^2! I am in: " + str(self.cubesat.power_mode) +" power mode. V_Batt = " + str(self.cubesat.battery_voltage) + f"V. IHBPFJASTMNE! {self.callsign}"
        except Exception as e:
            self.debug_print("Error with obtaining power data: " + ''.join(traceback.format_exception(e)))
            lora_beacon = f"{self.callsign} Hello I am Yearling^2! I am in: " + "an unidentified" +" power mode. V_Batt = " + "Unknown" + f". IHBPFJASTMNE! {self.callsign}"

        self.field = Field.Field(self.cubesat,self.debug)
        self.field.Beacon(lora_beacon)
#         if self.cubesat.f_fsk:
#             self.cubesat.radio1.cw(lora_beacon)
        del self.field
        del Field
    
    def joke(self):
        self.send(random.choice(self.jokes))
        
    def format_state_of_health(self, hardware):
        to_return = ""
        for key, value in hardware.items():
            to_return = to_return + key + "="
            if value:
                to_return += "1"
            else:
                to_return += "0"

            if len(to_return) > 245:
                return to_return

        return to_return
        

    def state_of_health(self):
        import Field
        self.state_list=[]
        #list of state information 
        try:
            self.state_list = [
                f"PM:{self.cubesat.power_mode}",
                f"VB:{self.cubesat.battery_voltage}",
                f"ID:{self.cubesat.current_draw}",
                f"IC:{self.cubesat.charge_current}",
                f"VS:{self.cubesat.system_voltage}",
                f"UT:{self.cubesat.uptime}",
                f"BN:{self.cubesat.c_boot}",
                f"MT:{self.cubesat.micro.cpu.temperature}",
                f"RT:{self.cubesat.radio1.former_temperature}",
                f"AT:{self.cubesat.internal_temperature}",
                f"BT:{self.last_battery_temp}",
                f"AB:{int(self.cubesat.burned)}",
                f"BO:{int(self.cubesat.f_brownout)}",
                f"FK:{int(self.cubesat.f_fsk)}"
            ]
        except Exception as e:
            self.debug_print("Couldn't aquire data for the state of health: " + ''.join(traceback.format_exception(e)))
        
        self.field = Field.Field(self.cubesat,self.debug)
        if not self.state_bool:
            self.field.Beacon(f"{self.callsign} Yearling^2 State of Health 1/2" + str(self.format_state_of_health(self.cubesat.hardware))+ f"{self.callsign}")
#             if self.cubesat.f_fsk:
#                 self.cubesat.radio1.cw(f"{self.callsign} Yearling^2 State of Health 1/2" + str(self.state_list)+ f"{self.callsign}")
            self.state_bool=True
        else:
            self.field.Beacon(f"{self.callsign} YSOH 2/2" + str(self.cubesat.hardware) +f"{self.callsign}")
#             if self.cubesat.f_fsk:
#                 self.cubesat.radio1.cw(f"{self.callsign} YSOH 2/2" + str(self.cubesat.hardware) +f"{self.callsign}")
            self.state_bool=False
        del self.field
        del Field

    def send_face(self):
        """Calls the data transmit function from the field class
        """
        import Field
        self.field = Field.Field(self.cubesat,self.debug)
        self.debug_print("Sending Face Data")
        self.field.Beacon(f'{self.callsign} Y-: {self.facestring[0]} Y+: {self.facestring[1]} X-: {self.facestring[2]} X+: {self.facestring[3]}  Z-: {self.facestring[4]} {self.callsign}')
#         if self.cubesat.f_fsk:
#                 self.cubesat.radio1.cw(f'{self.callsign} Y-: {self.facestring[0]} Y+: {self.facestring[1]} X-: {self.facestring[2]} X+: {self.facestring[3]}  Z-: {self.facestring[4]} {self.callsign}')
        del self.field
        del Field
    
    def listen(self):
        import cdh
        #This just passes the message through. Maybe add more functionality later. 
        try:
            self.debug_print("Listening")
            # Change timeout back to 10
            self.cubesat.radio1.receive_timeout=10
            received = self.cubesat.radio1.receive_with_ack(keep_listening=True)
        except Exception as e:
            self.debug_print("An Error has occured while listening: " + ''.join(traceback.format_exception(e)))
            received=None

        try:
            if received is not None:
                self.debug_print("Recieved Packet: "+str(received))
                cdh.message_handler(self.cubesat,received)
                return True
        except Exception as e:
            self.debug_print("An Error has occured while handling command: " + ''.join(traceback.format_exception(e)))
        finally:
            del cdh
        
        return False
    
    def listen_joke(self):
        try:
            self.debug_print("Listening")
            self.cubesat.radio1.receive_timeout=10
            received = self.cubesat.radio1.receive(keep_listening=True)
            if received is not None and "HAHAHAHAHA!" in received:
                return True
            else:
                return False
        except Exception as e:
            self.debug_print("An Error has occured while listening: " + ''.join(traceback.format_exception(e)))
            received=None
            return False

    '''
    Big_Data Face Functions
    change to remove fet values, move to pysquared
    '''  
    def face_toggle(self,face,state):
        dutycycle = 0x0000
        if state:
            duty_cycle=0xffff
        
        if   face == "Face0": self.cubesat.Face0.duty_cycle = duty_cycle      
        elif face == "Face1": self.cubesat.Face0.duty_cycle = duty_cycle
        elif face == "Face2": self.cubesat.Face0.duty_cycle = duty_cycle      
        elif face == "Face3": self.cubesat.Face0.duty_cycle = duty_cycle           
        elif face == "Face4": self.cubesat.Face0.duty_cycle = duty_cycle          
        elif face == "Face5": self.cubesat.Face0.duty_cycle = duty_cycle
    
    def all_face_data(self):
        
        self.cubesat.all_faces_on()
        try:
            import Big_Data
            a = Big_Data.AllFaces(self.debug,self.cubesat.tca)
            
            self.facestring = a.Face_Test_All()
            
            del a
            del Big_Data
        except Exception as e:
            self.debug_print("Big_Data error" + ''.join(traceback.format_exception(e)))
        
        return self.facestring
    
    def get_imu_data(self):
        
        self.cubesat.all_faces_on()
        try:
            data=[]
            data.append(self.cubesat.IMU.acceleration)
            data.append(self.cubesat.IMU.gyro)
            data.append(self.cubesat.magnetometer.magnetic)
        except Exception as e:
            self.debug_print("Error retrieving IMU data" + ''.join(traceback.format_exception(e)))
        
        return data
    
    def OTA(self):
        # resets file system to whatever new file is received
        pass

    '''
    Logging Functions
    '''  
    def log_face_data(self,data):
        
        self.debug_print("Logging Face Data")
        try:
                self.cubesat.log("/faces.txt",data)
        except:
            try:
                self.cubesat.new_file("/faces.txt")
            except Exception as e:
                self.debug_print('SD error: ' + ''.join(traceback.format_exception(e)))
        
    def log_error_data(self,data):
        
        self.debug_print("Logging Error Data")
        try:
                self.cubesat.log("/error.txt",data)
        except:
            try:
                self.cubesat.new_file("/error.txt")
            except Exception as e:
                self.debug_print('SD error: ' + ''.join(traceback.format_exception(e)))
    
    '''
    Misc Functions
    '''  
    #Goal for torque is to make a control system 
    #that will adjust position towards Earth based on Gyro data
    def detumble(self,dur = 7, margin = 0.2, seq = 118):
        self.debug_print("Detumbling")
        self.cubesat.RGB=(255,255,255)
        self.cubesat.all_faces_on()
        try:
            import Big_Data
            a=Big_Data.AllFaces(self.debug, self.cubesat.tca)
        except Exception as e:
            self.debug_print("Error Importing Big Data: " + ''.join(traceback.format_exception(e)))

        try:
            a.sequence=52
        except Exception as e:
            self.debug_print("Error setting motor driver sequences: " + ''.join(traceback.format_exception(e)))
        
        def actuate(dipole,duration):
            #TODO figure out if there is a way to reverse direction of sequence
            if abs(dipole[0]) > 1:
                a.Face2.drive=52
                a.drvx_actuate(duration)
            if abs(dipole[1]) > 1:
                a.Face0.drive=52
                a.drvy_actuate(duration)
            if abs(dipole[2]) > 1:
                a.Face4.drive=52
                a.drvz_actuate(duration)
            
        def do_detumble():
            try:
                import detumble
                for _ in range(3):
                    data=[self.cubesat.IMU.gyro,self.cubesat.IMU.Magnetometer]
                    data[0]=list(data[0])
                    for x in range(3):
                        if data[0][x] < 0.01:
                            data[0][x]=0.0
                    data[0]=tuple(data[0])
                    dipole=detumble.magnetorquer_dipole(data[1],data[0])
                    self.debug_print("Dipole: " + str(dipole))
                    self.send("Detumbling! Gyro, Mag: " + str(data))
                    time.sleep(1)
                    actuate(dipole,dur)
            except Exception as e:
                self.debug_print("Detumble error: " + ''.join(traceback.format_exception(e)))
        try:
            self.debug_print("Attempting")
            do_detumble()
        except Exception as e:
            self.debug_print('Detumble error: ' + ''.join(traceback.format_exception(e)))
        self.cubesat.RGB=(100,100,50)
        
    
    def Short_Hybernate(self):
        self.debug_print("Short Hybernation Coming UP")
        gc.collect()
        #all should be off from cubesat powermode
        self.cubesat.all_faces_off()
        self.cubesat.enable_rf.value=False
        self.cubesat.f_softboot=True
        time.sleep(120)
        self.cubesat.all_faces_on()
        self.cubesat.enable_rf.value=True
        return True
    
    def Long_Hybernate(self):
        self.debug_print("LONG Hybernation Coming UP")
        gc.collect()
        #all should be off from cubesat powermode
        self.cubesat.all_faces_off()
        self.cubesat.enable_rf.value=False
        self.cubesat.f_softboot=True
        time.sleep(600)
        self.cubesat.all_faces_on()
        self.cubesat.enable_rf.value=True
        return True
    