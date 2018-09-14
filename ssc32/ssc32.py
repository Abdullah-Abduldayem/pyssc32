# -*- coding: utf-8 -*-
"""
SSC32 controlling library
"""

import serial
import math

__all__ = [
    'SSC32'
]


class Servo(object):
    """
    Servo control class

    >>> servo.position
    1500
    >>> servo.position = 2500
    >>> servo.position
    2500
    >>> servo.max = 1600
    >>> servo.position = 2400
    1600
    """

    def __init__(self, on_changed_callback, no, name=None):
        """
        `on_changed_callback` — colld when position was changed
        `no` — servo number
        `name` — servo name
        """
        self.on_changed_callback = on_changed_callback
        self.name = name
        self.no = no
        self.min = 500
        self._pos = 1500
        self.max = 2500
        self.deg_max = 90.0
        self.deg_min = -90.0
        self.is_changed = False

    def __repr__(self):
        if self.name is not None:
            name = ' '+self.name
        else:
            name = ''
        return '<Servo{0}: #{1} pos={2}({5}°) {3}({6}°)..{4}({7}°)>'.format(
            name, self.no,
            self._pos, self.min, self.max,
            self.degrees, self.deg_min, self.deg_max)

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, pos):
        """
        Set absolute position
        """
        pos = int(pos)
        if pos > self.max:
            pos = self.max
        elif pos < self.min:
            pos = self.min

        self.is_changed = True
        self._pos = pos

        self.on_changed_callback()

    @property
    def degrees(self):
        deltapos = self._pos - self.min
        return self.deg_min + \
                (abs(self.deg_min)*deltapos + abs(self.deg_max)*deltapos) \
                / (self.max - self.min)

    @degrees.setter
    def degrees(self, deg):
        """
        Set position in degrees
        """
        deg = float(deg)
        pos = self.min + \
                (deg - self.deg_min) * (self.max - self.min) \
                / (abs(self.deg_min) + abs(self.deg_max))
        self.position = pos

    @property
    def radians(self):
        return math.radians(self.degrees)

    @radians.setter
    def radians(self, rad):
        """
        Set position in radians
        """
        self.degrees = math.degrees(rad)

    def _get_cmd_string(self):
        if self.is_changed:
            self.is_changed = False
            return '#{0}P{1}'.format(self.no, self._pos)
        else:
            return ''


class SSC32(object):
    """
    SSC32 control class

    It use indexing for access to servos.

    >>> ssc = SSC32('/dev/ttyUSB0', 115200)
    >>> ssc[1].position = 2000
    >>> ssc[1].name = 'gripper'
    >>> gripper = ssc['gripper']
    >>> gripper.max = 2000
    >>> gripper.min = 1000
    >>> gripper.deg_max = +75.0
    >>> gripper.deg_min = -75.0
    >>> ssc.commit(time=2000)
    >>> ssc.save_config('manipulator.cfg')
    """

    def __init__(self, port, baudrate, count=16, config=None, autocommit=None):
        """
        `port` — serial port
        `baudrate` — serial speed
        `count` — servo count, on original SSC32 need to be set to 32
        `config` — servo config file e.g. name and max/min
        `autocommit` — autocommit changes, used as default time (#<n>P<pos>T<time>)
        """
        self.config = None
        self.description = None

        self.autocommit = autocommit
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self._servos = [Servo(self._servo_on_changed, i) for i in xrange(count)]

        # for baudrate detection on Open Robotics controllers
        self.ser.write('\r'*10)

        if config:
            self.load_config(config)

    def close(self):
        self.ser.close()

    #def __del__(self):
    #    self.close()

    def __repr__(self):
        return '<SSC32: {0} {1},8,N,1 {2}>'.format(self.ser.port,
                                                   self.ser.baudrate,
                                                   self._servos)

    def __getitem__(self, it):
        if type(it) == str or type(it) == unicode:
            for servo in self._servos:
                it = it.upper()
                if servo.name == it:
                    return servo
            raise KeyError(it)
        return self._servos[it]

    def __len__(self):
        return len(self._servos)

    def _servo_on_changed(self):
        if self.autocommit is not None:
            self.commit(self.autocommit)

    def commit(self, time=None):
        """
        Commit servo states to comtroller

        `time` — operation time ([#<n>P<pos>]T<time>)
        """
        cmd = ''.join([self._servos[i]._get_cmd_string()
                       for i in xrange(len(self._servos))])
        if time is not None and cmd != '':
            cmd += 'T{0}'.format(time)
        cmd += '\n'
        self.ser.write(cmd)

    def is_done(self):
        """
        Check that operations is done
        """
        self.ser.flushInput()
        self.ser.write('Q\n')
        r = self.ser.read(1)
        return r == '.'

    def load_config(self, config):
        """
        Load servo config from file
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
        Save servo config to file

        default destination file — file from config was loaded
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

