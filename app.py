from flask import Flask, render_template, request, jsonify
from langchain_openai import ChatOpenAI
import base64
API_KEY = "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"  
# Initialize the chat model
chat_llm = ChatOpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1", model="meta-llama/llama-3.2-1b-instruct:free", temperature=0.0)
app = Flask(__name__)
@app.route("/")
def index():
    return render_template('chat.html')

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg", "")
    image = request.files.get("image")
    if image:
        # Convert image to base64 string
        image_data = base64.b64encode(image.read()).decode('utf-8')
        # For now, just append a placeholder text for the image
        msg += " [Image attached]"
    return jsonify(get_Chat_response(msg))
def get_Chat_response(text):
    global history
    history = []
    full_prompt = "\n".join(history + [text])
    response = chat_llm.invoke(full_prompt).content
    history.append(f"User: {text}")
    history.append(f"AI: {response}")
    return response

if __name__ == '__main__':
    app.run()