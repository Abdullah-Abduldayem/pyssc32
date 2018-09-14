#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import ssc32
from optparse import OptionParser


DEFAULT_CFG = '$HOME/.ssc32.rc'

def load_yaml(filename):
    with open(filename, 'r') as fd:
        return yaml.load(fd)

def save_yaml(filename, data):
    d = yaml.dump(data)
    with open(filename, 'w') as fd:
        fd.write(d.encode('utf-8'))

def abspath(path):
    return os.path.abspath(
        os.path.expanduser(
            os.path.expandvars(
                path
            )
        )
    )

def load_config(cfg_fname=DEFAULT_CFG):
    cfg_fname = abspath(cfg_fname)
    try:
        cfg = load_yaml(cfg_fname)
    except:
        cfg = {
            'port': '/dev/ttyUSB0',
            'baud': 115200,
            'config': abspath('$HOME/.ssc32.servo')
        }
    return cfg

def main():
    parser = OptionParser()
    parser.add_option('-c', '--cofig', dest='cfg_fname', default=DEFAULT_CFG, help='config file')
    parser.add_option('-p', '--port', dest='port', help='serial port', default=None)
    parser.add_option('-b', '--baudrate', dest='baud', help='baudrate', default=None)
    parser.add_option('-s', '--servo-config', dest='servoconfig', help='servo config', default=None)
    parser.add_option('-u', '--update-config', dest='upconf', action='store_true', default=False, help='Update config file')

    options, args = parser.parse_args()

    if len(args) != 1:
        print 'Error args: ', args
        return 1

    conf = load_config(options.cfg_fname)
    if options.port is not None:
        conf['port'] = options.port
    if options.baud is not None:
        conf['baud'] = int(options.baud)
    if options.servoconfig is not None:
        conf['config'] = abspath(options.servoconfig)

    ssc = ssc32.SSC32(conf['port'], conf['baud'], config=conf['config'])

    if options.upconf:
        save_yaml(abspath(options.cfg_fname), conf)

    filename = os.path.abspath(args[0])

    script = load_yaml(filename)
    script(ssc)

    return 0

if __name__ == '__main__':
    sys.exit(main())
