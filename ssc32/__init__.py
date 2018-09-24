# -*- coding: utf-8 -*-


__author__ = 'Vladimir Ermakov, Abdullah Abdul-Dayem'
__email__ = 'vooon341@gmail.com, abdullahdayem@gmail.com'
__license__ = 'MIT'
__version_tuple__ = (0, 5, 0)
__version__ = '{0}.{1}.{2}'.format(*__version_tuple__)

from .ssc32 import *
from .script import *

try:
    import yaml
except ImportError:
    import sys
    sys.stderr.writelines("Warning: For Servo Script PyYAML molule required")
