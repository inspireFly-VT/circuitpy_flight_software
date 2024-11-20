# SPDX-FileCopyrightText: 2024 Ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of sending and recieving data with the RFM9x or RFM69 radios.
# Author: Jerry Needell

import board
import busio
import digitalio
import time
import math
from adafruit_rfm import rfm9xfsk
from satellite_send_method_2 import DataToAX25_method2

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.SPI0_CS0)
RESET = digitalio.DigitalInOut(board.RF1_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SPI0_SCK, MOSI=board.SPI0_MOSI, MISO=board.SPI0_MISO)

# Initialze RFM radio
# uncommnet the desired import and rfm initialization depending on the radio boards being used

# Use rfm9x for two RFM9x radios using LoRa

# from adafruit_rfm import rfm9x

# rfm = rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Use rfm9xfsk for two RFM9x radios or RFM9x to RFM69 using FSK



rfm = rfm9xfsk.RFM9xFSK(spi, CS, RESET, RADIO_FREQ_MHZ)

# Use rfm69 for two RFM69 radios using FSK

# from adafruit_rfm import rfm69

# rfm = rfm69.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)

# For RFM69 only: Optionally set an encryption key (16 byte AES key). MUST match both
# on the transmitter and receiver (or be set to None to disable/the default).
# rfm.encryption_key = None
# rfm.encryption_key = (
#    b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"
# )

# for OOK on RFM69 or RFM9xFSK
# rfm.modulation_type = 1

# Send a packet.  Note you can only send a packet containing up to 60 bytes for an RFM69
# and 252 bytes for an RFM9x.
# This is a limitation of the radio packet size, so if you need to send larger
# amounts of data you will need to break it into smaller send calls.  Each send
# call will wait for the previous one to finish before continuing.

# jpg_file = open(r"Camera Function Test.jpg",'rb')

# This opens the image file and reads it into a list of bytes
jpg_file = open(r"blue.jpg", 'rb')
jpg_bytes = jpg_file.read()
print(type(jpg_bytes))
print(len(jpg_bytes))

# Sets up a counter and step variable to control what bytes are sent and how many are sen't
# at a time
counter = 0
step = 32

# Sets up current index to put into Ground Station data array
curr_index = 0

# This is the callsign that is used as packet source and destination bytes
callsign = "K4KDJ"
packet = None
print("Listening for send command...")
while packet is None :
    packet = rfm.receive(timeout=5.0)
    print("No send command received. Listening again...")
    
numberOfPackets = math.ceil(len(jpg_bytes) / step)
numberOfPacketsBytes = numberOfPackets.to_bytes(2, "big")
frame = DataToAX25_method2.encode_ax25_frame(numberOfPacketsBytes, callsign, callsign, b'\x00', 0)
rfm.send(frame)

# This loops through every [step] bytes in jpg_bytes and sends them to the ground station


while(counter < len(jpg_bytes)):
    packetIndex = counter // step
    # Encodes the bytes being send into AX25 packet form
    frame = DataToAX25_method2.encode_ax25_frame(jpg_bytes[counter : counter + step], callsign, callsign, b'\x00', packetIndex)
    
    # Sends the packeted data and prints out the status of the overal sending to the terminal
    rfm.send(frame)
    print(f"Packet {packetIndex} sent: ",frame)
    print(counter, " bytes sent, ", len(jpg_bytes) - counter, " bytes left.")
    
    # Checks that the groundstation received the sent bytes. If the bytes were received the ground station
    # sends back a message to acknowledge that the bytes were received, then counter is increased to send
    # the next set of bytes
    #packet = rfm.receive(timeout=0.5)
    #if packet is not None:
      #  counter += step
    counter += step
    
    time.sleep(0.33)

print("All packets sent")
 
# Listens for the corrupted packets from Ground Station
callsign = "K4KDJ"
packet = None
print("Listening for corrupted packets command...")
while packet is None :
    packet = rfm.receive(timeout=5.0)
    print("No corrupted packets command received. Listening again...")

corruptedPacketList = packet
operatingMode, fcsCorrect, data, packetIndex = Data_To_AX25_method2.decode_ax25_frame(packet)
#corruptedPacketList = [struct.unpack('h', byte_data[i:i+2])[0] for i in range(0, len(byte_data), 2)]
numCorruptedPackets = len(corruptedPacketList)

for index in corruptedPacketList:
    counter = index * step
    frame = DataToAX25_method2.encode_ax25_frame(jpg_bytes[counter : counter + step], callsign, callsign, b'\x00', index)
    
    rfm.send(frame)
    print(f"Packet {index} sent: ",frame)
    print("Packet", index, " sent, ", numCorruptedPackets, " packets left to send")
    
    numCorruptedPackets = numCorruptedPackets - 1

# # Working image transfer commented out to test packet transfers
# while(counter < len(jpg_bytes)):
#     rfm.send(jpg_bytes[counter:counter+step])
#     print("sent: ",jpg_bytes[counter:counter+step])
#     print(counter, " bytes sent, ", len(jpg_bytes) - counter, " bytes left.")
#     packet = rfm.receive(timeout=0.5)
#     if packet is not None:
#         counter += step


# while(counter < len(jpg_bytes)):
#     rfm.send(counter.to_bytes(2,"big"))
#     print("sent",counter)
#     packet = rfm.receive(timeout=0.5)
#     if packet is not None:
#         counter += 1


# Original testing code commented out to test image byte sending     
# while(True):
#     rfm.send(bytes("Hello!\r\n", "utf-8"))
#     print("Sent Hello World message!")
#     time.sleep(1);

# Wait to receive packets.
# print("Waiting for packets...")

# while True:
#     # Optionally change the receive timeout from its default of 0.5 seconds:
#     # packet = rfm9x.receive(timeout=5.0)
#     packet = rfm.receive(timeout=5.0)
#     # If no packet was received during the timeout then None is returned.
#     if packet is None:
#         # Packet has not been received
#         rfm.send("not received")
#         print("Received nothing! Listening again...")
#     else:
#         # Received a packet!
#         # Print out the raw bytes of the packet:
#         rfm.send("received")
#         print(f"Received (raw bytes): {packet}")
#         # And decode to ASCII text and print it too.  Note that you always
#         # receive raw bytes and need to convert to a text format like ASCII
#         # if you intend to do string processing on your data.  Make sure the
#         # sending side is sending ASCII data before you try to decode!
#         try:
#             packet_text = str(packet, "ascii")
#             print(f"Received (ASCII): {packet_text}")
#         except UnicodeError:
#             print("Hex data: ", [hex(x) for x in packet])
#         # Also read the RSSI (signal strength) of the last received message and
#         # print it.
#         rssi = rfm.last_rssi
#         print(f"Received signal strength: {rssi} dB")
