from flask import Flask, render_template, request, jsonify
import base64
import requests
import json
from typing import Dict, Any
import os
import docx  # Add this import for reading .docx files

# Configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"  # Changed back to /api/generate
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB limit
MODEL_NAME = "llama3.2-vision:latest"  # Updated to match your pulled model name

app = Flask(__name__)

# Initialize conversation history as a list
history: list = []

# Add function to read docx content
def read_docx_file(file_path: str) -> str:
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Read the predefined knowledge
try:
    PREDEFINED_KNOWLEDGE = read_docx_file('data.docx')
except Exception as e:
    print(f"Warning: Could not read data.docx: {str(e)}")
    PREDEFINED_KNOWLEDGE = ""

@app.route("/")
def index():
    return render_template('chat.html')

@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form.get("msg", "").strip()
        image = request.files.get("image")
        
        prompt_data = {
            "model": MODEL_NAME,
            "prompt": msg,
            "stream": False
        }
        
        if image:
            # Check file size
            image.seek(0, 2)
            size = image.tell()
            if size > MAX_IMAGE_SIZE:
                return jsonify("Image size too large. Please upload an image smaller than 10MB")
            
            image.seek(0)
            
            if not image.content_type.startswith('image/'):
                return jsonify("Invalid file type. Please upload an image file")
            
            # Convert image to base64
            image_data = base64.b64encode(image.read()).decode('utf-8')
            prompt_data["images"] = [image_data]

        return jsonify(get_chat_response(prompt_data))

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify("An error occurred while processing your request")

def get_chat_response(prompt_data: Dict[str, Any]) -> str:
    try:
        # Modify the prompt to include predefined knowledge
        system_prompt = f"Use this knowledge as context for your responses:\n{PREDEFINED_KNOWLEDGE}\n\nUser question: "
        prompt_data['prompt'] = system_prompt + prompt_data['prompt']
        
        # Check if Ollama is running
        response = requests.post(
            OLLAMA_ENDPOINT, 
            json=prompt_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Ollama error: {response.text}")
            return "Error: Unable to get response from Ollama"

        response_data = response.json()
        # Updated to match /api/generate response structure
        ai_response = response_data.get('response', 'Sorry, I could not process that.')
        
        # Update history
        history.append({
            "user": prompt_data['prompt'],  # Changed from messages structure
            "ai": ai_response
        })
        
        return ai_response

    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Please make sure it's running."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "An unexpected error occurred. Please try again."

if __name__ == '__main__':
    # Check if Ollama is installed
    if os.system("which ollama >/dev/null 2>&1") != 0:
        print("Warning: Ollama is not installed. Please install it first.")
        print("You can install it using: curl https://ollama.ai/install.sh | sh")
    
    # Start the Flask app
    app.run(debug=True, port=5000)
