# -*- config: utf-8 -*-
"""
Movement scripting.
"""

import time
import yaml
from copy import copy

__all__ = [
    'Script',
    'Movement',
    'ScriptError',
]


class ScriptError(Exception):
    pass


class Movement(yaml.YAMLObject):
    yaml_tag = '!Movement'

    def __init__(self, **kvargs):
        self.joints = [] # (joints, deg, rad, pos)
        self.update(**kvargs)

    def update(self, **kvargs):
        self.time = float(kvargs.pop('time', 0))
        self.wait = float(kvargs.pop('wait', 0))

        for k, v in kvargs.iteritems():
            try:
                joint, measure = k.rsplit('_', 1)
            except ValueError:
                joint, measure = k, 'pos'

            if measure in ['deg', 'degrees']:
                move = (joint, float(v), None, None)
            elif measure in ['rad', 'radians']:
                move = (joint, None, float(v), None)
            elif measure in ['pos', 'position']:
                move = (joint, None, None, int(v))
            else:
                raise ScriptError('unknown measure "{0}" for servo "{1}"'.format(measure, joint))

            self.joints.append(move)

    def run(self, ssc, time_):
        for move in self.joints:
            joint_name, deg, rad, pos = move
            joint = ssc[joint_name]
            if deg is not None:
                joint.degrees = deg
            elif rad is not None:
                joint.radians = rad
            else:
                joint.position = pos

        time_i = self.time if self.time else time_
        time_i = int(time_i * 1000)

        ssc.commit(time=time_i)
        while not ssc.is_done():
            time.sleep(0.01)
        time.sleep(self.wait)

    def __cmp__(self, obj):
        if not isinstance(obj, Movement):
            return False
        return cmp(self.joints, obj.joints)

    def __getstate__(self):
        d = {'time': self.time,
             'wait': self.time}
        for joint, deg, rad, pos in self.joints:
            if deg is not None:
                mv = {'deg': deg}
            elif rad is not None:
                mv = {'rad': rad}
            else:
                mv = {'pos': pos}
            d[joint] = mv
        return d

    def __setstate__(self, data):
        self.joints = []
        self.time = float(data.pop('time', 0))
        self.wait = float(data.pop('wait', 0))
        for k, v in data.iteritems():
            self.joints.append((k,
                                v.pop('deg', None),
                                v.pop('rad', None),
                                v.pop('pos', None)))


    def __repr__(self):
        return '<Movement time={0} wait={1} {2}>'.format(
            self.time, self.wait, self.joints)


class Script(yaml.YAMLObject):
    yaml_tag = '!Script'

    def __init__(self, time=None):
        self.time = time
        self.movements = []
        self.on_movement_done = lambda pn, movement: None

    def add(self, **kvargs):
        self.movements.append(Movement(**kvargs))

    def run(self, ssc):
        autocommit = ssc.autocommit
        ssc.autocommit = None
        ml = len(self.movements)
        for no, move in enumerate(self.movements):
            move.run(ssc, self.time)
            self.on_movement_done((no+1, ml), move)
        ssc.autocommit = autocommit

    def __call__(self, ssc):
        self.run(ssc)

    def __cmp__(self, obj):
        if not isinstance(obj, Script):
            return False
        return cmp(self.time, obj.time) and \
                cmp(self.movements, obj.movements)

    def __add__(self, obj):
        cls = Script(time=self.time)
        cls.movements = copy(self.movements)

        if isinstance(obj, dict):
            cls.add(**obj)
        elif isinstance(obj, Movement):
            cls.movements.append(obj)
        elif isinstance(obj, Script):
            cls.movements += obj.movements
        elif isinstance(obj, (tuple, list)):
            for i in obj:
                self.__add__(i)
        else:
            raise ValueError('Unsupported type')

        return cls

    def __getstate__(self):
        return {'time': self.time,
                'movements': self.movements}

    def __setstate__(self, data):
        self.time = data.pop('time', 0)
        self.movements = data.pop('movements', [])

    def __repr__(self):
        return '<Script time={0} {1}>'.format(
            self.time, self.movements)

