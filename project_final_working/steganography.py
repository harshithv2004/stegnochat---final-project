# steganography.py
from PIL import Image
import numpy as np
import base64

# STOP marker (16 bits) to indicate end-of-payload
STOP_MARKER = "1111111111111110"

def _to_bitstring(s: str) -> str:
    """Convert ascii string to bit string (8 bits per char)."""
    return ''.join(format(ord(ch), '08b') for ch in s)

def _bits_to_bytes(bitstr: str) -> bytes:
    """Convert bit string (length multiple of 8) to bytes."""
    ba = bytearray()
    for i in range(0, len(bitstr), 8):
        byte = bitstr[i:i+8]
        if len(byte) < 8:
            break
        ba.append(int(byte, 2))
    return bytes(ba)

def encode_image(image_path, message):
    """
    Encode 'message' (str) into image at image_path and return a PIL Image object.
    The message is first encoded as UTF-8, then base64-encoded (ASCII), then embedded.
    """
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img_array = np.array(img).copy()

    # Prepare payload: UTF-8 -> base64 ASCII
    utf8_bytes = message.encode('utf-8')
    b64_str = base64.b64encode(utf8_bytes).decode('ascii')  # safe ASCII
    payload = b64_str  # ASCII payload to embed
    binary_payload = _to_bitstring(payload) + STOP_MARKER

    data_index = 0
    max_bits = img_array.size  # total number of channel values

    if len(binary_payload) > max_bits:
        raise ValueError("Message is too large to encode in this image. Use a larger image or shorter message.")

    for row in range(img_array.shape[0]):
        for col in range(img_array.shape[1]):
            for channel in range(3):  # R, G, B
                if data_index < len(binary_payload):
                    original = int(img_array[row, col, channel])
                    bit = int(binary_payload[data_index])
                    img_array[row, col, channel] = np.uint8((original & ~1) | bit)
                    data_index += 1
                else:
                    break
            if data_index >= len(binary_payload):
                break
        if data_index >= len(binary_payload):
            break

    return Image.fromarray(img_array)


def decode_image(image_path):
    """
    Decode and return the hidden message (original UTF-8 string) if present.
    Returns user-friendly messages when nothing is found or when decoding fails.
    """
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img_array = np.array(img)
    binary_data = []

    # Collect LSBs
    for row in img_array:
        for pixel in row:
            for color in pixel:
                binary_data.append(str(int(color) & 1))

    binary_data = ''.join(binary_data)

    # Find stop marker
    stop_index = binary_data.find(STOP_MARKER)
    if stop_index == -1:
        return "[Hidden message not found]"

    payload_bits = binary_data[:stop_index]
    if not payload_bits:
        return "[No hidden message]"

    # Convert bits -> ASCII bytes (these should be base64 text)
    try:
        payload_bytes = _bits_to_bytes(payload_bits)
        # Interpret as ASCII (base64 string)
        b64_str = payload_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        if not b64_str:
            return "[No hidden message]"

        # Try base64-decoding to get original UTF-8 bytes
        try:
            original_bytes = base64.b64decode(b64_str, validate=True)
        except Exception:
            # If validate failed, try a lenient decode (ignore errors)
            try:
                original_bytes = base64.b64decode(b64_str + "==")
            except Exception:
                return "[Error decoding hidden message]"

        # Finally decode UTF-8
        try:
            decoded = original_bytes.decode('utf-8', errors='ignore')
            if decoded.strip() == "":
                return "[No hidden message]"
            return decoded
        except Exception:
            return "[Error decoding hidden message]"

    except Exception:
        return "[Error decoding hidden message]"
