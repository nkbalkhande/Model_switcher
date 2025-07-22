from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from flask import flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch
import os
from models import init_db, get_user, register_user, save_chat, get_user_history, get_all_users

# Load environment variables
load_dotenv()
gemini_key = os.getenv('Gemini_key')
groq_key = os.getenv('Groq_key')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Create DB
init_db()

# Define Models
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
    return render_template('index.html', user=session['username'], role=session.get('role'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Block anyone trying to register as admin
        if role == 'admin':
            return "You are not allowed to register as admin."

        user = get_user(username)
        if user:
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
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('home'))
        return "Invalid credentials."
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        new_role = request.form['new_role']

        if get_user(new_username):
            flash('User already exists!')
        else:
            register_user(new_username, new_password, new_role)
            flash('User added successfully!')

    users = get_all_users()
    return render_template('admin.html', user=session['username'], role=session['role'], users=users)


@app.route('/api/process', methods=['POST'])
def process():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    username = session['username']
    model = request.form.get('model', 'gemini')
    user_input = request.form.get('input', '')

    file_text = ""
    uploaded_file = request.files.get('file')
    if uploaded_file:
        filename = secure_filename(uploaded_file.filename)
        file_content = uploaded_file.read().decode('utf-8', errors='ignore')
        file_text = f"\n\n[File Content:]\n{file_content.strip()}\n"

    combined_input = f"{user_input}\n{file_text}".strip()

    history = get_user_history(username, 3)
    context = "\n".join(
        [f"User: {h['input']}\nAI: {h['output']}" for h in history])
    full_input = f"{context}\nUser: {combined_input}" if context else combined_input

    prompt = PromptTemplate(
        template="You are a helpful assistant. Respond to: {user_input}",
        input_variables=["user_input"]
    )
    followup_prompt = PromptTemplate(
        template="Here is the assistant’s initial reply: {first_response}. Now, improve it for clarity and detail.",
        input_variables=["first_response"]
    )
    parser = StrOutputParser()

    gemini_chain = (
        prompt | command_r_model | parser
        | followup_prompt | gemma_model | parser
        | followup_prompt | llama_model | parser
    )

    groq_chain = (
        prompt | llama_model | parser
        | followup_prompt | gemma_model | parser
        | followup_prompt | command_r_model | parser
    )

    branch = RunnableBranch(
        (lambda x: x['model'] == 'gemini', gemini_chain),
        groq_chain
    )

    output = branch.invoke({'user_input': full_input, 'model': model})

    save_chat(username, combined_input, output)

    history_output = get_user_history(username)

    return jsonify({
        'output': output,
        'chat_history': history_output
    })


if __name__ == '__main__':
    app.run(debug=True)
