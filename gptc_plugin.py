# Script for running the GPTC simulation
from gptc_model import Gptc

""" BlueSky plugin integrating GPTC into BlueSky """
# Import the global bluesky objects. Uncomment the ones you need
from random import randint
from bluesky import core, stack, traf, scr  # , settings, navdb, sim, tools
import numpy as np


# Initialization function of your plugin. Do not change the name of this
# function, as it is the way BlueSky recognises this file as a plugin.
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
        self.verbose = False
        # Separation distances. Both must be satisfied for a warning to be issued.
        self.min_lat_separation_distance = 5000  # feet
        self.min_vert_separation_distance = 1000  # feet
        self.scenario_count = 0  # Number of scenarios run so far.
        self.violation_count = 0  # Number of violations detected so far. Resets when a new scenario is loaded.

    def lon_to_ft(self, lon):
        """Convert longitude degrees to feet."""
        # This is an approximation that works for the US.
        return lon * 268_560.0

    def lat_to_ft(self, lat):
        """Convert latitude degrees to feet."""
        # This is an approximation.
        return lat * 364_488.0

    def m_to_ft(self, m):
        """Convert meters to feet."""
        return m * 3.28084

    def create(self, n=1):
        """This function gets called automatically when new aircraft are created."""
        # Don't forget to call the base class create when you reimplement this function!
        super().create(n)
        # After base creation we can change the values in our own states for the new aircraft
        self.npassengers[-n:] = [randint(0, 150) for _ in range(n)]

    @stack.command
    def start_gptc_scenario(self, filename=""):
        """
        Start the scenario
        """
        if filename == "":
            scr.echo("Please specify a scenario filename.")
            return
        # Write a text file with the scenario name, number, and violation count.
        with open("scenario_results.txt", "a", encoding="utf-8") as f:
            f.write(f"{filename},{self.scenario_count},{self.violation_count}\n")
        scr.echo(f"Starting GPTC scenario {filename}")
        stack.stack(f"LOAD {filename}")
        self.violation_count = 0
        self.scenario_count += 1

    @stack.command
    def gptc(self, enable="off"):
        """Enable or disable the GPTC plugin."""
        if enable == "on":
            self.enabled = True
            scr.echo("GPTC plugin enabled")
        elif enable == "off":
            self.enabled = False
            scr.echo("GPTC plugin disabled")

    @core.timed_function(name="separation_listener", dt=0.5)
    def separation_listener(self, dt):
        """
        Periodic update function to check for separation violations.
        """
        # Check if any two aircraft are too close to each other.
        # If so, send a warning to the sim.
        for idx1 in range(traf.ntraf):
            for idx2 in range(idx1 + 1, traf.ntraf):
                lat_dist = np.sqrt(
                    self.lat_to_ft(traf.lat[idx1] - traf.lat[idx2]) ** 2
                    + self.lon_to_ft(traf.lon[idx1] - traf.lon[idx2]) ** 2
                )
                vert_dist = np.abs(traf.alt[idx1] - traf.alt[idx2])
                if (lat_dist < self.min_lat_separation_distance and vert_dist < self.min_vert_separation_distance):
                    stack.stack(
                        "ECHO WARNING: Aircraft %s and %s are too close!"
                        % (traf.id[idx1], traf.id[idx2])
                    )
                    self.violation_count += 1

    @core.timed_function(name="gptc_update", dt=10)
    def gptc_update(self, dt):
        """
        Periodic update function to call GPTC.
        Runs every dt seconds, and only calls GPTC if the plugin is enabled.
        """
        if not self.enabled:
            # stack.stack(f"ECHO GPTC update: disabled")
            return
        # stack.stack(f"ECHO GPTC update: enabled")

        # Extract aircraft data from the simulation.
        # This is a dictionary with the following keys:
        #   - id: the aircraft id
        # And the following values:
        #   - lat: latitude in degrees
        #   - lon: longitude in degrees
        #   - alt: altitude in feet?
        #   - spd: speed in knots?
        #   - hdg: heading in degrees
        if self.verbose:
            for idx in range(traf.ntraf):
                print("Aircraft: ", traf.id[idx])
                print("Lat: ", traf.lat[idx])
                print("Lon: ", traf.lon[idx])
                print("Alt: ", traf.alt[idx])
                print("GroundSpd: ", traf.gs[idx])
                print("VertSpd: ", traf.vs[idx])
                print("Hdg: ", traf.hdg[idx])

        data = {}
        # Assemble traffic data into a dictionary.
        for idx in range(traf.ntraf):
            # TODO(rgg): find what waypoint the aircraft is flying to.
            data[traf.id[idx]] = {
                "lat": traf.lat[idx],
                "lon": traf.lon[idx],
                "alt": self.m_to_ft(traf.alt[idx]),
                "gs": traf.gs[idx],
                "hdg": traf.hdg[idx],
                "vs": traf.vs[idx],
            }

        # Query the model using simulated data.
        commands = self.controller.get_commands(data=data)
        # commands = []

        # Send each command to the sim
        for command in commands:
            print("Sending command: ", command)
            stack.stack(command)
            # TODO(rgg): get sim response and send to model, retrying if needed?
