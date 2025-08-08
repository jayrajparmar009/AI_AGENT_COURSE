from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr


# Load all the api keys

load_dotenv(override=True)

openai = OpenAI()


# Reading data from linkedin generated pdf
from pathlib import Path

base_dir = Path.cwd()
# pdf_path = base_dir / '1_foundation' / 'me' / 'linkedin.pdf'
reader = PdfReader('me/linkedin.pdf')
# reader = PdfReader(str(pdf_path))
linkedin = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text


# Reading the summary text from own file

summary_path = 'me/summary.txt'
with open(summary_path,"r", encoding="utf-8") as f:
    summary = f.read()


name = "Jayraj Parmar"

# Creating this system prompt; system prompt can be used to set the context for the chatbot.
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s personal website,\
particularly questions related to {name}'s career, background, skills and experience.\
Your responsibility is to represent {name} for interactions on the website as faithfully as possible.\
You are given a summary of {name}'s background and Linkedin profile which you can leverage to answer questions.\
Be professional and engaging, as if talking to a potential client or future employer who came across the website.\
If you don't know the answer, say so"

system_prompt += f"""## Summary : {summary} ## Linkedin Profile: {linkedin}"""
system_prompt += f"""With this context, please chat with the user, always staying in character as {name}"""


# Creating the chat function that will be used by Gradio to interact with the user
def chat(message, history):
    messages = [{'role':'system','content':system_prompt}] + history + [{'role':'user', 'content':message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content


gr.ChatInterface(chat, type="messages").launch()


# Now we want to be able to evaluate the output of the chatbot. So we will use another LLM to evaluate the answer

# Creating a pydanetic model for the evaluation

from pydantic import BaseModel

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# This is the evaluator_system_prompt that will tell LLM about how to act
evaluator_system_prompt = f"""You are an AI evaluator that decides whether a response to a question is acceptable.\
You are provided with a conversation bewtween a user and an Agent. Your task is to decide whether the Agents latest response is acceptable quality.\
The Agent is playing the role of {name} and is representing {name} on their website.\
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website.\
The Agent has been provided with context on {name} in the form of thier summary and Linkedin details. Here is the information:"""

evaluator_system_prompt += f"""## Summary : {summary} ## Linkedin Profile: {linkedin}"""
evaluator_system_prompt += f"""With this context, please evaluate the Agent's latest response, replying with whether the response is acceptable and your feedback."""


# This is the evaluator_user_prompt asking LLM to evlauate the response based on history and provide with feedback
def evaluator_user_prompt(reply, message, history):
    user_prompt = f"""Here is the conversation between the User and the Agent:\n\n{history}\n\n"""
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


# We will use gemini as our evaluator
import os

gemini = OpenAI(
    api_key = os.getenv("GOOGLE_API_KEY"),
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
)

def evaluate(reply, message, history) -> Evaluation:

    messages = [{"role": "system", "content": evaluator_system_prompt}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed


# Testing out the chatbot with a sample question
messages = [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": "do you hold a patent?"}]
response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
reply = response.choices[0].message.content

evaluate(reply, "Do you hold a patent?", messages[:1])



# Now writting function for rerunning the query if the reply is not acceptable

def rerun(reply, message, history, feedback):
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content



# Creating a fun little function to test if the rerun function works, function below is telling LLM to respond in pig latin if the question
# contains the word patent
    def chat(message, history):
        if "patent" in message:
            system = system_prompt + "\n\nEverything in your reply needs to be in pig latin - \
                it is mandatory that you respond only and entirely in pig latin"
        else:
            system = system_prompt
        messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply =response.choices[0].message.content

        evaluation = evaluate(reply, message, history)
        
        if evaluation.is_acceptable:
            print("Passed evaluation - returning reply")
        else:
            print("Failed evaluation - retrying")
            print(evaluation.feedback)
            reply = rerun(reply, message, history, evaluation.feedback)       
        return reply

gr.ChatInterface(chat, type="messages").launch()