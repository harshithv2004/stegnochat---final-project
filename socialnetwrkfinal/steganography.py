from PIL import Image
import numpy as np

# Function to encode a message into an image
def encode_image(image_path, message):
    img = Image.open(image_path)

    # Ensure the image is in RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img_array = np.array(img)
    # Convert the message into binary format and add a stop sequence
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '1111111111111110'  # Stop sequence
    data_index = 0

    print("Message to encode (binary):", binary_message[:100])  # Debugging: show first 100 bits

    # Encode the message into the image
    for row in range(img_array.shape[0]):
        for col in range(img_array.shape[1]):
            for color in range(3):  # Loop through RGB channels
                if data_index < len(binary_message):
                    original_color = img_array[row, col, color]
                    img_array[row, col, color] = (original_color & 0xFE) | int(binary_message[data_index])
                    data_index += 1
                else:
                    break
            if data_index >= len(binary_message):
                break
        if data_index >= len(binary_message):
            break

    # Return the encoded image
    encoded_img = Image.fromarray(img_array)
    print("Encoding complete, saving image...")
    return encoded_img


# Function to decode the hidden message from an image
def decode_image(image_path):
    img = Image.open(image_path)

    # Ensure the image is in RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img_array = np.array(img)
    binary_message = ""

    # Decode the message from the image
    for row in range(img_array.shape[0]):
        for col in range(img_array.shape[1]):
            for color in range(3):  # Loop through RGB channels
                binary_message += str(img_array[row, col, color] & 1)

    # Debugging: Log the first 100 bits of the binary message
    print("Decoded binary message (first 100 bits):", binary_message[:100])

    # Convert binary message to text
    chars = [chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8)]
    message = ''.join(chars)

    # Debugging: Log the decoded text before finding the stop sequence
    print("Decoded text (before stop sequence):", message)

    # Find the stop sequence
    stop_idx = message.find('ÿ')  # Stop sequence marker
    if stop_idx != -1:
        final_message = message[:stop_idx]
        print("Final decoded message:", final_message)  # Log the final decoded message
        return final_message
    else:
        print("Stop sequence not found.")
        return ""  # No valid hidden message found
