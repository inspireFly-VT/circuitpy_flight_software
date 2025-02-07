# This code is for the "a" side of the communications between the boards
# Start this code first and then start b's code afterwards
# Once b has started you may now input commands
from easy_comms_circuit import EasyComms
import time
import board
import busio
import storage

# Initialize communication
com1 = EasyComms(board.GP0, board.GP1, baud_rate=115200)
com1.start()
received_bytes = b""

# Remount the filesystem to be writable
# storage.remount("/", readonly=False)

# Start interaction loop with b:
while True:
    # Enter Inputs
    command = 'chunk'#input('\n~> Input "photodata" to see all the photos data, "chunk" to gather chunks, or say "finished" to end communication: ')

    time.sleep(2)
    
#     # End communications
#     if command.lower() == 'finished':
#         request = "finished"
#         com1.overhead_send(request)
#         print('Ended communications.')
#         break

#     # Read default overhead message for photos data
#     if command.lower() == 'photodata':
#         request = "photodata"
#         com1.overhead_send(request)
#         message = ""
#         message = com1.overhead_read()
#         print(f"Look for: {message.strip('\n')}")

#     # Send over chunks
    if command.lower() == 'chunk':
        request = "chunk"
        com1.overhead_send(request)  # tell b you are requesting for chunks
        lowerchunk = '0'#input('Chunk lower bound: ')  # input lower bound
        upperchunk = '50'#input('Chunk upper bound: ')  # input upper bound
        time.sleep(2)
        if lowerchunk.isdigit() and upperchunk.isdigit() and int(lowerchunk) <= int(upperchunk):
            message = lowerchunk + ' ' + upperchunk  # compile lower and upper bounds in message to send
            com1.overhead_send(message)
            print(message)
            ##
            jpg_bytes, count = com1.read_bytes(lowerchunk, upperchunk)  # call read_bytes to read chunks from b
            print('Number of chunks received = ', count)
            print('Number of bytes received = ', len(jpg_bytes))
            print(jpg_bytes)
            # Assemble chunks into photo file
            if jpg_bytes is not None:
                try:
                    with open("received2.jpg", "wb") as file:
                        file.write(jpg_bytes)
                        print("JPG file successfully created!")
                except OSError as e:
                    print(f"Failed to write file: {e}")    
        else:
            # If lower and upper bound inputs are incorrect
            print('Incorrect input, only accepted whole numbers.')
            message = "Wrong"
            com1.overhead_send(message)
            
    command = 'finished'#input('\n~> Input "photodata" to see all the photos data, "chunk" to gather chunks, or say "finished" to end communication: ')
    time.sleep(2)
    
    if command.lower() == 'finished':
        request = "finished"
        com1.overhead_send(request)
        print('Ended communications.')
        break
    
    else:
        print('Wrong command entered, try again.')

