

import richardview.majumdar_lab_widgets as mlw
import richardview.built_in_widgets as biw
from richardview.dashboard import RichardViewDashboard

def run_demo_dashboard():
    """Run a demo dashboard, configured for offline use via serial emulators, including 
    widgets for a thermocouple, two MKS MFC's, an Aalborg MFC, an Picarro spectrometer, 
    and an ultraviolet light controlled via an IoT relay. Intended for early learning of 
    how to use a RichardView dashboard."""

    # How to construct a dashboard:
    # - Define all of the widgets you want
    # - Load them into your window, specifying grid positions
    # - Remember that Column 1 is reserved for system GUI elements

    # Create a dashboard object
    dashboard = RichardViewDashboard(dashboard_name = "RichardView Demo",
                                use_serial_emulators=True,
                                polling_interval_ms=1000,
                                window_resizeable=False)

    # The next many sections initialize each of the individual widgets.

    # Add a title block
    dashboard.add_widget(biw.TitleWidget(dashboard,"RichardView Demo",20),0,1)

    # Add a thermocouple widget
    tc1 = mlw.OmegaUSBUTCWidget(parent_dashboard=dashboard,
                                name='Reactor Thermocouple',
                                nickname='Reactor TC',
                                default_serial_port='COM14')
    dashboard.add_widget(tc1,row=1,column=1)

    # Add an Aalborg MFC
    mfc1=mlw.AalborgDPCWidget(parent_dashboard=dashboard,
                            name='Methane MFC',
                            nickname='Methane MFC',
                            default_serial_port='COM9')
    dashboard.add_widget(mfc1,row=2,column=1)

    # Add an MKS MFC
    mfc_2=mlw.MksMFCWidget(parent_dashboard=dashboard,
                        name='Argon MFC',
                        nickname='Argon MFC',
                        channel='A1',
                        device_id='001',
                        default_serial_port='COM3')
    dashboard.add_widget(mfc_2,row=1,column=2)

    # Add another MKS MFC
    mfc_3=mlw.MksMFCWidget(parent_dashboard=dashboard,
                        name='Oxygen MFC',
                        nickname='Oxygen MFC',
                        device_id='001',
                        channel='A2',
                        widget_to_share_serial_with=mfc_2)
    dashboard.add_widget(mfc_3,row=2,column=2)

    # Add a Valco 2-way valve
    valve_1 = mlw.Valco2WayValveWidget(parent_dashboard=dashboard,
                                    name='Reactor Bypass Valve',
                                    nickname='Reactor Bypass Valve',
                                    default_serial_port='COM11',
                                    valve_positions=['Thru Reactor','Bypass Reactor'])
    #dashboard.add_widget(valve_1,row=1,column=1)
    # Omit for now just to save space

    # Add an UV LED controller controlled with an IoT relay
    uv_led_1 = mlw.IotRelayWidget(parent_dashboard=dashboard,
                                name='UV Light',
                                nickname='UV Light',
                                default_serial_port='COM10')
    dashboard.add_widget(uv_led_1,row=0,column=2)

    # Add a Picarro Cavity Ringdown Spectrometer
    picarro_1 = mlw.PicarroCRDWidget(parent_dashboard=dashboard,
                                name='Picarro',
                                nickname='Picarro',
                                default_serial_port='COM2')
    dashboard.add_widget(picarro_1,row=3,column=1)

    # Add a demo for a widget without a serial connection
    spice_1 = biw.SpicinessWidget(parent_dashboard=dashboard,
                                name='Spice-O-Meter',
                                nickname='Spice')
    dashboard.add_widget(spice_1,row=3,column=2)

    # Here's where you'd add interlocks, if you wanted any

    # Start the dashboard
    dashboard.start()









