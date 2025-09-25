from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json, os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from steganography import encode_image, decode_image
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# ---------------- Data Management ----------------
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def load_chats():
    try:
        with open('chats.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_chats(chats):
    with open('chats.json', 'w') as f:
        json.dump(chats, f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_as_png(uploaded_file):
    """
    Save uploaded image as PNG in the uploads folder.
    Returns the new PNG filename (safe).
    """
    filename = secure_filename(uploaded_file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    uploaded_file.save(temp_path)

    # Convert to PNG to avoid lossy formats breaking LSB
    img = Image.open(temp_path)
    img = img.convert('RGB')
    png_filename = os.path.splitext(filename)[0] + '.png'
    png_path = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
    img.save(png_path, format='PNG')

    # Clean up original if it was not png
    if temp_path != png_path and os.path.exists(temp_path):
        os.remove(temp_path)

    return png_filename, png_path

# ---------------- Routes ----------------
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if any(user['username'] == username for user in users):
            return render_template('register.html', error="Username already exists")

        hashed_password = generate_password_hash(password)
        users.append({'username': username, 'password': hashed_password})
        save_users(users)

        return render_template('register.html', success=True)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        for user in users:
            if user['username'] == username and check_password_hash(user['password'], password):
                session['username'] = username
                return redirect(url_for('chat'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    chats = load_chats()

    if request.method == 'POST':
        receiver = request.form['receiver'].strip()
        message = request.form['message'].strip()
        hidden_message = request.form['hidden_message'].strip()
        image = request.files.get('image')

        if not receiver or not message:
            return render_template('chat.html', username=username, chats=[], error="Receiver and message are required")

        users = load_users()
        if not any(u['username'] == receiver for u in users):
            return render_template('chat.html', username=username, chats=[], error="Receiver does not exist")

        image_filename = None
        decoded_message = None

        if image and allowed_file(image.filename):
            try:
                image_filename, image_path = save_as_png(image)

                # Encode hidden message into PNG
                encoded_image = encode_image(image_path, hidden_message)
                encoded_image.save(image_path, format='PNG')

                # Decode immediately for confirmation
                decoded_message = decode_image(image_path)
            except Exception as e:
                import traceback
                print("Full traceback:\n", traceback.format_exc())
                return f"Internal server error: {e}", 500

        # Find or create chat
        chat = next((c for c in chats if set([c['user1'], c['user2']]) == {username, receiver}), None)
        if not chat:
            chat = {'user1': username, 'user2': receiver, 'messages': []}
            chats.append(chat)

        chat['messages'].append({
            'sender': username,
            'message': message,
            'image': image_filename,
            'decoded_message': decoded_message
        })
        save_chats(chats)

    user_chats = [c for c in chats if username in [c['user1'], c['user2']]]
    return render_template('chat.html', username=username, chats=user_chats)

@app.route('/encode_message', methods=['POST'])
def encode_message():
    image = request.files['image']
    message = request.form['message']
    if image and allowed_file(image.filename):
        filename, image_path = save_as_png(image)
        encoded_image = encode_image(image_path, message)
        encoded_image.save(image_path, format='PNG')
        return jsonify({'message': 'Image encoded successfully!', 'image': filename})
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/decode_message', methods=['POST'])
def decode_message_route():
    image = request.files['image']
    if image and allowed_file(image.filename):
        filename, image_path = save_as_png(image)
        decoded_message = decode_image(image_path)
        return jsonify({'decoded_message': decoded_message})
    return jsonify({'error': 'Invalid file'}), 400

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
