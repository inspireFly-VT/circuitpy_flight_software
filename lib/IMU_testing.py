'''
For testing the IMU on the new flight board
'''
import time
from lib.pysquared import cubesat as c
import functions
from debugcolor import co

def debug_print(statement):
    if c.debug:
        print(co("[IMU TESTING] " + str(statement), 'pink','bold'))

f = functions.functions(c)

while True:  # Magnetometer
    time.sleep(3)
    IMUdata = []
    debug_print("Getting IMU Data...")
    IMUdata = f.get_imu_data()

    #this should be in the order acceleration, gyroscope, and magnometer
    debug_print(IMUdata)
    print()



