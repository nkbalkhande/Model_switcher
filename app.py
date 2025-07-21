from models import init_db, register_user, get_user
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ✅ Load environment variables
load_dotenv()
gemini_key = os.getenv('Gemini_key')
groq_key = os.getenv('Groq_key')

# ✅ Import DB functions from models.py

# ✅ Initialize Flask app and DB
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
init_db()  # creates users.db and users table if not exist

# ✅ Define Models
gemini_model = ChatGoogleGenerativeAI(
    model='gemini-1.5-flash', google_api_key=gemini_key)
llama_model = ChatGroq(model='llama3-70b-8192', api_key=groq_key)
command_r_model = ChatGroq(model='llama3-8b-8192', api_key=groq_key)
gemma_model = ChatGroq(model='deepseek-r1-distill-llama-70b', api_key=groq_key)
mixtral_model = ChatGroq(model='mixtral-8x7b-32768', api_key=groq_key)


@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        existing_user = get_user(username)
        if existing_user:
            return "User already exists. Please login."

        register_user(username, password, role)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['role'] = user[3]
            return redirect(url_for('home'))
        return "Invalid credentials."
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ✅ In-memory chat history (can be replaced with DB later)
chat_history_db = {}  # username: list of {'input': ..., 'output': ...}


@app.route('/api/process', methods=['POST'])
def process():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    username = session['username']
    data = request.json
    model = data.get('model', 'gemini')
    user_input = data.get('input', '')

    # Retrieve user history
    history = chat_history_db.get(username, [])
    last_turns = history[-3:]
    context = "\n".join(
        [f"User: {h['input']}\nAI: {h['output']}" for h in last_turns])
    full_input = f"{context}\nUser: {user_input}" if context else user_input

    # Prompt templates
    prompt = PromptTemplate(
        template="You are a helpful assistant. Respond to: {user_input}",
        input_variables=["user_input"]
    )
    followup_prompt = PromptTemplate(
        template="Here is the assistant’s initial reply: {first_response}. Now, improve it for clarity and detail.",
        input_variables=["first_response"]
    )
    parser = StrOutputParser()

    # Model chains
    gemini_chain = (
        prompt | gemini_model | parser
        | followup_prompt | command_r_model | parser
        | followup_prompt | gemma_model | parser
        | followup_prompt | llama_model | parser
    )

    groq_chain = (
        prompt | llama_model | parser
        | followup_prompt | gemma_model | parser
        | followup_prompt | command_r_model | parser
        | followup_prompt | gemini_model | parser
    )

    branch = RunnableBranch(
        (lambda x: x['model'] == 'gemini', gemini_chain),
        groq_chain
    )

    # Run chain
    output = branch.invoke({'user_input': full_input, 'model': model})

    # Store in chat history
    chat_history_db.setdefault(username, []).append({
        'input': user_input,
        'output': output
    })

    return jsonify({
        'output': output,
        'history': chat_history_db[username][-5:]
    })


if __name__ == '__main__':
    app.run(debug=True)
