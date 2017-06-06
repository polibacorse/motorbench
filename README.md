# Motorbench

## What is Motorbench?
Motorbench helps engineers test motors using sensors such as the encoder,
the flow and the pressure.
The last two sensors are expressed in function of the encoder behaviour and are
displayed on an animated plot.

## Technical details
Encoder is expressed in degrees, flow in kg/h and pressure in kPa.

The software is written in C (for Arduino) and Python (Front-end).
The front-end uses matplotlib to provide plotting functionality and uses
numpy for high performance memory management.

Cables got lost? Need to start from scratch? Please read the
[wiki](https://github.com/polibacorse/motorbench/wiki/Cables-configuration)
to see the configuration.

## System requirements

The software was designed and tested with Python 3.6. To install the required
libraries just type on the terminal

```
$ pip install -r requirements.txt
```

`pip` is the Python Package Manager and it must be installed to provide an
easy package installation.

## How to run
Just plug Arduino on the USB port and do

```
$ python motorbench.py
```

_NOTE_: if the script doesn't see the Arduino, just replace vid and pid codes at
`motorbench.py`.

When you have enough data, press `CTRL+C` on the terminal to stop the program;
it will automatically generate 2 CSV files, one for the flow and one for the
pressure. `nan` values should be treated as values not acquired.

## TODO list

- Practical tests
- Customise plot toolbar by removing buttons
- Add "save graph" button to save CSVs data and a png with Flow/Pressure curves
- If the user close the plot window, close the entire application

## Known bugs

- Memory leak of ~100 kB every 30 s. This can cause instability and saturation.
