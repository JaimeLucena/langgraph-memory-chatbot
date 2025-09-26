import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
load_dotenv(find_dotenv())
openai_api_key = os.environ["OPENAI_API_KEY"]
chatbot = ChatOpenAI(model="gpt-4o-mini")

messagesToTheChatbot = [
    HumanMessage(content="My favorite color is blue."),
]

response = chatbot.invoke(messagesToTheChatbot)

print("\n----------\n")

print("My favorite color is blue.")

print("\n----------\n")
print(response.content)

print("\n----------\n")

response = chatbot.invoke([
    HumanMessage(content="What is my favorite color?")
])

print("\n----------\n")

print("What is my favorite color?")

print("\n----------\n")
print(response.content)

print("\n----------\n")
