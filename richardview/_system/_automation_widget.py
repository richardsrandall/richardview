from tkinter import *
from tkinter import messagebox
from tkinter import filedialog as fd
from datetime import timedelta
import time
import traceback

# Widget for automated programs (this one is a little bit complicated!)
class AutomationWidget:
    """ This widget contains buttons to show/hide the console (on PC's), show/hide all the other widgets' serial controls, 
    print automation help to the console, and open help/tutorials.

    :param parent: The dashboard to which this widget will be added.
    :type parent: richardview.dashboard.Dashboard
    """

    def __init__(self, parent_dashboard):
        """"Constructor for a AutomationWidget"""
        self.parent = parent_dashboard
        self.root = parent_dashboard.get_tkinter_object()
        self.main_color = '#FF7F7F'
        # Lay out all the tkinter elements
        self.frame = Frame(self.root,highlightbackground=self.main_color, highlightcolor=self.main_color, highlightthickness=5)
        Label(self.frame,text="Automation Control ").grid(row=1,column=1,sticky='nesw')
        self.automation_running_label = StringVar()
        Label(self.frame,textvariable=self.automation_running_label).grid(row=1,column=2,sticky='nesw')
        self.file_loaded = StringVar()
        self.file_loaded.set("No file loaded.")
        Label(self.frame,textvariable=self.file_loaded).grid(row=2,column=1,sticky='nesw')
        self.lines_loaded = StringVar()
        Label(self.frame,textvariable=self.lines_loaded).grid(row=3,column=1,sticky='nesw')
        Label(self.frame,text="Next action in: ").grid(row=4,column=1,sticky='nesw')
        Label(self.frame,text="Time remaining: ").grid(row=5,column=1,sticky='nesw')
        self.step_countdown_readout = StringVar()
        self.step_countdown_readout.set("0:00:00")
        Label(self.frame,textvariable=self.step_countdown_readout).grid(row=4,column=2,sticky='nesw')
        self.time_to_go_readout = StringVar()
        self.time_to_go_readout.set("0:00:00")
        Label(self.frame,textvariable=self.time_to_go_readout).grid(row=5,column=2,sticky='nesw')
        self.script_load_button = Button(self.frame,text="    Load    ",command=self._load_automation_file)
        self.script_load_button.grid(row=2,column=2,sticky='nesw')
        self.start_button_text = StringVar()
        self.script_start_button = Button(self.frame,textvariable=self.start_button_text,command=self._start_automated_tasks)
        self.script_start_button.grid(row=3,column=2,sticky='nesw')
        self.script_pause_button = Button(self.frame,text="Pause",command=self._pause_automated_tasks)
        self.script_pause_button.grid(row=2,column=3,sticky='nesw')
        self.script_stop_button = Button(self.frame,text="    Stop    ",command=self._stop_automated_tasks)
        self.script_stop_button.grid(row=3,column=3,sticky='nesw')
        Label(self.frame,text="        ").grid(row=5,column=3,sticky='nesw')

        # Define some automation variables
        self.delay_for_loading = 0 # Keep track of accumulated delay when using schedule_delay function
        self.delay_list = [] # List of delay intervals, in seconds
        self.absolute_time_list = [] # List of system times, in seconds
        self.lambda_list = [] # List of lambda functions to call
        self.automation_index = 0 # What step of the automation we're on
        self.seconds_to_next_task = 0 # Persistent countdown variable
        self.time_to_go = 0 # Total time remaining in recipe
        self.pause_tasks = True
        self._buttons_stopped_mode()
        self.end_time = 0

    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame
    
    def get_parent_dashboard(self):
        """Get the automation widget's parent Dashboard object.
        
        :return: The Dashboard to which this widget was added
        :rtype: richardview.dashboard.Dashboard"""

    def schedule_delay(self, delay):
        """This function is meant to be called in automation scripts. It causes a delay before a subsequent call to schedule_function 
        or schedule_action is executed. It fills a role in an automation script similar to time.sleep() in a Python program.

        In the automation script, you can just say 'schedule_delay(...)'; you don't need to say 'dashboard.automation_widget.schedule_delay(...)' 
        or similar.

        :param delay: The delay in hh:mm:ss format
        :type delay: str
        """
        h,m,s = delay.split(":") # Delay is expected as a string in 0:00:00 format.
        delay_to_add = 3600*int(h)+60*int(m)+int(s)
        self.delay_for_loading+=delay_to_add

    def schedule_function(self, function):
        """This function is meant to be called in automation scripts. It executes whatever function is passed after any delay that 
        has been caused by preceding calls to schedule_delay. If you are trying to change a widget field and then confirm the change, 
        it's better to use schedule_action -- this method is meant to let you execute arbitrary functions at a scheduled time within 
        an automation script, e.g. printing a widget's instance variable to the console.\n

        In the automation script, you can just say 'schedule_function(...)'; you don't need to say 'dashboard.automation_widget.schedule_function(...)' 
        or similar.

        :param function: The function to be executed at the scheduled time
        :type function: function
        """
        if len(self.delay_list)==0:
            self.seconds_to_next_task = self.delay_for_loading
        self.delay_list.append(self.delay_for_loading)
        self.delay_for_loading=0
        self.lambda_list.append(function)
        self.time_to_go = sum(self.delay_list)

    def schedule_action(self, target_widget_nickname, target_field_name, new_target_value, confirm=True):
        """This function is meant to be called in automation scripts. It changes the target field in the target widget to a certain value, 
        then optionally executes that widget's confirm function. It's useful for scheduling most simple automation tasks, e.g., flipping a valve 
        at a certain time.\n
        
        If you want to change multiple fields on a widget, make several consecutive calls to schedule_action, with confirm=False on all 
        but the last and confirm=True on the last. That way, the widget's confirm function is only executed once all its fields have been set properly.\n

        In the automation script, you can just say 'schedule_action(...)'; you don't need to say 'dashboard.automation_widget.schedule_action(...)' 
        or similar.

        :param target_widget_nickname: The nickname of the widget whose field you want to change.
        :type target_widget_nickname: str
        :param target_field_name: The name of the widget field that you want to change.
        :type target_field_name: str
        :param new_target_value: The new value to which the target field should be set. Numbers should be typecast to str first.
        :type new_target_value: str
        :param confirm: True if the target widget's confirm method should be called after updating the field; False if not.
        :type confirm: bool, optional
        """
        target_widget=self.parent.widgets_by_nickname[target_widget_nickname]
        if not (target_field_name in target_widget.attributes.keys()):
            print("Error loading action to change field "+target_field_name+" in widget "+target_widget_nickname+": no such field exists. If you need to change a variable that's not a field, use schedule_function, not schedule_action.")
            raise Exception("Can't find the specified field to automate.")
        # Try first to find a field with that name; if not, set an object with that name
        confirm_function = (target_widget.confirm if confirm else None)
        self.schedule_function(lambda: self._schedule_helper(target_widget, target_field_name, new_target_value, confirm_function))

    # This function exists to generate lambda functions that are put in a queue to call on schedule for automation
    def _schedule_helper(self, target_widget, field_name, new_target_value, confirm_function):
        """This is used to generate function objects that will be executed at a future time as a result of the schedule_action method
        
        :param target_widget: The widget whose field you want to change.
        :type target_widget: richardview.generic_widget.GenericWidget
        :param field_name: The name of the widget field that you want to change.
        :type field_name: str
        :param new_target_value: The new value to which the target field should be set. Numbers should be typecast to str first.
        :type new_target_value: str
        :param confirm_function: The widget's confirm function, or None if no confirm function should be executed.
        :type confirm_function: function
        """
        old_value = target_widget.get_field(field_name)
        target_widget.set_field(field_name, new_target_value)
        print("Automatic script switched value \""+old_value+"\" to \""+new_target_value+"\".")
        if not (confirm_function is None):
            confirm_function()

    # Button handling methods

    def _update_tasks(self):
        """This function gets called every polling interval and checks whether it's time to execute 
        the next task(s) in the automation queue. There's some other machinery to handle pausing the script and 
        update GUI components like the 'n out of m steps done' and 'xx:xx:xx to go' readouts.
        """
        if self.pause_tasks:
            return
        if time.time() > self.absolute_time_list[self.automation_index]:# It's time to execute a task
            execute_me = self.lambda_list[self.automation_index]
            try:
                if execute_me.__code__.co_argcount==0:
                    execute_me()
                else:
                    execute_me(self.parent)
            except Exception as e:
                print("Error in user-provided function called as part of automation script:")
                print(traceback.format_exc())
            self.automation_index += 1
            self.lines_loaded.set(str(self.automation_index)+"/"+str(len(self.delay_list))+" steps done.")
            if self.automation_index >= len(self.delay_list): # Script is finished; reset everything
                self.automation_index = 0 
                self.seconds_to_next_task = 0 if (len(self.delay_list)==0) else self.delay_list[0]
                self.time_to_go = sum(self.delay_list)
                self.pause_tasks = True
                self.step_countdown_readout.set(str(timedelta(seconds=self.seconds_to_next_task)))
                self.time_to_go_readout.set(str(timedelta(seconds=self.time_to_go)))
                self._buttons_stopped_mode()
                self.automation_running_label.set("(finished!)")
                self.lines_loaded.set("0/"+str(len(self.delay_list))+" steps done.")
                print("Script successfully finished.")
                return
            else:
                self.seconds_to_next_task = self.delay_list[self.automation_index]
        else:
            self.seconds_to_next_task = int(round(float(self.absolute_time_list[self.automation_index])-time.time()))
        if self.seconds_to_next_task <= 0:
            self.root.after(0,self._update_tasks) # Execute next task immediately if it's got a delay of 0
        else:
            self.root.after(1000,self._update_tasks)
            self.time_to_go = int(round(float(self.end_time)-time.time()))
        self.step_countdown_readout.set(str(timedelta(seconds=self.seconds_to_next_task)))
        self.time_to_go_readout.set(str(timedelta(seconds=self.time_to_go))) # Updatecounters

    def _start_automated_tasks(self):
        """Start an automation script. Generates a list of absolute times at which each action in the 
        automation queue will be executed, and starts calling _update_tasks every second."""
        if len(self.delay_list)==0:
            messagebox.showinfo("","No script is loaded.")
            return
        if not self.parent.serial_connected:
            messagebox.showinfo("","Please open serial communications before starting an automation script.")
            return
        print("Starting automated script.")
        # Populate absolute start times
        t0 = time.time()
        rel_times = []
        for i in range(0, self.automation_index):
            rel_times.append(0)
        rel_times.append(self.seconds_to_next_task)
        for i in range(self.automation_index+1,len(self.delay_list)):
            rel_times.append(self.delay_list[i]+rel_times[i-1])
        self.absolute_time_list = [t+t0 for t in rel_times]
        self.end_time = self.absolute_time_list[len(self.absolute_time_list)-1]
        # Actually start
        self._buttons_running_mode()
        self.pause_tasks = False
        self._update_tasks()

    def _load_automation_file(self): # Open a dialog and load a file for automation
        """Load an automation script from a file. Generates a list of functions and a list of the delays before each one will be 
        executed after starting the script. Sets GUI elements like '0/n steps done' and 'xx:xx:xx remaining'.\n
        
        Note that this method loads the contents of the automation file and calls exec() on it. This is obviously not secure; only use 
        automation scripts whose authors you trues. exec() is called in a namespace with schedule_delay, schedule_action, and schedule_function 
        already defined as local variables for you to use.
        """
        # Reset everything
        self.delay_for_loading = 0
        self.delay_list = []
        self.absolute_time_list = []
        self.lambda_list = []
        self.automation_index = 0
        self.seconds_to_next_task = 0
        self.time_to_go = 0
        self.pause_tasks = True
        self._buttons_stopped_mode()
        self.step_countdown_readout.set(str(timedelta(seconds=self.seconds_to_next_task)))
        self.time_to_go_readout.set(str(timedelta(seconds=self.time_to_go)))
        self.file_loaded.set("No file loaded.")
        self.lines_loaded.set("")
        # Hopefully these all get overwritten; above is just to cover our bases if there's an error.
        filename = fd.askopenfilename()
        f = str.split(filename,'/')
        f = f[len(f)-1] # We just want the file name to display, not its whole path
        script = open(filename).read()
        try:
            exec(script,{}, #We only want certain special keywords in the namespace that is executed
                 {'schedule_delay':self.schedule_delay, 'schedule_action':self.schedule_action,
                  'schedule_function':self.schedule_function, 'get_dashboard':self.get_parent_dashboard})
        except Exception as e:
            print(traceback.format_exc())
            messagebox.showinfo("","The script you loaded contains an error. See console for details.")
            return
        lines = len(self.delay_list)
        self.file_loaded.set("Loaded: "+f)
        self.lines_loaded.set("0/"+str(len(self.delay_list))+" steps done.")
        self.time_to_go = sum(self.delay_list)
        self.seconds_to_next_task = 0 if (len(self.delay_list)==0) else self.delay_list[0]
        self.step_countdown_readout.set(str(timedelta(seconds=self.seconds_to_next_task)))
        self.time_to_go_readout.set(str(timedelta(seconds=self.time_to_go)))
        print("Loaded "+filename)

    # Helper functions to enable/disable buttons

    def _pause_automated_tasks(self):
        """Pause the automation script"""
        print("Pausing automated script.")
        self._buttons_paused_mode()
        self.pause_tasks = True
 
    def _stop_automated_tasks(self):
        """Stop the automation script and go back to the beginning"""
        print("Aborting automated script.")
        self._buttons_stopped_mode()
        self.pause_tasks = True
        self.automation_index = 0
        self.time_to_go = sum(self.delay_list)
        self.seconds_to_next_task = self.delay_list[0]
        self.step_countdown_readout.set(str(timedelta(seconds=self.seconds_to_next_task)))
        self.time_to_go_readout.set(str(timedelta(seconds=self.time_to_go)))
        self.lines_loaded.set("0/"+str(len(self.delay_list))+" steps done.")

    def _buttons_running_mode(self):
        """Disable 'start' and 'load' buttons, turn frame green, add 'running' label."""
        self.script_load_button.configure(state='disabled')
        self.script_start_button.configure(state='disabled')
        self.script_pause_button.configure(state='normal')
        self.script_stop_button.configure(state='normal')
        self.start_button_text.set("Start")
        self.automation_running_label.set("(running)")
        self.frame.configure(highlightbackground='green')

    def _buttons_paused_mode(self):
        """Disable 'pause' and 'load' buttons, turn frame yellow, add 'paused' label."""
        self.script_load_button.configure(state='disabled')
        self.script_start_button.configure(state='normal')
        self.script_pause_button.configure(state='disabled')
        self.script_stop_button.configure(state='normal')
        self.automation_running_label.set("(paused)")
        self.start_button_text.set("Resume")
        self.frame.configure(highlightbackground='yellow')

    def _buttons_stopped_mode(self):
        """Disable 'pause' and 'stop' buttons, turn frame red, add 'inactive' label."""
        self.script_load_button.configure(state='normal')
        self.script_start_button.configure(state='normal')
        self.script_pause_button.configure(state='disabled')
        self.script_stop_button.configure(state='disabled')
        self.automation_running_label.set("(stopped)")
        self.start_button_text.set("Start")
        self.frame.configure(highlightbackground=self.main_color)
