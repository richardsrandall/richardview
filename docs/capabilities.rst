Capabilities
========================

A RichardView dashboard consists of multiple widgets, most of which represent a physical device. 
Using a dashboard, a user can easily monitor and control multiple devices' states, providing a single 
control panel for a multi-instrument experimental setup. Our goal is to enable graduate students and 
other researchers with basic Python knowledge to quickly equip experimental setups with data acquisition and 
automated control, allowing higher-quality and higher-throughput experimentation.

These are the software's core features:

* Many physical devices' states can be polled and reported to a single interface every second (or some other interval).
* The states of all those devices can be logged 
  to a .csv file suitable for analysis in Python, Matlab, 
  Excel, or other tools. 
* Widgets can also be controlled automatically according to an automation script. 
  Automation scripts are written in Python as standalone .py files using Python control structures and a simple set of functions.
* It is possible to define software interlocks that return the system to 
  a safe state, notify the user via email or text, 
  or otherwise respond when unsafe or undesireable conditions are detected. 
* It is fairly easy to create scripts that live-plot the contents of a RichardView logfile as the logfile is updated, 
  helping to visualize an experiment's progress.

Currently, RichardView comes with widgets for the following devices:

* Aalborg DPC mass flow controllers
* MKS Mass Flo Controllers, controlled by an MKS 946 Vacuum System Controller
* Picarro G2210-i Cavity Ringdown Spectrometer for CH4, CO2, H2O, and C2H6 (logging only)
* Digital Loggers IoT Relay 2, which can give on/off control of many types of AC devices
* Omega USB-UTC Thermocouple Adapter
* VICI Valco Automatic 2-Way Selector Valve
* VICI Valco Automatic 8-Way Selector Valve
* SRI 8610C Gas Chromatographs

We hope that RichardView users will write and share widgets to control their own devices, eventually creating an ecosystem 
of available widgets that others can use. 
Using the procedures outlined in the tutorial section, it is straightforward to write a new widget to control (or, if that is impractical, to simply log data from) a given physical device. 
Most often, this means writing a widget that queries the device via a serial port. One can determine whether this is possible by consulting a device's manual and looking for a 
'serial,' 'RS232,' 'RS485,' or equivalent interface.

One can also write a widget that watches a specific computer file for updates, then 
displays those values in a widget. This is useful for devices like gas chromatographs that are far too complicated to control entirely via a user-written serial protocol, but that log 
data to a specific file, and whose data it would be convenient to log along with the data from all the dashboard-controlled instruments. See the Tutorial subsection on the GenericWidget class.

It would also be quite easy to write widgets to control DC or stepper motors, using any of a number of commercially available USB-controlled H-bridge or stepper motor driver circuits. 
We have not done this yet, but note it because it opens the door to controlling custom electromechanical devices.
It's also easy to write widgets to interface with user-created Arduino devices, as with the IoTRelayWidget in the majumdar_lab_widgets package. 
It also shouldn't be too hard to implement Modbus support, but we haven't done so yet.

Note that RichardView was designed to sample only once per second. It might be able to sample a little faster, but not a lot faster. 
If you need more than 5 Hz sampling, you should probably look into other data acquisition and control schemes. A workaround for 
data acquisition might be a device that 'buffers' between the sensor and RichardView, aggregating many data points and then sending 
them all to RichardView when it queries once per second.
