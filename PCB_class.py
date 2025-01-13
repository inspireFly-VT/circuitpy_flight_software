#Code created by David Encarnacion
#Last Updated: 11/4/2024 10:14

import time
from ssd1351 import Display
from machine import Pin, SPI, reset
from Camera import *
from easy_comms_micro import Easy_comms
import os

class PCB:
    def __init__(self):
        self.spi_display = SPI(0, baudrate=14500000, sck=Pin(18), mosi=Pin(19))
        self.display = Display(self.spi_display, dc=Pin(14), cs=Pin(21), rst=Pin(7))
        
        self.spi_camera = SPI(1, sck=Pin(10), miso=Pin(8), mosi=Pin(11), baudrate=8000000)
        self.cs = Pin(9, Pin.OUT)
        self.onboard_LED = Pin(25, Pin.OUT)
        self.cam = Camera(self.spi_camera, self.cs)
        
        self.com1 = Easy_comms(uart_id=1, baud_rate=9600)
        self.com1.start()
        
        
        self.last_num = self.get_last_num()
    
    def get_last_num(self):
        if(os.stat('last_num.txt')[6] == 0):
            with open('last_num.txt', 'w') as file:
                print("File was empty. Bummer...")
                file.write(str(1))
        try:
            with open('last_num.txt', 'r') as f:
                return int(f.read())
        except OSError:
            return 1

    def TakePicture(self, imageName, resolution):
            timeout_duration = 5  # Specify the timeout duration in seconds
            start_time = time.time()  # Record the start time

            self.onboard_LED.on()
            finalImageName = f"{imageName}.jpg"
            self.cam.resolution = resolution
            sleep_ms(500)
            
            # Try to capture the image and reset if it takes too long
            try:
                self.cam.capture_jpg()
            except Exception as e:
                print("Error during capture:", e)
#                 reset()

            # Check if the capture took too long
            if time.time() - start_time > timeout_duration:
                print("Picture capture timed out, resetting...")
#                 reset()  # Reset the device if it exceeded the timeout duration
            
            sleep_ms(500)
            self.cam.saveJPG(finalImageName)
            self.onboard_LED.off()
            
            # Update last number
            with open('last_num.txt', 'w') as f:
                f.write(str(self.last_num + 1))

    def TakeMultiplePictures(self, imageName, resolution, interval, count):
        self.cam.resolution = resolution
        for x in range(count):
            endImageName = f"{imageName}{self.last_num}"
            self.TakePicture(endImageName, resolution)
            sleep_ms(500)
            if x == 0:
                try:
                    os.remove(f"{endImageName}.jpg")
                except OSError:
                    print(f"Error removing file: {endImageName}.jpg")
            sleep_ms(interval)

    def display_image(self, image_path):
        self.display.draw_image(image_path, 0, 0, 128, 128)

    def communicate_with_fcb(self, jpg_bytes):
        self.com1.overhead_send('ping')
        print("Ping sent...")
        while True:
            command = self.com1.overhead_read()
            if command.lower() == 'chunk':
                print('Sending communications acknowledgment...')
                self.com1.overhead_send('acknowledge')
                print('Acknowledgment sent, commencing data transfer...')
                time.sleep(2)
                self.send_chunks(jpg_bytes)
            elif command.lower() == 'end':
                print('See you space cowboy...')
                break

    def send_chunks(self, jpg_bytes):
        chunksize = 66
        message = self.com1.overhead_read()

        if message != "Wrong" and message != "No image data received":
            a, b = map(int, message.split())
            for i in range(a, b + 1):
                print("Chunk #", i)
                self.onboard_LED.off()
                chunk = jpg_bytes[i * chunksize:(i + 1) * chunksize]
                chunknum = i.to_bytes(2, 'little')
                chunk = chunknum + chunk
                
                crctagb = self.com1.calculate_crc16(chunk)
                chunk += crctagb.to_bytes(2, 'little')
                
                self.onboard_LED.on()
                self.com1.send_bytes(chunk)
                print(len(chunk))
                while (recievecheck := self.com1.overhead_read()) == "Chunk has an error.":
                    self.com1.send_bytes(chunk)
                self.onboard_LED.off()
                
            print("All requested chunks sent successfully.")
        elif message == "No image data received":
            print("No image data received by 'a' side. Ending chunk transfer process.")
