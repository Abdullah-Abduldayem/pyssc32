# -*- coding: utf-8 -*-
"""
SSC32 controlling library
"""

import serial
import math
import sys
import struct
import time
import os

sys.path.append('..')
from ssc32.servo import Servo

try:
    xrange
except NameError:
    xrange = range

__all__ = [
    'SSC32'
]


class SSC32Serial(serial.Serial):
    """
    Serial interfacing class. Particularly useful for automatically adding 
    carriage return (CR, \r, 0x0D) and reading until CR is reached
    """

    def __init__(self, port, baudrate, timeout=1):
        super(SSC32Serial, self).__init__(port, baudrate, timeout=timeout)

        # for baudrate detection on Open Robotics controllers
        self.write_line('\r'*10)
        
    
    def write_line(self, val):
        """
        Write byte string with CR line terminator.
        For python3, data is automatically encoded into a byte string to avoid unicode conflicts.
        
        Args:
            val (str): String to write
        """
        val += "\r"
        if sys.version_info >= (3, 0):
            val = val.encode()
        
        self.write(val)
    
    
    def read_line(self, size=500):
        """
        Read line until a CR (carriage return) is detected
        
        Args:
            size (int, optional): Maximum buffer length.
        
        Returns:
            str: Read string.
        """
        
        val = self.read_until('\r', size)
        
        if (len(val) > 0):
            if (val[-1] == "\r"):
                val = val[0:-1]
                
        if sys.version_info >= (3, 0):
            val = val.decode()
            
        return val
    

