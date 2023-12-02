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
            openai_organization=secrets["OPENAI_organization"],  # U-M shortcode
        )
        self.prompt_header = "Act as an air traffic controller. \
                                Your job is to issue a command to each aircraft, helping them land and avoid collisions. \
                                Keep responses short and in the format <aircraft>: <heading> <flight level> <latitude> <longitude> \n\
                                The threshold for runway 22L is located at 130.0, 65.0, at FL0 and heading 220.\n\
                                The following is a list of aircraft in the area:\n"
        self.retry_message = "Please try again. Keep responses short and in the format <aircraft>: <heading> <flight level> <latitude> <longitude>. Give one line per aircraft."
        self.max_retry = 2

    def parse_radar_data(self, data):
        """
        Parse the air traffic data.
        Generate a natural-language representation of the air traffic data.
        """
        # TODO(rgg): parse the data from a real simulation.
        parsed_data = "Aircraft UA34 is at 123.5, 64.3 with heading 90 at flight level 100, landing at runway 22L.\n\
                        Aircraft DL33 is at 115.5, 55.6 with heading 270 at flight level 100, landing at runway 22L.\n\
                        Aircraft UA32 is at 153.5, 45.4 with heading 130 at flight level 200, landing at runway 22L.\n\
                        "
        return parsed_data

    def get_command(self, data):
        """
        Takes in sim data and returns a command.
        """
        # Convert raw sim data to natural language.
        nl_data = self.parse_radar_data(data)
        # Assemble the prompt.
        prompt = self.prompt_header + nl_data
        msg = HumanMessage(content=prompt)
        # Ask the query.
        response = self.llm(messages=[msg])
        # Check response meets the required format for sim.
        # Retry with error message if response is not valid.
        retry_count = 0
        while retry_count < self.max_retry:
            if self.response_valid(response.content):
                break
            else:
                print("Invalid response. Retrying...")
                response = self.llm(messages=[msg])
                retry_count += 1
        return response.content

    def response_valid(self, response):
        """
        Parse the response from the model.
        """
        lines = response.split("\n")
        # Check that all lines are short enough.
        # TODO(rgg): check that all lines are in the correct format.
        line_count_valid = len(lines) == 3
        if not line_count_valid:
            print("Wrong number of lines.")
        line_length_valid = True
        for line in lines:
            if len(line) > 30:
                print("Line too long.")
                line_length_valid = False
        return line_count_valid and line_length_valid
