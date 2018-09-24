import ssc32
import time
import sys

ssc = ssc32.SSC32("/dev/ttyUSB0", 115200, count=32)
print('Version', ssc.get_firmware_version())
print('is_done', ssc.is_done())


ssc[0].name = "fl_base"
ssc[1].name = "fl_thigh"
ssc[2].name = "fl_toe"

ssc[8].name = "bl_base"
ssc[9].name = "bl_thigh"
ssc[10].name = "bl_toe"

ssc[16].name = "fr_base"
ssc[17].name = "fr_thigh"
ssc[18].name = "fr_toe"

ssc[24].name = "br_base"
ssc[25].name = "br_thigh"
ssc[26].name = "br_toe"


print(ssc[26].no)

## Move to 0 degrees
joint = ssc["bl_toe"]
joint.degrees = 0
ssc.commit(300)
ssc.wait_for_movement_completion()


print('query_pulse_width', ssc.query_pulse_width(joint))

## Cancel a joint movement half-way
joint.degrees = 50
ssc.commit(1000)
time.sleep(0.5)
ssc.stop_servo(joint)
print("Stopped")

print("Done", ssc.is_done())

sys.exit()

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