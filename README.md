#StegoChat 

 StegoChat is a secure chat application built with Flask that allows users to send both normal messages and hidden messages inside images using LSB (Least Significant Bit) steganography.
The project combines web development + image processing + security concepts to show how steganography can be applied in real-world communication.

# Steganography Chat Application

A web-based chat application that allows users to send hidden messages within images using steganography techniques.

## Features

- User registration and login with password hashing
- Real-time chat between users
- Image upload with hidden message encoding
- Decode hidden messages from images
- Secure session management
- Supports common image formats: PNG, JPG, JPEG, GIF


  ##Project Structure

    
      ├── app.py             # Main Flask application
      ├── steganography.py   # Encoding and decoding hidden messages
      ├── templates/         # HTML templates
      │   ├── index.html
      │   ├── login.html
      │   ├── register.html
      │   └── chat.html
      ├── static/            # Static files like uploaded images
      │   └── uploads/
      ├── users.json         # User data storage
      ├── chats.json         # Chat data storage
      └── README.md          # Project documentation

##How It Works

     Users register and log in.
      
     Users can send messages to each other.
     
     If an image is uploaded with a hidden message:
     
     The message is encoded into the image using least significant bit (LSB) steganography.
     
     The receiver can decode the hidden message from the image.

##Dependencies

    Flask
    
    Pillow (PIL)
    
    NumPy
    
    Werkzeug
