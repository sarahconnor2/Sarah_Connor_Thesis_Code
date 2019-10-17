import Adafruit_ADXL345

def gatherData():
    
    accel = Adafruit_ADXL345.ADXL345()

    while (1):
        # Read the X, Y, Z axis acceleration values and print them.
        x, y, z = accel.read()
        
        print('X={0}, Y={1}, Z={2}'.format(x, y, z))
    

gatherData()