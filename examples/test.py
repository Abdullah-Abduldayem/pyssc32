import sys
sys.path.append("..")
import ssc32
import time

ssc = ssc32.SSC32("/dev/ttyUSB0", 115200, count=16)
print('Version', ssc.get_firmware_version())
print('is_done', ssc.is_done())

## Move to -50 degrees
joint = ssc[0]
joint.degrees = -50
ssc.commit()
ssc.wait_for_movement_completion()
print('query_pulse_width', ssc.query_pulse_width(joint))

## Cancel a joint movement half-way
joint.degrees = 0
ssc.commit(2000)
time.sleep(0.5)
ssc.stop_servo(joint)

## Test digital output
for _ in range(2):
    print("CH4 = 5V")
    ssc.set_binary_output(4, 1)
    time.sleep(0.5)
    print("CH4 = 0V")
    ssc.set_binary_output(4, 0)
    time.sleep(0.5)
    
for _ in range(2):
    print("CH0 to CH7 -> 5V")
    ssc.set_byte_output(1, 0xFF)
    time.sleep(0.5)
    print("CH0 to CH7 -> 0V")
    ssc.set_byte_output(1, 0x00)
    time.sleep(0.5)


## Rest reading of inputs
print(ssc.read_analog_input("ABC"))
print(ssc.read_digital_input("ABC", latched=False))



print(ssc)