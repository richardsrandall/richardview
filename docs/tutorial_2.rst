Tutorial: Building Your Own Dashboards
=======================================

This section describes how to build a new dashboard out of existing widgets. 
You'd do this if you happen to be using the devices that RichardView comes with widgets for, or if 
you'd previously developed widgets for your devices, but you changed the devices' physical setup and 
consequently need to make a new dashboard. Or, maybe you're still learning, 
in which case building dashboards out of the widgets included with this package is a great place to start.

Building a Basic Dashboard
****************************

This section describes how to build a new dashboard out of existing widgets. 
You'd do this if you happen to be using the devices that RichardView comes with widgets for, or if 
you'd previously developed widgets for your devices, but you changed the devices' physical setup and 
consequently need to make a new dashboard.

The general structure of the code to initialize and launch a dashboard is as follows:

* Import RichardViewDashboard and any widget packages you need
* Initialize the dashboard itself
* Initialize as many widgets as you want and add them to the dashboard
* Define software interlocks, if you want them (a bit more advanced)
* Launch the dashboard

The code to set up a simple dashboard with a title widget and a  widget for an Omega thermocouple looks like this: 

.. code-block:: python

    # Do your imports
    import richardview.majumdar_lab_widgets as mlw
    import richardview.built_in_widgets as biw
    from richardview.dashboard import RichardViewDashboard

    # Create a dashboard object
    dashboard = RichardViewDashboard(dashboard_name = "RichardView Demo",
                                use_serial_emulators=True,
                                polling_interval_ms=1000,
                                window_resizeable=False)

    # Add a title block
    dashboard.add_widget(biw.TitleWidget(dashboard,"RichardView Demo",20),row=0,column=1)

    # Add a thermocouple widget
    tc1 = mlw.OmegaUSBUTCWidget(parent_dashboard=dashboard,
                                name='My Thermocouple',
                                nickname='My TC',
                                default_serial_port='COM14')
    dashboard.add_widget(tc1,row=3,column=3)
    
    # Start the dashboard
    dashboard.start()

You can look in the Documentation tab to see what arguments are required to initialize a dashboard 
or any particular type of widget.

Building a More Complicated Dashboard
*********************************************

Here's the complete code to launch the build-in Demo Dashboard:

.. code-block:: python

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
    # Omit this one for now just to save space

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


Additional Dashboard Features
*********************************

Adding interlocks
''''''''''''''''''

An 'interlock' refers to any function that gets polled once per dashboard update cycle. It could be anything, but 
its intended purpose is to allow the dashboard to check for unsafe or undesireable operating conditions, then either 
mitigate them or notify the user. A safety-related example would be, upon detection of too high a temperature in the reactor, shutting 
down any active automation scripts, stopping the flow of reaction gases, and flowing inert argon instead. A convenience-related 
example would be, upon detection that an important instrument has disconnected during an automation script, pausing the 
automation script and sending yourself an email notification (perhaps using the GmailHelper class described in a later section).

Here's an example of the latter. This code would be inserted in the dashboard initialization .py file, after all widgets 
are added to the dashboard but before ``dashboard.start()`` has been called.

.. code-block:: python

    # Initialize a Gmail helper... see the section below on this class.
    from richardview.utilities.gmail_helper import GmailHelper
    gh = GmailHelper(gmail_address="fake_address@gmail.com",auth_string="app_password",
        destination_emails=['person_1@hotmail.com','12345678910@vtext.com'])
    #Assume 1-234-567-8910 is a cell number on Verizon

    # Define the interlock
    def check_coms_failures_during_script():
        # This is only important while running an automation script
        if dashboard._automation_widget.pause_tasks == True:
            return
        # Test whether communications to the Picarro Spectrometer have failed
        # In this case, the Picarro tracks how many bad readings there have been
        # 10+ bad readings probably means the instrument is crashed or disconnected
        if gui.panels_by_nickname['Picarro CRD'].bad_readings>9:
            # Notify console and pause automation
            print("Picarro CRD Spectrometer appears to have disconnected. Pausing automation and stopping gas flows.")
            dashboard._automation_control_panel._pause_automated_tasks()
            # Return system to safe mode
            dashboard.set_field('Oxygen MFC','Mode Entry','Closed',execute=True)
            dashboard.set_field('Argon MFC','Mode Entry','Closed',execute=True)
            dashboard.set_field('Methane MFC','Mode Entry','Closed',execute=True)
            dashboard.set_field('UV Light','Status Selection','Off',execute=True)
            # Send some notifications
            gh.send_email(subject="RichardView Alert",
                message_body="The Picarro seems to have disconnected. Automation script has been paused. Light and gases are turned off.")

    # Add the interlock to the dashboard
    dashboard.add_interlock(check_coms_failures_during_script)

Launching from an Icon
''''''''''''''''''''''''

It's usually best to write and debug your dashboard from some kind of development environment, but once it works, 
it's nice to have it launch from clicking a shortcut like a standalone desktop app. 
In the first image in the 'gallery' tab, you can see 
the desktop icon that launches that particular RichardView dashboard.

To do this on a PC, take the file in which the dashboard is initialized 
(e.g., 'my_dashboard.py') and change its extension to .pyw (e.g., 'my_dashboard.pyw'). This will suppress opening a 
terminal window when it's opened. Then, right-click this file and create a shortcut, and right-click the shortcut and 
select 'properties' and then click the 'change icon' button. Change the shortcut's icon to whatever you want -- Windows 
comes with various built-in icons, and you can also look for .ico files on the internet that fit the theme of what 
your dashboard does. After the shortcut icon is changed, move it to your desktop.

On a Mac, you can right-click your .py file and say "open with," choose "other," and tell it to always open this file with 
'Python Launcher'. In the Python Launcher preferences, check the 'Run in Terminal Window' box. Double-clicking the .py file 
should now launch the dashboard and a terminal window. Now, right-click the .py file and choose 'Make Alias,' and drag the 
alias to your desktop. Rename the alias if you wish. Finally, copy the icon image file you want to use onto your clipboard.
Right-click the alias and choose 'get info', then click the picture of its current icon in the top-left corner of the 
'get info' window. Hit command-v and the icon should be replaced with the one on your clipboard.

