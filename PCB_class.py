#Code created by David Encarnacion
#Last Updated: 11/4/2024 10:14

import time
from ssd1351 import Display
from machine import Pin, SPI, reset
from Camera import *
from easy_comms_micro import Easy_comms
import os
import math

class PCB:
    def __init__(self):
        # Initialize GPIO3 as an output pin
        self.pin3 = Pin(12, Pin.OUT)
        # Set GPIO3 to high
#         pin3.value(1)
        self.pin3.value(0)
        self.spi_display = SPI(0, baudrate=14500000, sck=Pin(18), mosi=Pin(19))
        self.display = Display(self.spi_display, dc=Pin(14), cs=Pin(21), rst=Pin(7))
        
        self.spi_camera = SPI(1, sck=Pin(10), miso=Pin(8), mosi=Pin(11), baudrate=8000000)
        self.cs = Pin(9, Pin.OUT)
        self.onboard_LED = Pin(25, Pin.OUT)
        self.cam = Camera(self.spi_camera, self.cs)
        
        #self.pin3.value(1)
        self.com1 = Easy_comms(uart_id=1, baud_rate=9600)
#         self.com1.start()
        
        
        self.last_num = self.get_last_num()
    
    def get_last_num(self):
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
        sleep_ms(700)
        #self.pin3(0)
        sleep_ms(700)
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
        #self.pin3(1)

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
        num_Chunks = math.ceil(len(jpg_bytes) / chunksize)
        
        print("Number of Chunks: ", num_Chunks)

        # Step 1: Send the num_Chunks value to the FCB before starting to send the actual chunks
        num_chunks_message = str(num_Chunks)
        self.com1.overhead_send(num_chunks_message)
        print(f"Sent num_Chunks: {num_Chunks}")
        
#         # Step 2: Wait for acknowledgment from FCB that it’s ready to receive data
#         acknowledgment = self.com1.wait_for_acknowledgment()  # Assuming wait_for_acknowledgment is implemented
#         if not acknowledgment:
#             print("Error: No acknowledgment received. Aborting data transfer.")
#             return
        if self.com1.overhead_read() == "acknowledge:
            # Step 3: Start sending the actual chunks
            for i in range(0, num_Chunks):  # Loop from 0 to num_Chunks - 1
                print("Chunk #", i)
                self.onboard_LED.off()
                
                # Create the chunk for the current chunk index
                chunk = jpg_bytes[i * chunksize:(i + 1) * chunksize]
                chunknum = i.to_bytes(2, 'little')  # Chunk number as 2 bytes
                chunk = chunknum + chunk
                
                # Add CRC tag to the chunk
                crctagb = self.com1.calculate_crc16(chunk)
                chunk += crctagb.to_bytes(2, 'little')
                
                self.onboard_LED.on()
                self.com1.send_bytes(chunk)  # Send chunk
                
                print(f"Sent chunk of length {len(chunk)} bytes")
                
                # Retry mechanism for error handling
                retry_limit = 5  # Set a limit on retries to avoid infinite loops
                retries = 0
                while (recievecheck := self.com1.overhead_read()) == "Chunk has an error.":
                    if retries >= retry_limit:
                        print(f"Error sending chunk {i}, retry limit reached. Skipping.")
                        break
                    retries += 1
                    self.com1.send_bytes(chunk)  # Resend the chunk if error detected
                    print(f"Retrying chunk {i}, attempt {retries}")
                
                self.onboard_LED.off()

            print("All requested chunks sent successfully.")

