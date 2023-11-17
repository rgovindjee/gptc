from langchain.schema import HumanMessage
from langchain.chat_models import AzureChatOpenAI
from dotenv import dotenv_values

# Load environment file for secrets.
secrets = dotenv_values(".env")  # Place .env file in the same directory as this file.

# Define llm parameters
llm = AzureChatOpenAI(
    deployment_name=secrets['model'],  # e.g. gpt-35-turbo
    openai_api_version=secrets['API_VERSION'],  # e.g. 2023-05-15
    openai_api_key=secrets['OPENAI_API_KEY'],  # secret
    azure_endpoint=secrets['azure_endpoint'],  # a URL
    openai_organization=secrets['OPENAI_organization']  # U-M shortcode
    )

# Ask a query.
msg = HumanMessage(content="Explain step by step. Where is the University of Michigan?")

# Get and print response.
response = llm(messages=[msg])
print(response.content)