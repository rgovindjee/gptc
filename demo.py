from langchain.schema import HumanMessage
from langchain.chat_models import AzureChatOpenAI
from dotenv import dotenv_values

#Load environment file for secrets.
secrets = dotenv_values(".env")  

#Define llm parameters
llm = AzureChatOpenAI(
    deployment_name=secrets['model'],
    openai_api_version=secrets['API_VERSION'],
    openai_api_key=secrets['OPENAI_API_KEY'],
    openai_api_base=secrets['openai_api_base'],
    openai_organization=secrets['OPENAI_organization']
    )

#Ask a query
msg = HumanMessage(content="Explain step by step. Where is the University of Michigan?")

#Get and print response
response = llm(messages=[msg])
print(response.content)