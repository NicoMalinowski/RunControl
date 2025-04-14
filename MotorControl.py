import serial           # import the module
import serial.tools.list_ports
from argparse import ArgumentParser
import time


# Establish communication with the PU
ports = serial.tools.list_ports.comports()        
ComPort = serial.Serial('/dev/ttyUSB1') # open COM3
ComPort.baudrate = 9600 # set Baud rate to 9600

# Define working parameters of motor and positions
MS=4
StepsFullRotation=int(360/(1.8/MS))

POS1=int((70/4)*StepsFullRotation) # (dist in mm) / (mm/rotation)* (steps in full rotation)
POS2=int(((70+115)/4)*StepsFullRotation)
POS3=int(((70+2*115)/4)*StepsFullRotation)
POS4=int(((70+3*115)/4)*StepsFullRotation)


def to_position(pos = 0):

  """Drives the motor into the wanted position

  """
  if pos == 0:
    Data="/1m30h10j4V1600L400Z{}R".format(int(POS4)+800)
  elif pos == 1:
    Data="/1m30h10j4V1600L400A{}R".format(int(POS1))
  elif pos == 2:
    Data="/1m30h10j4V1600L400A{}R".format(int(POS2))
  elif pos == 3:
    Data="/1m30h10j4V1600L400A{}R".format(int(POS3))
  elif pos == 4:
    Data="/1m30h10j4V1600L400A{}R".format(int(POS4)) 
  else:
    print("Error: Please enter an allowed position.")
    return 0
    
  data=Data.encode().hex()+"0d0a"
  data=bytes.fromhex(data)
  ComPort.write(data)
  ret=ComPort.readline()
  #print(ret)
  if ret==b'\xff/0M\x03\r\n':
    print("Command received")
  f=True  
  while f==True:
    Data="/1?0"
    ComPort.write(bytes.fromhex(Data.encode().hex()+"0d0a"))
    ret=ComPort.readline()
    #print(ret)
    ret=ret.split(b"/")[1].decode()
    if "`" in ret:
      f=False
    else:
      time.sleep(1)
    


if __name__ == "__main__" :

    to_position(0)

