'''
In this method the PyCubed will wait a pre-allotted loiter time before proceeding to execute
main. This loiter time is to allow for a keyboard interupt if needed. 

Authors: Nicole Maggard and Michael Pham
'''

# import time
# import microcontroller
# 
# try:
#         import main
# 
# except Exception as e:    
#         print(e)
#         time.sleep(10)

# while True:
#     try:
#         import main
# 
#     except Exception as e:    
#         print(e)
#         print("Running again in 10 seconds")
#         time.sleep(10)
    #microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
    #microcontroller.reset()

'''
vvvCode for UART Commsvvv - Dave :p
'''
# code.py (CircuitPython)
# This code is for the "a" side of the communications between the boards
# Start this code first and then start b's code afterward
# Once b has started you may now input commands
from easy_comms_circuit import EasyComms
import time
import board
import busio
import storage

# Initialize communication
com1 = EasyComms(board.TX, board.RX, baud_rate=9600)
com1.start()
received_bytes = b""  # Keep this as bytes to avoid decoding issues
storage.remount("/", readonly=False)

# Initialize counter for unique filenames
image_counter = 0

# Start interaction loop with b:
while True:
    # Check if overhead read has received 'end' command to stop sending 'chunk' requests
    overhead_command = com1.overhead_read()

    command = 'chunk'
    time.sleep(2)

    if command.lower() == 'chunk':
        request = "chunk"
        com1.overhead_send(request)
        
        # Wait for acknowledgment from PCB
        ack_received = False
        while not ack_received:
            acknowledgment = com1.overhead_read()
            if acknowledgment == 'acknowledge':
                ack_received = True
                print('Acknowledgment received, proceeding with data transfer...')
            else:
                time.sleep(1)

        lowerchunk = '0'
        upperchunk = '200'
        time.sleep(2)

        if lowerchunk.isdigit() and upperchunk.isdigit() and int(lowerchunk) <= int(upperchunk):
            message = lowerchunk + ' ' + upperchunk
            com1.overhead_send(message)
            print(message)
            
            jpg_bytes, count = com1.read_bytes(lowerchunk, upperchunk)
            print('Number of chunks received = ', count)
            print('Number of bytes received = ', len(jpg_bytes))
            
            if jpg_bytes is not None:
                try:
                    # Generate the unique filename
                    filename = f"inspireFly_Capture_{image_counter}.jpg"
                    with open(filename, "wb") as file:
                        file.write(jpg_bytes)
                        print(f"{filename} successfully created!")
                    
                    # Increment the counter for the next file
                    image_counter += 1
                    
                except OSError as e:
                    print(f"Failed to write file: {e}")
        else:
            print('Incorrect input, only accepted whole numbers.')
            message = "Wrong"
            com1.overhead_send(message)
            
    command = 'end'
    
    if command.lower() == 'end':
        # Send 'end' to acknowledge end of communication
        request = "end"
        com1.overhead_send(request)
        print('Ended communications.')
        time.sleep(3)
        #break
            
    else:
        print('Wrong command entered, try again.')
