# -*- coding: utf-8 -*-

import idaapi
import ida_kernwin
import idc
import ida_diskio
import threading
import time

VERSION = "0.1"
auto_save_enabled = True
auto_save_interval_minutes = 10
auto_save_timer = None

try:
    class AutoSavePlugin(idaapi.action_handler_t):
        def __init__(self):
            idaapi.action_handler_t.__init__(self)
           
        @classmethod
        def get_name(self):
            return self.__name__
        
        @classmethod
        def get_label(self):
            return self.label
            
        @classmethod
        def register(self, plugin, label):
            self.plugin = plugin
            self.label = label
            instance = self()
            return idaapi.register_action(idaapi.action_desc_t(
                self.get_name(),  # Name. Acts as an ID. Must be unique.
                instance.get_label(),  # Label. That's what users see.
                instance  # Handler. Called when activated, and for updating
            ))
            
        @classmethod
        def unregister(self):
            """Unregister the action.
            After unregistering the class cannot be used.
            """
            idaapi.unregister_action(self.get_name())
        
        @classmethod
        def activate(self, ctx):
            # dummy method
            return 1
            
        @classmethod
        def update(self, ctx):
            # if ctx.widget_type == idaapi.BWN_DISASM:
            #     return idaapi.AST_ENABLE_FOR_WIDGET
            # return idaapi.AST_DISABLE_FOR_WIDGET
            return idaapi.AST_ENABLE_FOR_WIDGET
            
    class MenuOption(AutoSavePlugin):
        def activate(self, ctx):
            self.plugin.menuItem()
            return 1
            
except:
    pass
    

p_initialized = False

#--------------------------------------------------------------------------
# Plugin
#--------------------------------------------------------------------------
class AutoSave_Plugin_t(idaapi.plugin_t):
    comment = "Autosave Plugin"
    help = "Enables periodic saving of the IDB."
    wanted_name = "Auto Save"
    flags = idaapi.PLUGIN_KEEP
    
    def init(self):
        global p_initialized

        # register popup menu handlers
        try:
            MenuOption.register(self, "Auto Save")
        except:
            pass
        
        if p_initialized is False:
            p_initialized = True
            auto_save_start()
            idaapi.register_action(idaapi.action_desc_t(
                "Auto Save",
                "Auto Save Interval...",
                MenuOption(),
                None,
                None,
                0))
            idaapi.attach_action_to_menu("File/Save", "Auto Save", idaapi.SETMENU_APP)

        return idaapi.PLUGIN_KEEP

    def term(self):
        pass
        
    def menuItem(self):
        # do stuff here
        global auto_save_interval_minutes
        user_input = ida_kernwin.ask_long(
            auto_save_interval_minutes,
            f"Enter auto-save interval in minutes (current is {auto_save_interval_minutes}, set 0 to disable):"
        )
        if user_input is not None:
            auto_save_interval_minutes = user_input
            if auto_save_interval_minutes == 0:
                auto_save_enabled = False                    
                print(f"Auto-save interval disabled.")
            else:
                idc.save_database("", 1)
                auto_save_enabled = True  
                print(f"Auto-save interval set to {auto_save_interval_minutes} minutes.")
        else:
            print("Invalid input. Auto-save interval remains unchanged.")
    
    def run(self, arg):
        self.menuItem()

def auto_save_handler():
    """
    Timer callback to save the database.
    """
    global auto_save_enabled, auto_save_interval_minutes
    if auto_save_enabled and idaapi.get_root_filename():
        idaapi.execute_sync(save_database, idaapi.MFF_WRITE)
    return 1000 * 60 * auto_save_interval_minutes 
        
def save_database():
    global auto_save_enabled
    # disable this print just for testing
    print("Auto-save running...")
    if not auto_save_enabled:
        return

    if idc.save_database("", 1):
        print("Database saved successfully.")
    else:
        print("Failed to save the database.")
    
def auto_save_start():
    global auto_save_enabled, auto_save_timer
    if auto_save_enabled:
        print(f"Auto-save enabled. Saving every {auto_save_interval_minutes} minutes.")
        auto_save_timer = ida_kernwin.register_timer(1000 * 60 * auto_save_interval_minutes, auto_save_handler)
    else:
        print("Auto-save disabled.")
        
# register IDA plugin
def PLUGIN_ENTRY():
    return AutoSave_Plugin_t()