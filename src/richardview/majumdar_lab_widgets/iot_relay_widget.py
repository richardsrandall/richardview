import numpy as np

from .. import generic_widget
from .. import generic_serial_emulator

class IotRelayWidget(generic_widget.GenericWidget):
    """ Widget for using an Arduino to control a Digital Loggers Internet of Things (IoT) Relay, like this: https://www.digital-loggers.com/iot2.html .
    This can be used for on/off control of pretty much any AC-powered device like a light, fan, or pump.\n

    The arduino is expected to control the IoT relay with a digital output pin and to read serial commands using its built-in USB connection. 
    An arduino nano works well; these typically use mini-B USB connections. The arduino ground and digital output pin get connected to the green connector on the side of the IoT relay. 
    Commands to the arduino are broken up by carriage return and newline characters. The arduino should turn on the IoT relay when the command 'On' is received 
    and turn it off when the command 'Off' is received. Additionally, when the command 'Q' for query is received, it should reply with its status ('On' or 'Off') 
    followed by a newline or carriage return character.\n

    A suitable arduino sketch (program) to control the IoT relay can quickly be written by analogy to this Arduino forum post: https://forum.arduino.cc/t/serial-commands-to-activate-a-digital-output/49036/3

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str

    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port):
        """ Constructor for a Digital Loggers IoT relay controller widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#DD88DD',default_serial_port=default_serial_port,baudrate=9600)
        # Add a dropdown field
        self.mode_options=['On','Off']
        self.add_field(field_type='dropdown', name='Status Selection',label='Selected Status: ',
                       default_value=self.mode_options[0], log=True, options=self.mode_options)
        # Add a readout field
        self.add_field(field_type='text output', name='Actual Status',
                       label='Actual Status: ', default_value='No Reading', log=True)
        # Move the confirm button
        self.move_confirm_button(row=3, column=2)

    def on_serial_open(self,success):
        """If serial opened successfully, do nothing; if not, set readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool
        """
        # If handshake failed, set readout to No Reading
        if not success:
            self.set_field('Actual Status','No Reading')

    def on_serial_query(self):
        """Send a query to the device asking whether it is currently on or off.
        """
        self.get_serial_object().reset_input_buffer()
        self.get_serial_object().write(b'Q\n')

    def on_serial_read(self):
        """Parse the response from the previous serial query and update the display. Return True if valid and False if not.

        :return: True if the response was of the expected format, False otherwise.
        :rtype: bool
        """
        status = (self.get_serial_object().readline()).decode('ascii')
        status = status.replace("\n","")
        status = status.replace("\r","")
        if status=='On':
            self.set_field('Actual Status','On')
            return True
        elif status=='Off':
            self.set_field('Actual Status','Off')
            return True
        else:
            self.set_field('Actual Status','Read Error')
            return False

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Actual Status','No Reading')

    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the arduino.
        """
        selected = self.get_field('Status Selection')
        if selected=='On':
            self.get_serial_object().write(b'On\r\n')
        elif selected=='Off':
            self.get_serial_object().write(b'Off\r\n')

    def construct_serial_emulator(self):
        """Get the serial emulator to use when we're testing in offline mode.

        :return: An IoT relay serial emulator object.
        :rtype: richardview.majumdar_lab_widgets.iot_relay_widget.IoTRelaySerialEmulator"""
        return IoTRelaySerialEmulator()

class IoTRelaySerialEmulator(generic_serial_emulator.GenericSerialEmulator):
    """Serial emulator to allow offline testing of dashboards containing IoT relay widgets.
    Acts as a Pyserial Serial object for the purposes of the program, implementing a few of the same methods.
    Confirms to console when an on/off command is sent, and otherwise returns a randomly selected 'on' or 'off' status.
    """
    # This class simulates what a real instrument would respond so I can test code on my laptop
    def write(self,value):
        """Write to this object as if it were a Pyserial Serial object. Ignores queries and reports on/off commands to console."""
        if 'Q' in str(value):#Ignore queries
            return
        print("UV LED got command: "+str(value)+"; ignoring.")

    def readline(self):
        """Reads a response as if this were a Pyserial Serial object. The only time readline is called is to check the response to a status query."""
        v = np.random.randint(0,20)
        v = 'On' if v>10 else 'Off'
        v = str(v)+'\r\n'
        return v.encode('ascii')

