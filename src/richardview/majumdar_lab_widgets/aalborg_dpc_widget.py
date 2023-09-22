import numpy as np
from collections import defaultdict
from .. import generic_widget
from .. import generic_serial_emulator

class AalborgDPCWidget(generic_widget.GenericWidget):
    """ Widget for an Aalborg DPC mass flow controller (MFC).
    This widget controls a single MFC via a serial port.\n
    By default, the gas selection dropdown includes a few gases that the author happened to use.
    Aalborg has many, many gas options in its user manual. You can configure the gas options in the constructor.\n
    In practice, the MFC's sometimes bug out when serial commands are sent directly back-to-back, so we use a short delay between queries/commands that are sent.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param default_gas: The default gas that's selected in the dropdown, defaults to 'Ar' for Argon
    :type default_gas: str, optional
    :param gas_options: The list of gas names (strings) that can be selected. Defaults to argon, hydrogen, and methane.
    :type gas_options: list, optional
    :param gas_numbers: The list of gas numbers (integers) corresponding to gas_options according to the Aalborg DPC handbook. Defaults to indices for Ar, H2, and CH4.    
    :type gas_numbers: list, optional
    
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port,default_gas='Ar',
                 gas_options=["Ar","H2","CH4"],gas_numbers=(1,13,15)):
        """ Constructor for an Aalborg DPC mass flow controller widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#00A36C',default_serial_port=default_serial_port,baudrate=9600)
        # Input fields: select gas, mode, setpoint
        self.gas_options=gas_options
        self.gas_numbers=gas_numbers #Indices in the Aalborg MFC list of gases
        self.add_field(field_type='dropdown',name='Gas Selection',
                       label='Select Gas: ', default_value=default_gas, log=True, options=self.gas_options)
        self.mode_options=['Closed','Setpoint','Open']
        self.add_field(field_type='dropdown',name='Mode Selection',
                       label='Select Mode: ',default_value='Closed', log=True, options=self.mode_options)
        self.add_field(field_type='text input', name='Setpoint Entry', label='Enter Setpoint (sccm): ', default_value='0.0',log=True)
        # Output fields: gas status, mode reading, flow reading. move_field is used to make widget more compact.
        self.add_field(field_type='text output',name='Device Gas',label='Actual: ',default_value='None',log=True,column=2,row=3)
        self.add_field(field_type='text output',name='Device Mode',label='Actual: ',default_value='None',log=True,column=2,row=4)
        self.add_field(field_type='text output',name='Device Setpoint',label='Actual: ',default_value='None',log=True,column=2,row=5)
        self.add_field(field_type='text output',name='Actual Flow',label='Actual Flow (sccm): ',default_value='None',log=True)

    def on_serial_open(self,success):
        """If serial opened successfully, do nothing; if not, set readouts to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool
        """
        # If handshake failed, set readouts to 'none'
        if not success:
            for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
                self.set_field(f,'No Reading')
        pass

    def on_serial_query(self):
        """Send four queries to the serial device asking for the gas selection, mode, setpoint, and actual flow rate.
        Mode refers to open, closed, or setpoint.
        """
        s = self.get_serial_object()
        # Queries serial for all the desired values
        queries = (b'G\r',b'V,M\r',b'SP\r',b'FM\r') #Gas, mode, setpoint, flow rate)
        write_delay = 10 #Milliseconds to wait; this device glitches a bit if commands are sent back-to-back.
        s.reset_input_buffer()
        delay = 0
        for query in queries:
            s.write(query)

    def on_serial_read(self):
        """Parse the responses from the previous 4 serial queries and update the display. Return True if valid and False if not.

        :return: True if all 4 responses were of the expected format, False otherwise.
        :rtype: bool
        """
        try:
            # Parse the Gas data
            gas = self.get_serial_object().readline()
            gas = gas[gas.index(':')+1:]
            gas = gas[gas.index(',')+1:gas.index('r')-1]
            self.set_field('Device Gas',gas)
            # Parse the Mode data
            mode_status = self.get_serial_object().readline()
            mode_start = mode_status.index("VM")
            mode_end = mode_status.index('r')
            mode_status = mode_status[mode_start+3:mode_end-1]
            if mode_status == "C": # syntax from MFC
                mode_status = "Closed" # syntax for GUI
            if mode_status == "A":
                mode_status = "Setpoint"
            if mode_status == "O":
                mode_status = "Open"
            self.set_field('Device Mode',mode_status)
            # Parse the Setpoint data
            setpoint_status = self.get_serial_object().readline()
            setpoint_start = setpoint_status.index("SP")
            setpoint_end = setpoint_status.index("r")
            setpoint_status = setpoint_status[setpoint_start+3:setpoint_end-1]
            setpoint_value = max(0,float(setpoint_status))
            setpoint_str = "{:.1f}".format(setpoint_value)
            self.set_field('Device Setpoint',setpoint_status)
            # Parse the flow data
            flow_status = self.get_serial_object().readline()
            flow_start = flow_status.index(">")
            flow_end = flow_status.index("r")
            flow_status = flow_status[flow_start+1:flow_end-1]
            flow_value = (max(0,float(flow_status)))
            flow_str = "{:.1f}".format(flow_value)
            self.set_field('Actual Flow',flow_str)
        except Exception as e:
            for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
                self.set_field(f,'Read Error')
            return False
        return True
            
    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
            self.set_field(f,'None')

    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the MFC.
        Prints warnings to console if the entered parameters are invalid.
        """
        s = self.get_serial_object()
        # Update the MFC gas:
        gas = self.get_field('Gas Selection')
        g = gas
        if not(gas in self.gas_options):
            print("\"Confirm\" pressed with no/invalid gas option selected.")
            return
        gas = str(self.gas_numbers[self.gas_options.index(gas)]).encode('ascii')
        s.write(b'G,'+gas+b'\r')
        # Update the mode:
        mode=self.get_field('Mode Selection')
        m = mode
        change_sp = (mode=='Setpoint')
        if not(mode in self.mode_options):
            print("\"Confirm\" pressed with no/invalid mode option selected.")
            return
        mode_chars = ("C","A","O")
        mode = str(mode_chars[self.mode_options.index(mode)]).encode('ascii')
        s.write(b'V,M,'+mode+b'\r')
        # Update the setpoint if needed:
        if change_sp:
            try:
                setpoint = (self.get_field('Setpoint Entry'))
                sp = setpoint
                setpoint = float(setpoint)
                setpoint = '{:.2e}'.format(setpoint)
            except Exception as e:
                print("Enter setpoint number as an int or float.")
                return
            setpoint=setpoint.encode('ascii')
            s.write(b'SP,'+setpoint+b'\r')
        # Print to console
        print("MFC '"+str(self.name)+"' set to gas "+g+", mode "+m+((", setpoint "+sp+" sccm.") if change_sp else '.'))

    def construct_serial_emulator(self):
        """Get the serial emulator to use when we're testing in offline mode.

        :return: An Aalborg DPC serial emulator object.
        :rtype: richardview.majumdar_lab_widgets.aalborg_dpc_widget.AalborgDPCSerialEmulator"""
        return AalborgDPCSerialEmulator()

class AalborgDPCSerialEmulator(generic_serial_emulator.GenericSerialEmulator):
    """Serial emulator to allow offline testing of dashboards containing Aalborg DPC mass flow controllers.
    Acts as a Pyserial Serial object for the purposes of the program, implementing a few of the same methods. Has a fake 'input buffer' 
    where responses to queries from a fake 'MFC' are stored.\n
    Serial queries are answered with a fixed gas (Ar), a fixed mode (Setpoint), a fixed setpoint (100 sccm), and a random actual flow (100-104 sccm).
    """
    
    def __init__(self):
        """Create a new serial emulator for an Aalborg DPC."""
        self.output_buffer = []
        self.setpoint=100

    def reset_input_buffer(self):
        """Reset the serial buffer, as if this were a Pyserial Serial object."""
        self.output_buffer = []

    def write(self,value):
        """Write to this object as if it were a Pyserial Serial object. Adds appropriate responses to a fake input buffer.

        :param value: The string to write, encoded as ascii bytes.
        :type value: bytes"""
        queries = (b'G\r',b'V,M\r',b'SP\r',b'FM\r')
        if value not in queries:
            return b'B:$\r'#A nonsense reply
        setpoint_str = 'SP:'+str(self.setpoint)+'\r'
        reading_str = '>'+str(self.setpoint+np.random.randint(0,5))+'\r'
        responses = (b'G:1,AR\r',b'VM:Setpoint\r',setpoint_str.encode('ascii'),reading_str.encode('ascii'))
        self.output_buffer.append(str(responses[queries.index(value)]))

    def readline(self):
        """Reads a response from the fake input buffer as if this were a Pyserial Serial object.

        :return: The next line in the fake input buffer.
        :rtype: str"""
        return self.output_buffer.pop(0)

    def readlines(self):
        """Reads all responses from the fake input buffer as if this were a Pyserial Serial object.

        :return: A list of lines in the fake input buffer.
        :rtype: list"""
        out = list(self.output_buffer)
        self.output_buffer = []
        return out

    def close(self):
        """Close the object as if this were a Pyserial Serial object."""
        pass