class SSC32(object):
    """
    SSC32 control class
    
    Example:
    ::
    
        import ssc32
        ssc = ssc32.SSC32('/dev/ttyUSB0', 115200)
        ssc[1].position = 2000
        ssc[1].name = 'gripper'
        gripper = ssc['gripper']
        gripper.max = 2000
        gripper.min = 1000
        gripper.deg_max = +75.0
        gripper.deg_min = -75.0
        ssc.commit(time=2000)
        ssc.save_config('manipulator.cfg')
    """
    
    

    def __init__(self, port, baudrate, count=32, timeout=1, config=None, autocommit=None):
        """
        :param str port: Serial port
        :param int baudrate: Serial speed
        :param int count: (Optional) Servo count. On original SSC32 need to be set to 32
        :param str config: (Optional)  Configuration file which contains servo names and limits
        :param bool autocommit: (Optional) Autocommit changes as soon as the servo postion is changed
        
        :raise Exception: if "SSC32" not detected in the board's firmware version
        """
        self.config = None
        self.description = None

        self.autocommit = autocommit
        
        ## Create serial connection
        self.ser = SSC32Serial(port, baudrate, timeout=timeout)
        self.ser.flush()
        self.ser.flushInput()
        
        ## Check that this is actually an SSC32 board
        if (not "SSC32" in self.get_firmware_version()):
            raise Exception("No SSC32 board detected")
        
        self._servos = [Servo(self._servo_on_changed, i) for i in xrange(count)]

        if config:
            self.load_config(config)

    def close(self):
        """
        Close serial port
        """
        self.ser.close()

    def __del__(self):
        self.close()

    def __repr__(self):
        return '<SSC32: port={0}, baud={1}, servos={3} {2}>'.format(self.ser.port,
                                                   self.ser.baudrate,
                                                   self._servos,
                                                   self._servos.__len__())

    def __getitem__(self, it):
        """
        Get servo corresponding to a certain index or name
        
        :param it: Servo to look up
        :type it: int or str or ssc32.Servo
        :rtype: ssc32.Servo
        :raise KeyError: if string name not found.
        :raise TypeError: if input us not int, str or ssc32.Servo
        
        Example:
        ::
        
            import ssc32
            ssc = ssc32.SSC32('/dev/ttyUSB0', 115200)
            
            joint0 = ssc[0]
            joint0.name = "elbow"
            joint_elbow = ssc["elbow"]
            
            ## Both joint0 and joint_elbow will be referring to the same object
        """
        if sys.version_info >= (3, 0):
            is_str = (type(it) == str)
        else:
            is_str = (type(it) == str or type(it) == unicode)

        if is_str:
            it = it.upper()
            for servo in self._servos:
                if servo.name == it:
                    return servo
            raise KeyError(it)
        elif (type(it) == int):
            return self._servos[it]
        elif (type(it) == Servo):
            return it
        else:
            raise TypeError("Servo must be of type int, string or Servo.")

    def __len__(self):
        """
        Get number of servos
        
        :return: Number of servos
        :rtype: int
        """
        return len(self._servos)

    def _servo_on_changed(self):
        if self.autocommit is not None:
            self.commit(self.autocommit)   
            
    
    ##########
    ## SSC32 MOTOR COMMANDS
    ##########
    def commit(self, time=None):
        """
        Commit servo states to controller
        
        :param int time: (Optional) Time in ms for entire move. Max: 65535
        """
        
        cmd = ''.join([self._servos[i]._get_cmd_string()
                       for i in xrange(len(self._servos))])
        
        if time is not None and cmd != '':
            cmd += 'T{0}'.format(time)

        self.ser.write_line(cmd)
        
        
    def move_all_servos(self, time=None):
        """
        Alias for commit()
        
        :param int time: (Optional) Time in ms for entire move. Max: 65535
        """
        self.commit(self, time=time)
        
        
    def move_single_servo(self, servo, time=None):
        """
        Move a single servo independent of the others
        
        :param servo: Name, index or instance of ssc32.Servo
        :type servo: int or str or ssc32.Servo
        """
        serv = self[servo]
        
        cmd = serv._get_cmd_string()
        if time is not None and cmd != '':
            cmd += 'T{0}'.format(time)

        self.ser.write_line(cmd)
        
    
    def set_binary_output(self, channel, level):
        """
        Set the signal line on one of the servos to be HIGH or LOW
        
        :param channel: Servo index, name or instance
        :type channel: int or str or ssc32.Servo
        :param int level: Zero sets output to LOW, any other value sets to HIGH
        """
        
        if (level==0):
            L = "L"
        else:
            L = "H"
        
        serv = self[channel]
        self.ser.write_line('#{}{}'.format(serv.no, L))
        
    def set_byte_output(self, bank, value):
        """
        Sets 8 digital pins to the specified byte value.
        
        :param int bank: Bank of pins to set. (**0:** `Channels 0-7`, **1:** `Channels 8-15`, **2:** `Channels 16-23`, **3:** `Channels 24-31`)
        :param byte value: A byte between 0 and 255 that detemines how the 8bits in the bank should be set.
        
        :raises ValueError: if `bank` not in the range [0,3]
        :raises ValueError: if `value` not in the range [0,255]
        """
        if (type(bank) != int or bank >= len(self._servos)//8 or bank < 0):
            raise ValueError("Bank must be an integer between 0 and {}".format(len(self._servos)//8))
        if (type(value) != int or value > 255 or value < 0):
            raise ValueError("Value must be an integer between 0 and 255")
        
        self.ser.write_line('#{}:{}'.format(bank, value))
        
    
    def get_firmware_version(self):
        """
        Get the firmware version of the board
        
        :return: Firmware version of board
        :rtype: str
        """
        self.ser.write_line('VER')
        r = self.ser.read_line()
        return r


    def is_done(self):
        """
        Checks if movement is finished
        
        :return: True if movement is finished, False otherwise
        :rtype: bool
        """
        self.ser.flushInput()
        self.ser.write_line('Q')
        r = self.ser.read(1)
        return r == '.'
    
    
    def query_pulse_width(self, servo):
        """
        Query pulse width of a given servo
        
        :param servo: Servo index, name or instance
        :type servo: int or str or ssc32.Servo
        :return: Pulse width in microseconds
        :rtype: int
        """
        serv = self[servo]
        self.ser.write_line("QP{}".format(serv.no))
        
        r = self.ser.read(1)
        r = struct.unpack('B', r)[0]*10
        return r
        
    
    def stop_servo(self, servo):
        """
        Stop the servo on specified channel
        
        :param servo: Servo index, name or instance
        :type servo: int or str or ssc32.Servo
        """
        serv = self[servo]
        self.ser.write_line('STOP {}'.format(serv.no))


    ##########
    ## SSC32 I/O COMMANDS
    ##########
    def read_analog_input(self, inputs):
        """
        Read analog input on the pins from "A" to "D"
        
        :param str inputs: The names of the channel(s) to read (eg. "A" or "ABCD")
        :return: The read voltage(s)
        :rtype: int of list(int)
        
        Example:
        ::
        
            ssc.read_analog_input("A")
            ## 240
            
            ssc.read_analog_input("ACD")
            ## [240, 30, 196]
        """
        
        cmd = ""
        count = 0
        
        for input in inputs:
            input = input.upper()
            if (input >= "A" and input <= "D"):
                cmd += "V" + input + " "
                count += 1

        if (cmd == ""):
            return None
        
        
        self.ser.write_line(cmd)
        vals = self.ser.read(count)
        
        ret = []
        for v in vals:
            v = struct.unpack('B', v)[0]
            ret.append(v)
            
        if (count == 1):
            return ret[0]
        
        return ret
    
    
    
    def read_digital_input(self, inputs, latched=False):
        """
        Read digital input on the pins from "A" to "D"
        
        :param str inputs: The names of the channel(s) to read (eg. "A" or "ABCD")
        :param bool latched: Ask for latched input data. False by default.
        :return: The read states
        :rtype: bool of list(bool)
        
        Example:
        ::
        
            ssc.read_digital_input("A")
            ## True
            
            ssc.read_digital_input("ACD")
            ## [True, False, True]
        """
        
        cmd = ""
        count = 0
        
        lat = ""
        if (latched):
            lat = "L"
        
        for input in inputs:
            input = input.upper()
            if (input >= "A" and input <= "D"):
                cmd += input + lat + " "
                count += 1

        if (cmd == ""):
            return None
        
        
        self.ser.write_line(cmd)
        vals = self.ser.read(count)
        
        ret = []
        for v in vals:
            ret.append(v == "1")
            
        if (count == 1):
            return ret[0]
        
        return ret
    
    
    ##########
    ## QUALITY OF LIFE FUNCTIONS
    ##########
    def wait_for_movement_completion(self):
        """
        Wait for movement to end
        """
        
        while not self.is_done():
            time.sleep(0.01)


    ##########
    ## CONFIG FUNCTIONS
    ##########
    def load_config(self, config):
        """
        Load servo config from file
        
        :param str config: Path to configuration file.
        """
        self.config = config
        self.description = ''
        with open(config, 'r') as fd:
            for line in fd.readlines():
                if line.startswith('#~ '):
                    self.description += line[2:].strip() + '\n'
                    continue
                elif line.startswith('#') or not line:
                    continue
                dat = line.split()
                servo = self._servos[int(dat[1])]
                servo.name = dat[0].upper()
                servo.min = int(dat[2])
                servo.max = int(dat[3])
                servo.deg_min = float(dat[4])
                servo.deg_max = float(dat[5])


    def save_config(self, config=None):
        """
        Save servo configuration to file. If load_config was called earlier, this function will save to the previously loaded file by default.
        
        :param str config: Path to configuration file. Default: Saves to previously loaded config path.
        """
        if config is None:
            config = self.config
        with open(config, 'w') as fd:
            if self.description:
                fd.write(''.join(
                    ['#~ ' + line + '\n' for line 
                     in self.description.splitlines()]))
            fd.write('# name\t#\tmin\tmax\tmin°\tmax°\n')
            for servo in self._servos:
                if servo.name is not None:
                    fd.write('\t'.join([str(item) for item in [
                        servo.name.upper(), servo.no,
                        servo.min, servo.max,
                        servo.deg_min, servo.deg_max]]) + '\n')
