"""
Motorbench
Motor Sensors Reading from Arduino Uno MEGA

Copyright (C) 2017  Giovanni Grieco <giovanni.grc96@gmail.com>
                    Poliba Corse <polibacorse@poliba.it>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import csv
import ctypes
import math
import numpy as np
import platform
import re
import serial
import serial.tools.list_ports
import signal

from datetime import datetime
from matplotlib import pyplot as plt

# pyinstaller "Missing module" fix
import matplotlib.backends.backend_tkagg

"""Configuration

Just edit this dict with the correct vid and pid to endure proper
device identification.
"""
ARDUINO = {
    'vid': 9025,
    'pid': 67
}

"""Utilities for Motorbench
"""
class Helper():
    """Helper to handle indices and logical indices of NaNs.

    Thanks to http://stackoverflow.com/a/6520696
    Input:
        - y, 1d np array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature
            indices = index(logical_indices),
            to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= _nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """
    def nan_helper(y):
        return np.isnan(y), lambda z: z.nonzero()[0]

    """Helper to return a list without unknown values
    """
    def clean_list(lst):
        return [x for x in lst if x is not None]

"""Core object
"""
class Motorbench():
    def __init__(self):
        self._arduino = None

        self._find_arduino()
        self._serial_io = serial.Serial(
            self._arduino.device,
            9600,
            bytesize=serial.EIGHTBITS)

        self._init_plots()
        self._revalues = re.compile(b'E([0-9\.]+)F([0-9\.]+)P([0-9\.]+)')

        signal.signal(signal.SIGINT, self._save_graph)
        self._run_loop()

    """Return a connected Arduino as PySerial ListPortInfo object.

    Try to find Arduino using PySerial's Tools module.
    Warn user and exit if any Arduino is found.
    """
    def _find_arduino(self):
        for port in serial.tools.list_ports.comports():
            if port.vid == ARDUINO['vid'] and port.pid == ARDUINO['pid']:
                self._arduino = port

        if not self._arduino:
            msg_err = 'Arduino not found.\n' \
                'Please connect it and restart the program.'

            if platform.system() == 'Windows':
                ctypes.windll.user32.MessageBoxW(0, msg_err, 'Oops!', 0x10)
            else:
                print(msg_err)

            exit(1)

    """Return void

    Initialise matplotlib plots.
    BUG: if someone closes the window, the program should exit, not
        redraw itself incorrectly.
    """
    def _init_plots(self):
        """
        Flow and pressure data should be to the floor int value of
        encoder. By empiric test we have a range from -8 to 362 degrees.
        ENC_MIN (which is abs value) represents array bias to shift idx
        to positive int.
        """
        self._ENC_MIN = 8
        self._ENC_MAX = 362

        vector_dim = self._ENC_MAX + self._ENC_MIN
        self._sensors = dict()

        ENCODER_PLOT_ID = 311
        FLOW_PLOT_ID = 312
        PRESSURE_PLOT_ID = 313

        plt.ion()
        # fig = plt.figure()
        #test_toolbar.TestToolbar(fig)

        plt.subplot(ENCODER_PLOT_ID)
        self._sensors['encoder'] = {
            'ID': ENCODER_PLOT_ID,
            # [0] is to have a fixed point so matplotlib can plot with
            # multiple NaNs
            'data': np.array([0] * vector_dim).astype(np.float)
        }
        self._sensors['encoder']['plot'] = plt.plot(
            self._sensors['encoder']['data'])[0]
        plt.title('Encoder')
        plt.ylabel('degrees')
        plt.xlabel('time')

        plt.subplot(FLOW_PLOT_ID)
        self._sensors['flow'] = {
            'ID': FLOW_PLOT_ID,
            'data': np.array(
                [0] + [np.nan] * vector_dim).astype(np.float),
            'plot': plt.plot([], [])[0]
        }
        plt.title('Flow')
        plt.ylabel('kg/h')
        plt.xlabel('degrees')

        plt.subplot(PRESSURE_PLOT_ID)
        self._sensors['pressure'] = {
            'ID': PRESSURE_PLOT_ID,
            'data': np.array(
                [0] + [np.nan] * vector_dim).astype(np.float),
            'plot': plt.plot([], [])[0]
        }
        plt.title('Pressure')
        plt.ylabel('kPa')
        plt.xlabel('degrees')

        plt.tight_layout()

    def _save_graph(self, signal, frame):
        print('Saving session and exiting...')
        session_time = datetime.now().isoformat(sep=' ', timespec='minutes')

        self._sensors['flow']['data'].tofile(
            session_time + '_flow.csv',
            sep=',',
            format='%10.5f')
        self._sensors['pressure']['data'].tofile(
            session_time + '_pressure.csv',
            sep=',',
            format='%10.5f')

        exit(0)

    """Return list of sensor values from Arduino
    """
    def _get_frame(self):
        read = self._serial_io.readline().rstrip()

        filtered = self._revalues.search(read)

        return [
            float(filtered.group(1)),
            float(filtered.group(2)),
            float(filtered.group(3))
        ]

    def _update_encoder(self, value, flow, pressure):
        plt.subplot(self._sensors['encoder']['ID'])
        self._sensors['encoder']['data'] = np.append(
            self._sensors['encoder']['data'], value)
        self._sensors['encoder']['data'] = np.delete(
            self._sensors['encoder']['data'], 0)

        self._sensors['encoder']['plot'].set_xdata(
            np.arange(len(self._sensors['encoder']['data'])))
        self._sensors['encoder']['plot'].set_ydata(
            self._sensors['encoder']['data'])

        # autozoom
        plt.ylim([
            min(self._sensors['encoder']['data']) - 1,
            max(self._sensors['encoder']['data']) + 1
            ])
        plt.title('Encoder: ' + str(value) + '°')

    def _update(self, value, encoder_value, sensor_name, title=['','']):
        plt.subplot(self._sensors[sensor_name]['ID'])
        self._sensors[sensor_name]['data'][
            self._ENC_MIN + math.floor(encoder_value)] = value

        """
        Interpolation
        """
        nans, x = Helper.nan_helper(self._sensors[sensor_name]['data'])
        data_with_nans = np.interp(
            x(nans), x(~nans), self._sensors[sensor_name]['data'][~nans])

        self._sensors[sensor_name]['plot'].set_xdata(
            np.arange(len(data_with_nans)))
        self._sensors[sensor_name]['plot'].set_ydata(data_with_nans)

        """
        Autozoom feature
        """
        plt.xlim([
            min(self._sensors['encoder']['data']) - 1,
            max(self._sensors['encoder']['data']) + 1
            ])
        # get rid of NaNs when autozooming
        nan_filtered = Helper.clean_list(self._sensors[sensor_name]['data'])
        plt.ylim([
            min(nan_filtered) - 0.5,
            max(nan_filtered) + 0.5
            ])

        plt.title(title[0] + str(value) + title[1])

    def _run_loop(self):
        while True:
            encoder, flow, pressure = self._get_frame()
            self._update_encoder(encoder, flow, pressure)
            self._update(flow, encoder, 'flow', title=['Flow: ', ' kg/h'])
            self._update(pressure, encoder, 'pressure',
                title=['Pressure: ', ' kPa'])

            plt.pause(0.2) # let matplotlib breathe fresh air

if __name__ == '__main__':
    Motorbench()
