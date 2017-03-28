"""
Motorbench
Motor Sensors Reading from Arduino Uno MEGA

Author: Giovanni Grieco <giovanni.grc96@gmail.com>
Copyright (c) Poliba Corse. All rights reserved.
"""

import serial
from matplotlib import pyplot
import numpy
import math
import signal
import csv
from datetime import datetime

#import test_toolbar

class Motorbench():
	def __init__(self):
		try:
			self.serial_io = serial.Serial('/dev/tty.usbmodem1421', 9600, bytesize=serial.EIGHTBITS)
		except serial.serialutil.SerialException:
			print('Houston, serial file not found. Abort mission.')
			exit()

		"""
		Flow and pressure data should be to the floor int value of encoder
		By empiric test we have a range from -8 to 362 degrees
		ENC_MIN (which is abs value) reppresents array bias to shift idx to positive int
		"""
		self.ENC_MIN = 8
		self.ENC_MAX = 362

		vector_dim = self.ENC_MAX + self.ENC_MIN
		self.sensors = dict()

		ENCODER_PLOT_ID = 311
		FLOW_PLOT_ID = 312
		PRESSURE_PLOT_ID = 313

		pyplot.ion()
		# fig = pyplot.figure()
		#test_toolbar.TestToolbar(fig)

		pyplot.subplot(ENCODER_PLOT_ID)
		self.sensors['encoder'] = {
			'ID': ENCODER_PLOT_ID,
			# [0] is to have a fixed point so matplotlib can plot with multiple NaNs
			'data': numpy.array([0] * vector_dim).astype(numpy.float)
		}
		self.sensors['encoder']['plot'] = pyplot.plot(self.sensors['encoder']['data'])[0]
		pyplot.title('Encoder')
		pyplot.ylabel('degrees')
		pyplot.xlabel('time')

		pyplot.subplot(FLOW_PLOT_ID)
		self.sensors['flow'] = {
			'ID': FLOW_PLOT_ID,
			'data': numpy.array([0] + [numpy.nan] * vector_dim).astype(numpy.float),
			'plot': pyplot.plot([],[])[0]
		}
		pyplot.title('Flow')
		pyplot.ylabel('kg/h')
		pyplot.xlabel('degrees')

		pyplot.subplot(PRESSURE_PLOT_ID)
		self.sensors['pressure'] = {
			'ID': PRESSURE_PLOT_ID,
			'data': numpy.array([0] + [numpy.nan] * vector_dim).astype(numpy.float),
			'plot': pyplot.plot([],[])[0]
		}
		pyplot.title('Pressure')
		pyplot.ylabel('kPa')
		pyplot.xlabel('degrees')

		pyplot.tight_layout()
		signal.signal(signal.SIGINT, self.save_graph)
		self.run_loop()

	def save_graph(self, signal, frame):
		print('Saving session and exiting...')
		session_time = str(datetime.now())
		self.sensors['flow']['data'].tofile(session_time+'_flow.csv',sep=',',format='%10.5f')
		self.sensors['pressure']['data'].tofile(session_time+'_pressure.csv', sep=',', format='%10.5f')
		exit()

	def nan_helper(self, y):
		"""Helper to handle indices and logical indices of NaNs.
		Thanks to http://stackoverflow.com/a/6520696
		Input:
		- y, 1d numpy array with possible NaNs
		Output:
		- nans, logical indices of NaNs
		- index, a function, with signature indices= index(logical_indices),
		  to convert logical indices of NaNs to 'equivalent' indices
		Example:
		>>> # linear interpolation of NaNs
		>>> nans, x= nan_helper(y)
		>>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
		"""
		return numpy.isnan(y), lambda z: z.nonzero()[0]


	def get_frame(self):
		sensors = [0,0,0]
		for _ in range(3):
			x = self.serial_io.readline().rstrip()
			if b'E' in x:
				sensors[0] = float(x[1:])
			if b'F' in x:
				sensors[1] = float(x[1:])
			if b'P' in x:
				sensors[2] = float(x[1:])
		return sensors

	def update_encoder(self, value, flow, pressure):
		pyplot.subplot(self.sensors['encoder']['ID'])
		self.sensors['encoder']['data'] = numpy.append(self.sensors['encoder']['data'], value)
		self.sensors['encoder']['data'] = numpy.delete(self.sensors['encoder']['data'], 0)

		self.sensors['encoder']['plot'].set_xdata(numpy.arange(len(self.sensors['encoder']['data'])))
		self.sensors['encoder']['plot'].set_ydata(self.sensors['encoder']['data'])

		# autozoom
		pyplot.ylim([min(self.sensors['encoder']['data'])-1,max(self.sensors['encoder']['data'])+1])
		pyplot.title('Encoder: '+str(value)+'°')

	def update(self, value, encoder_value, sensor_name, title=['','']):
		pyplot.subplot(self.sensors[sensor_name]['ID'])
		self.sensors[sensor_name]['data'][self.ENC_MIN+math.floor(encoder_value)] = value

		# interpolate
		nans, x = self.nan_helper(self.sensors[sensor_name]['data'])
		data_with_nans = numpy.interp(x(nans), x(~nans), self.sensors[sensor_name]['data'][~nans])

		self.sensors[sensor_name]['plot'].set_xdata(numpy.arange(len(data_with_nans)))
		self.sensors[sensor_name]['plot'].set_ydata(data_with_nans)

		# autozoom
		pyplot.xlim([ min(self.sensors['encoder']['data'])-1, max(self.sensors['encoder']['data'])+1 ])
		pyplot.ylim([ min(x for x in self.sensors[sensor_name]['data'] if x is not None)-0.5,
			max(x for x in self.sensors[sensor_name]['data'] if x is not None)+0.5 ])
		pyplot.title(title[0]+str(value)+title[1])

	def run_loop(self):
		while True:
			encoder,flow,pressure = self.get_frame()
			self.update_encoder(encoder, flow, pressure)
			self.update(flow, encoder, 'flow', title=['Flow: ', ' kg/h'])
			self.update(pressure, encoder, 'pressure', title=['Pressure: ', ' kPa'])

			pyplot.pause(0.2) # let matplotlib breathe fresh air

if __name__ == '__main__':
	Motorbench()
