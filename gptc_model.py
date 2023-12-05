from langchain.schema import HumanMessage
from langchain.chat_models import AzureChatOpenAI
from dotenv import dotenv_values


class Gptc:
    """
    Generative pre-trained traffic controller.
    This class takes in air traffic data, generates a natural-language representation, and outputs a traffic control command.
    """

    def __init__(self):
        # Load the model
        # Load environment file for secrets.
        secrets = dotenv_values(
            ".env"
        )  # Place .env file in the same directory as this file.
        # Define llm parameters
        self.llm = AzureChatOpenAI(
            deployment_name=secrets["model"],  # e.g. gpt-35-turbo
            openai_api_version=secrets["API_VERSION"],  # e.g. 2023-05-15
            openai_api_key=secrets["OPENAI_API_KEY"],  # secret
            azure_endpoint=secrets["azure_endpoint"],  # a URL
            # U-M shortcode
            openai_organization=secrets["OPENAI_organization"],
        )
        self.mode = "hdg"  # Alt, hdg, or both.
        if self.mode == "alt":
            self.prompt_header = "Act as an air traffic controller. \
Your job is to issue a command to each aircraft, avoid collisions while maintaining overall course. \n\
You will be interacting with a program that simulates air traffic. \n\
Please return simulator commands in the form ALT <aircraft> <altitude>\n\
The simulator will throw an error if you do not precisely follow this format, or provide extraneous commentary. \n\
The aircraft in this scenario start at the same altitude and will collide if you don't tell them to go to different altitudes. \n\
The minimum vertical separation distance is 2000 ft. \n\
The minimum horizontal separation distance is 5 nautical miles. \n\
The aircraft prefer to fly at 25000 ft when not close to a collision. \n\
Here is an example of a successful deconfliction procedure: Airplane A and Airplane B are flying directly at eachother at 310 kts and 25000 feet. Before they get too close, A is told to ascend 2000 ft to 27000, while B is told to descend 2000 ft to 23000. The aircraft are still heading towards one another but are at different altitudes. \n\
\nThe following is a list of aircraft in the area: \n"
        elif self.mode == "hdg":
            self.prompt_header = "Act as an air traffic controller. Your job is to issue a command to each aircraft, avoid collisions while maintaining overall course. \
You will be interacting with a program that simulates air traffic. \
Please return simulator commands in the form HDG <aircraft> <heading> \
The simulator will throw an error if you do not precisely follow this format, or provide extraneous commentary. \
The aircraft in this scenario start at the same altitude and will collide if you don't tell them to go to different headings. \
The minimum horizontal separation distance is 15 nautical miles. \
Here is an example of a successful deconfliction procedure: Airplane A and Airplane B are flying directly at each other. Before they get too close, A is told turn north 30 degrees, while B is told to turn south 30 degrees. The aircraft are now heading in different directions. Once they are no longer going to conflict with one another, the aircraft need to resume their previous headings. \
In this case, DL123 prefers to fly at 115.8 degrees, and DL456 prefers to fly at 271.5 degrees."
        else:
            self.prompt_header = "Act as an air traffic controller. \
                                    Your job is to issue a command to each aircraft, helping them land and avoid collisions. \
                                    Keep responses short and in the format <aircraft>: <heading> <flight level> <latitude> <longitude> \n\
                                    The threshold for runway 22L is located at 130.0, 65.0, at FL0 and heading 220.\n\
                                    The following is a list of aircraft in the area:\n"
        self.retry_message = "Please try again. Keep responses short and in the format <aircraft>: <heading> <flight level> <latitude> <longitude>. Give one line per aircraft."
        self.max_retry = 2

    def lon_to_ft(self, lon):
        """Convert longitude degrees to feet."""
        # This is an approximation that works for the US.
        return lon * 268_560.0

    def lat_to_ft(self, lat):
        """Convert latitude degrees to feet."""
        # This is an approximation.
        return lat * 364_488.0

    def parse_radar_data(self, data):
        """
        Parse the air traffic data.
        Data is given as a dictionary with the following keys:
            - id: the aircraft id
        And the following values:
            - lat: latitude in degrees
            - lon: longitude in degrees
            - hdg: heading in degrees
            - alt: altitude in feet
            - gs: ground speed in knots
            - vs: vertical speed in feet per minute
        Generate a natural-language representation of the air traffic data.
        """
        parsed_data = ""
        for id in data:
            parsed_data += f"Aircraft {id} is at lat {data[id]['lat']:.4f}, \
lon {data[id]['lon']:.4f} with heading {data[id]['hdg']:.1f} at altitude {data[id]['alt']:.0f} ft. \
{id} has a groundspeed of {data[id]['gs']:.3f} m/s and vertical speed of {data[id]['vs']:.3f} m/s\n"
        if len(data) == 2:
            ac1 = list(data.keys())[0]
            ac2 = list(data.keys())[1]
            # Calculate the distance between the two aircraft.
            lat_dist = self.lat_to_ft(data[ac1]["lat"] - data[ac2]["lat"])
            lon_dist = self.lon_to_ft(data[ac1]["lon"] - data[ac2]["lon"])
            parsed_data += f"The aircraft are approximately {abs(lon_dist):.3f} ft apart in longitude.\n"
            parsed_data += f"The aircraft are approximately {abs(lat_dist):.3f} ft apart in latitude.\n"
        return parsed_data

    def get_commands(self, data):
        """
        Takes in sim data and returns a command.
        """
        # Convert raw sim data to natural language.
        nl_data = self.parse_radar_data(data)
        # Assemble the prompt.
        prompt = self.prompt_header + nl_data
        print(f"Sending message to model: {prompt}")
        msg = HumanMessage(content=prompt)
        # Ask the query.
        response = self.llm(messages=[msg])
        # Check response meets the required format for sim.
        # Retry with error message if response is not valid.
        print(f"Received response from model: {response.content}")
        retry_count = 0
        while retry_count < self.max_retry:
            if self.response_valid(response.content):
                break
            else:
                print("Invalid response. Retrying...")
                response = self.llm(messages=[msg])
                retry_count += 1
        return response.content.split("\n")

    def response_valid(self, response):
        """
        Parse the response from the model.
        """
        lines = response.split("\n")
        if self.mode == "alt":
            # Check that all lines start with "ALT".
            for line in lines:
                if not line.startswith("ALT"):
                    print("Line does not start with ALT.")
                    return False
        elif self.mode == "hdg":
            # Check that all lines start with "HDG".
            for line in lines:
                if not line.startswith("HDG"):
                    print("Line does not start with HDG.")
                    return False
        # Check that all lines are short enough.
        if self.mode == "alt" or self.mode == "hdg":
            max_line_length = 20
            for line in lines:
                if len(line) > max_line_length:
                    print("Line too long.")
                    return False
            return True
        else:
            line_count_valid = len(lines) == 3
            if not line_count_valid:
                print("Wrong number of lines.")
            line_length_valid = True
            for line in lines:
                if len(line) > 30:
                    print("Line too long.")
                    line_length_valid = False
            return line_count_valid and line_length_valid
