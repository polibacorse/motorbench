/*
 * motobench.ino
 * Read attached sensors to the Arduino Uno MEGA and convert analog signals to
 * meaningful values.
 *
 * Copyright (c) Giovanni Grieco <giovanni.grc96@gmail.com>,
 *		 Poliba Corse <polibacorse@poliba.it>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * PINS PLACEMENT
 * Encoder    A0
 * Air flow   A1
 * Pressure   A2
 */
float encoder 	= 0.0;
float airflow 	= 0.0;
float pressure  = 0.0;
float v_IN 	= 0.0;

const int DELAY = 333;

void setup(void)
{
	pinMode(A0,INPUT);
	pinMode(A1,INPUT);
	pinMode(A2,INPUT);

	Serial.begin(9600);
}

void loop(void)
{
	encoder = read_encoder(analogRead(A0));
	airflow = read_airflow(analogRead(A1));
	pressure = read_pressure(analogRead(A2));

	Serial.println(
		'E' + (String) encoder +
		'F' + (String) airflow +
		'P' + (String) pressure);

	encoder = 0.0;
	airflow = 0.0;
	pressure = 0.0;
	v_IN = 0.0;

	delay(DELAY);
}

/*
 * Convert meaningless analog value to voltage.
 */
inline float atov(float a)
{
	return a * 5 / 1023;
}

/*
 * Read encoder sensor, convert voltage value in degrees.
 * Linear law from 0.5 to 4.5 V, +/- 0.5% FS
 */
float read_encoder(float aval)
{
	v_IN = atov(aval) - 0.5;

	// 1.76 : 4.5 = x : v_IN
	return v_IN * 1.76 / 4;
}

/*
 * Read MAF sensor, convert voltage value in kg/h.
 * Quadratic polynomia curve, from 1 to 4.5V with +/- 3% accuracy
 */
float read_airflow(float aval)
{
	v_IN = atov(aval);

	return	- 10.3268
		- 70.8735 * v_IN
		+ 153.347 * pow(v_IN, 2)
		- 95.6418 * pow(v_IN, 3)
		+ 27.3203 * pow(v_IN, 4)
		-  2.4999 * pow(v_IN, 5);
}

/*
 * Read PRT 02/03 pressure sensor
 * Approx. linear law. with +/- 1% f.s.o. accuracy
 * Output from 0.25V to 4.75V
 * Known points: (250mV, 17kPa), (2500mV, 61kPa), (4750mV, 105kPa)
 */
float read_pressure(float aval)
{
	v_IN = atov(aval);

	return (v_IN - 0.29) / 0.05114;
}
