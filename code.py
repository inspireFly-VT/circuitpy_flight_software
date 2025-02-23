'''
In this method the PyCubed will wait a pre-allotted loiter time before proceeding to execute
main. This loiter time is to allow for a keyboard interupt if needed. 

Authors: Nicole Maggard and Michael Pham
'''

import time
import microcontroller

try:
        import main

except Exception as e:    
        print(e)
        time.sleep(10)

while True:
    try:
        import main

    except Exception as e:    
        print(e)
        print("Running again in 10 seconds")
        time.sleep(10)
    #microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
    #microcontroller.reset()

# '''
# vvvCode for UART Commsvvv - Dave :p
# '''
# # main.py
# from easy_comms_circuit import EasyComms
# import board
# import time
# from FCB_class import FCBCommunicator
# 
# # Initialize communication and FCBCommunicator
# com1 = EasyComms(board.TX, board.RX, baud_rate=9600)
# com1.start()
# fcb_comm = FCBCommunicator(com1)
# 
# # Start interaction loop
# while True:
#     overhead_command = com1.overhead_read()
# 
#     # Set the command
#     command = 'chunk'
#     time.sleep(2)
# 
#     if command.lower() == 'chunk':
#         fcb_comm.send_command("chunk")
#         
#         if fcb_comm.wait_for_acknowledgment():
#             jpg_bytes = fcb_comm.send_chunk_request()
#             
#             if jpg_bytes is not None:
#                 fcb_comm.save_image(jpg_bytes)
#                 
#     command = 'end'
#     
#     if command.lower() == 'end':
#         fcb_comm.end_communication()
#         time.sleep(3)
#         break
# 
#     else:
#         print("Wrong command entered, try again.")
