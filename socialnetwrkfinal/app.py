from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import os
from werkzeug.utils import secure_filename
from steganography import encode_image, decode_image  # Assuming these functions are in steganography.py

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Load users and chat data
def load_users():
    try:
        with open('backend/users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open('backend/users.json', 'w') as f:
        json.dump(users, f)

def load_chats():
    try:
        with open('backend/chats.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_chats(chats):
    with open('backend/chats.json', 'w') as f:
        json.dump(chats, f)

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if any(user['username'] == username for user in users):
            return "Username already exists", 400

        users.append({'username': username, 'password': password})
        save_users(users)

        return render_template('register.html', success=True)

    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username  # Set session
                return redirect(url_for('chat'))

        return "Invalid credentials", 400

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear session
    return redirect(url_for('index'))

@app.route('/chat', methods=['GET', 'POST'])
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    chats = load_chats()

    if request.method == 'POST':
        receiver = request.form['receiver']
        message = request.form['message']
        hidden_message = request.form['hidden_message']
        image = request.files.get('image')

        # Check if there's an image and process it for steganography
        image_filename = None
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

            # Encode the hidden message into the image
            print(f"Encoding hidden message: {hidden_message}")  # Debug log
            encoded_image = encode_image(image_path, hidden_message)
            encoded_image.save(image_path)

        # Check if a chat exists between sender and receiver, or create a new one
        chat = next((chat for chat in chats if set([chat['user1'], chat['user2']]) == {username, receiver}), None)

        if not chat:
            chat = {'user1': username, 'user2': receiver, 'messages': []}
            chats.append(chat)

        # Decode hidden message if an image was uploaded
        decoded_message = None
        if image_filename:
            try:
                decoded_message = decode_image(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                print(f"Decoded hidden message: {decoded_message}")  # Debug log
            except Exception as e:
                print(f"Error decoding message: {e}")  # Debug log

        # Add the message with the image filename (if any)
        chat['messages'].append({
            'sender': username,
            'message': message,
            'image': image_filename,
            'decoded_message': decoded_message or None
        })
        save_chats(chats)

    user_chats = [chat for chat in chats if session['username'] in [chat['user1'], chat['user2']]]
    return render_template('chat.html', username=username, chats=user_chats)

@app.route('/encode_message', methods=['POST'])
def encode_message():
    image = request.files['image']
    message = request.form['message']

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        encoded_image = encode_image(image_path, message)
        encoded_image.save(image_path)

        return jsonify({'message': 'Image encoded successfully!', 'image': filename})

@app.route('/decode_message', methods=['POST'])
def decode_message():
    image = request.files['image']

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        decoded_message = decode_image(image_path)

        return jsonify({'decoded_message': decoded_message})

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
