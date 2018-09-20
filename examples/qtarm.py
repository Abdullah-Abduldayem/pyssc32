#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import threading
from PyQt4 import Qt

sys.path = [".."] + sys.path
from ssc32 import SSC32
#import ssc32
from ssc32yaml import load_yaml, load_config


class MainWindow(Qt.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.scripts = {}
        config = load_config()

        for scr in glob.glob(os.path.join(os.path.dirname(__file__), 'scripts', '*.yaml')):
            self.scripts[os.path.basename(scr)] = load_yaml(scr)
            
        print(config)

        self.ssc = SSC32(config['port'], config['baud'], config=config['config'])

        widget = Qt.QWidget()
        layout = Qt.QHBoxLayout()
        self.setCentralWidget(widget)
        widget.setLayout(layout)

        self.axis = {}

        for name in ['JOINT'+str(x) for x in range(5)] + ['GRIP']:
            slider = Qt.QScrollBar()
            slider.setMaximum(self.ssc[name].max)
            slider.setValue(1500)
            slider.setMinimum(self.ssc[name].min)

            layout.addWidget(slider)
            self.axis[name] = slider
            self.connect(slider, Qt.SIGNAL('valueChanged(int)'),
                         self.on_slider(name))

        bwidget = Qt.QWidget()
        blayout = Qt.QVBoxLayout()
        bwidget.setLayout(blayout)
        layout.addWidget(bwidget)

        self.state = Qt.QLabel("Connected")
        blayout.addWidget(self.state)

        for name, script in self.scripts.iteritems():
            button = Qt.QPushButton(name)
            blayout.addWidget(button)
            self.connect(button, Qt.SIGNAL('clicked()'),
                         self.on_run_script(script))

    def on_movement_done(self, pn, move):
        self.update_state()
        self.update_sliders()

        self.state.setText(
            self.state.text() + 
            '\nMovement {0} of {1}\n'.format(pn[0], pn[1]))

    def update_state(self):
        t = ''
        k = self.axis.keys()
        k.sort()
        for name in k:
            t += '{name}:\tabs: {servo.position}\t' \
                 'deg: {servo.degrees:3.3}\trad: {servo.radians:0.4}\n'.format(
                name=name, servo=self.ssc[name])
        self.state.setText(t)

    def update_sliders(self):
        for name, slider in self.axis.iteritems():
            slider.setValue(self.ssc[name].position)

    def on_run_script(self, script):
        def inner():
            def thread_run():
                script.on_movement_done = self.on_movement_done
                script(self.ssc)
                self.update_sliders()
                self.update_state()

            threading.Thread(target=thread_run).start()
        return inner

    def on_slider(self, name):
        def inner(val_):
            val = self.axis[name].value()
            self.ssc[name].position = val
            print("Commit {0}: {1}".format(name, val))
            self.ssc.commit()
            self.update_state()

        return inner


if __name__ == '__main__':
    app = Qt.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

