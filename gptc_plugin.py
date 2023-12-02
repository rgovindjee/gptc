# Script for running the GPTC simulation
from gptc_model import Gptc

""" BlueSky plugin integrating GPTC into BlueSky """
# Import the global bluesky objects. Uncomment the ones you need
from random import randint
from bluesky import core, stack, traf, scr  # , settings, navdb, sim, tools
import numpy as np


### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():
    global gptc
    gptc = GptcPlugin()
    # Configuration parameters
    config = {
        # The name of your plugin
        "plugin_name": "gptc_plugin",
        # The type of this plugin.
        "plugin_type": "sim",
    }
    return config


class GptcPlugin(core.Entity):
    """Example new entity object for BlueSky."""

    def __init__(self):
        super().__init__()
        # All classes deriving from Entity can register lists and numpy arrays
        # that hold per-aircraft data. This way, their size is automatically
        # updated when aircraft are created or deleted in the simulation.
        with self.settrafarrays():
            self.npassengers = np.array([])
        # Make a new controller.
        self.controller = Gptc()
        self.enabled = False

    def create(self, n=1):
        """This function gets called automatically when new aircraft are created."""
        # Don't forget to call the base class create when you reimplement this function!
        super().create(n)
        # After base creation we can change the values in our own states for the new aircraft
        self.npassengers[-n:] = [randint(0, 150) for _ in range(n)]

    @stack.command
    def gptc(self, enable="off"):
        """Enable or disable the GPTC plugin."""
        if enable == "on":
            self.enabled = True
            scr.echo("GPTC plugin enabled")
        elif enable == "off":
            self.enabled = False
            scr.echo("GPTC plugin disabled")

    @core.timed_function(name="example", dt=5)
    def ac_update(self, dt):
        """Periodic update function for our example entity."""
        # stack.stack('ECHO Example update: creating a random aircraft')
        # stack.stack('MCRE 1')
        if not self.enabled:
            return
        # Query the model using simulated data.
        commands = self.controller.get_command(data=None)

        # Send each command to the sim
        for command in commands:
            print("Sending command: ", command)
            stack.stack(command)

        # I want to print the average position of all aircraft periodically to the
        # BlueSky console
        scr.echo(
            "Average position of traffic lat/lon is: %.2f, %.2f"
            % (np.average(traf.lat), np.average(traf.lon))
        )
        # ac  = 'MY_AC'
        # wpt = 'SPY'
        # stack.stack('ADDWPT %s %s' % (ac, wpt))
