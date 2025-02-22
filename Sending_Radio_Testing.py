
print("rfm_simpletest Ran")

import board
import busio
import digitalio
from lib import rfm9xfsk
import time

RADIO_FREQ_MHZ = 433.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.SPI0_CS0)
RESET = digitalio.DigitalInOut(board.RF1_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SPI0_SCK, MOSI=board.SPI0_MOSI, MISO=board.SPI0_MISO)
#board.SPI0_SCK,board.SPI0_MOSI,board.SPI0_MISO

rfm = rfm9xfsk.RFM9xFSK(spi, CS, RESET, RADIO_FREQ_MHZ)

rfm.modulation_type = 0


message = bytes("Hello world!", "utf-8")
simpleMessage = bytes("Hi", "utf-8")
bytesLengthMessage = bytes("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWX", "utf-8")
counter = 1

while True:
    rfm.send(bytesLengthMessage)
    print("Sent " + str(bytesLengthMessage))
    counter += 1
    time.sleep(5)
    