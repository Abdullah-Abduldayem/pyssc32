# -*- coding: utf-8 -*-

import time
import ssc32
import yaml

ssc = ssc32.SSC32('/dev/ttyUSB0', 115200,
                  autocommit=1000,
                  config='example.cfg')

# see example config.cfg
joint0 = ssc['joint0']
joint1 = ssc['joint1']
joint2 = ssc['joint2']
joint3 = ssc['joint3']
joint4 = ssc['joint4']
grip = ssc['grip']

joint0.degrees = 60
ssc.commit()

#go_default = ssc32.Script(time=1000)
#go_default.add(joint0_deg=0,
#               joint1_deg=-130,
#               joint2_deg=-45,
#               joint3_deg=55,
#               joint4_deg=0,
#               grip=2300)

def run_script(scr):
    scr(ssc)

def save_script(scr, filename):
    d = yaml.dump(scr)
    with open(filename, 'w') as fd:
        fd.write(d.encode('utf-8'))

def load_script(filename):
    with open(filename, 'r') as fd:
        return yaml.load(fd)

go_default = load_script('scripts/go_default.yaml')

run_script(go_default)
