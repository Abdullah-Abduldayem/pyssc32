# -*- coding: utf-8 -*-
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
    MIN_CHANNEL = 0
    MAX_CHANNEL = 31
    def __init__(self, on_changed_callback, num, name=None, pos=1500):
        """
        :param func on_changed_callback: Callback function position is changed
        :param int num: Servo number
        :param str name: (Optional) Servo name
        :param int pos: (Optional) Initial position (in PWM)
        
        :raise ValueError: if `num` not an integer in the range [0, 31]
        :raise TypeError: if `pos` not an integer
        """
        
        if(type(num) != int or num<Servo.MIN_CHANNEL or num>Servo.MAX_CHANNEL):
            raise ValueError("Channel number must be an integer between {} and {}".format(
                Servo.MIN_CHANNEL,
                Servo.MAX_CHANNEL))
        
        self.min = 500
        self.max = 2500
        if(type(pos) != int):
            raise TypeError("Position must be an integer")
        
        self.on_changed_callback = on_changed_callback
        self.name = name
        self.num = num
        
        self.position = pos
        self._speed = None
        
        self.deg_max = 90.0
        self.deg_min = -90.0
        self.is_changed = False

    def __repr__(self):
        if self._name is not None:
            name = ' '+self._name
        else:
            name = ''
        return '<Servo{0}: #{1} name={8} pos={2}({5}°) range={3}...{4}({6}°...{7}°)>'.format(
            name, self.num,
            self._pos, self.min, self.max,
            self.degrees, self.deg_min, self.deg_max,
            self._name)

    @property
    def position(self):
        """
        Target position using PWM.

        :type: int or float
        """
        return self._pos

    @position.setter
    def position(self, pos):
        pos = int(pos)
        if pos > self.max:
            pos = self.max
        elif pos < self.min:
            pos = self.min

        self.is_changed = True
        self._pos = pos

        self.on_changed_callback()

    @property
    def speed(self):
        """
        Maximum speed of servo (unknown units)

        :type: int, float or None
        """
        return self._speed
    
    @speed.setter
    def speed(self, val):
        if (val is None or val == -1):
            self._speed = None
        elif(type(val) != int or type(val) != float):
            raise TypeError("Speed must be int or float.")
        else:
            self._speed = int(val)

    @property
    def name(self):
        """
        Name for servo
    
        :type: str or None
        """
        return self._name

    @name.setter
    def name(self, name):
        if (name is not None):
            self._name = name.upper()
        else:
            self._name = None

    @property
    def degrees(self):
        """
        Target position in degrees.

        :type: float
        """
        
        deltapos = self._pos - self.min
        return self.deg_min + \
                (abs(self.deg_min)*deltapos + abs(self.deg_max)*deltapos) \
                / (self.max - self.min)

    @degrees.setter
    def degrees(self, deg):
        deg = float(deg)
        pos = self.min + \
                (deg - self.deg_min) * (self.max - self.min) \
                / (abs(self.deg_min) + abs(self.deg_max))
        self.position = pos

    @property
    def radians(self):
        """
        Target position in radians.

        :type: float
        """
        return math.radians(self.degrees)

    @radians.setter
    def radians(self, rad):
        self.degrees = math.degrees(rad)

    def _get_cmd_string(self):
        """
        Create the command string to send to the control board for this particular servo
        
        :return: Command string
        :rtype: str
        """
        if self.is_changed:
            self.is_changed = False
            
            cmd = '#{channel}P{pulse_width}'.format(
                channel=self.num,
                pulse_width=self._pos)
            
            if (self._speed):
                cmd += "S{speed}".format(speed=self._speed)
            
            return cmd
        else:
            return ''