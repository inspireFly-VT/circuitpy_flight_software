import board
import sys
print(dir(board))


print("")
print(sys.path)
print("")
sys.path.append("/sd")
print(sys.path)

print("")
#print("A0:", board.A0)
print("D0:", board.D0)
print("")
#print("VOLTAGE_MONITOR: ", board.VOLTAGE_MONITOR)
print("RF1_RST:", board.RF1_RST)
#print("A3: ", board.A3)
print("RF1_IO0:", board.RF1_IO0)
print("RF1_IO4:", board.RF1_IO4)
#print("GP11: ", board.GP11)
print("")
#print("GP15: ", board.GP15)