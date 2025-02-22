# FCB_class.py
import time
import storage
import os

class FCBCommunicator:
    def __init__(self, com_instance):
        self.com = com_instance
        self.image_counter = 0
        self.last_num = self.get_last_num()

        #storage.remount("/", readonly=False)

    def send_command(self, command):
        self.com.overhead_send(command)

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
        
    def wait_for_acknowledgment(self, timeout=30):
        """
        Waits for an acknowledgment from the FCB.
        If acknowledgment is received, it proceeds with the data transfer.
        If the timeout is reached without receiving acknowledgment, it returns False.
        
        :param timeout: Time in seconds to wait before giving up (default is 30 seconds).
        :return: True if acknowledgment is received, False if timeout is reached.
        """
        start_time = time.time()
        
        while True:
            acknowledgment = self.com.overhead_read()
            
            if acknowledgment == 'acknowledge':
                print('Acknowledgment received, proceeding with data transfer...')
                return True
            
            if time.time() - start_time > timeout:
                print("Timeout reached. No acknowledgment received.")
                return False
            
            time.sleep(1)  # Wait for a while before trying again


    def send_chunk_request(self, lowerchunk='0'):
        # Dynamically get upperchunk from the PCB during runtime
        upperchunk = self.com.overhead_read()

        # Check if both chunks are valid digits and that lowerchunk is less than or equal to upperchunk
        if lowerchunk.isdigit() and upperchunk.isdigit() and int(lowerchunk) <= int(upperchunk):
            message = f"{lowerchunk} {upperchunk}"
            self.send_command(message)
            print(f"Sent request for chunks: {message}")
            time.sleep(1)
            self.send_command("acknowledge")

            try:
                # Try to read bytes from the given chunks
                jpg_bytes, count = self.com.read_bytes(lowerchunk, upperchunk)
                print(f"Number of chunks received: {count}")
                print(f"Number of bytes received: {len(jpg_bytes)}")
                return jpg_bytes
            except Exception as e:
                print(f"Error while receiving chunks: {e}")
                return None
        else:
            print("Incorrect input, only accepted whole numbers, and lowerchunk must be less than or equal to upperchunk.")
            self.send_command("Wrong")
            return None



    def save_image(self, jpg_bytes):
        filename = f"inspireFly_Capture_{self.image_counter}.jpg"
        try:
            with open(filename, "wb") as file:
                file.write(jpg_bytes)
                print(f"{filename} successfully created!")
            self.image_counter += 1
        except OSError as e:
            print(f"Failed to write file: {e}")

    def end_communication(self):
        time.sleep(3)
        self.send_command("end")
        time.sleep(3)
        print("Ended communications.")
