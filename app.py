from flask import Flask, request, jsonify, render_template
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch
from dotenv import load_dotenv
import os

load_dotenv()
gemini_key = os.getenv('Gemini_key')
groq_key = os.getenv('Groq_key')

app = Flask(__name__)

# Configure models
gemini_model = ChatGoogleGenerativeAI(
    model='gemini-1.5-flash',
    google_api_key=gemini_key,
    temperature=0.7
)

groq_model = ChatGroq(
    model='llama3-70b-8192',
    api_key=groq_key
)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    model = data.get('model', 'gemini')
    user_input = data.get('input', '')

    prompt = PromptTemplate(
        template="You are a helpful assistant. Respond to: {user_input}",
        input_variables=["user_input"]
    )

    followup_prompt = PromptTemplate(
        template="Here is the assistant’s initial reply: {first_response}. Now, improve it for clarity and detail.",
        input_variables=["first_response"]
    )

    parser = StrOutputParser()

    # Define the two possible chains
    gemini_chain = prompt | gemini_model | parser | followup_prompt | groq_model | parser
    groq_chain = prompt | groq_model | parser | followup_prompt | gemini_model | parser

    # Create a RunnableBranch that selects the appropriate chain
    branch = RunnableBranch(
        (lambda x: x["model"] == "gemini", gemini_chain),
        groq_chain
    )

    # Invoke with both the input and model selection
    output = branch.invoke({"user_input": user_input, "model": model})

    return jsonify({"output": output})


if __name__ == '__main__':
    app.run(debug=True)
