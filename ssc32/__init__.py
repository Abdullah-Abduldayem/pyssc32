# -*- coding: utf-8 -*-


__author__ = 'Vladimir Ermakov'
__email__ = 'vooon341@gmail.com'
__license__ = 'MIT'
__version_tuple__ = (0, 4, 1)
__version__ = '{0}.{1}.{2}'.format(*__version_tuple__)

from ssc32 import *

try:
    import yaml
    from script import *
except ImportError:
    import sys
    sys.stderr.writelines("Warning: For Servo Script PyYAML molule required")

