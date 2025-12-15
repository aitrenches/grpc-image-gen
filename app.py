import os
import openai
from flask import Flask, request, jsonify
from functools import wraps
from dotenv import load_dotenv
from image_utils import save_base64_image

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

openai.api_key = OPENAI_API_KEY

# Authentication Decorator
def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        if api_key != os.getenv("API_SECRET_KEY"):
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route("/generate", methods=["POST"])
@authenticate
def generate_image():
    data = request.json
    prompt = data.get("prompt")
    size = data.get("size", "1024x1024")
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json"
        )
        base64_image = response.data[0].b64_json
        
        # Save the image to the images folder
        filename = None
        try:
            filename = save_base64_image(base64_image)
        except Exception as save_error:
            # If saving fails, log the error but still return the base64 data
            print(f"Warning: Failed to save image: {str(save_error)}")
        
        return jsonify({
            "image": base64_image,
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

