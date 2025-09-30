from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, requests
from gtts import gTTS
from uuid import uuid4

app = Flask(__name__)
CORS(app)  # Allow frontend to call backend

# ---------- CONFIG ----------
# DO NOT put your API key here! Set as environment variable when deploying
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise SystemExit("Set OPENROUTER_API_KEY in environment before deploying")

ASSISTANT_NAME = "Quark"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Simple session memory
session_messages = [
    {"role": "system", "content": f"You are {ASSISTANT_NAME}, witty and practical AI assistant."}
]

# ---------- Helper Functions ----------
def openrouter_chat(messages, model="openai/gpt-4o-mini"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.2
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        resp = r.json()
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"API error: {e}"

def generate_tts(text):
    """Generate gTTS audio and return filename"""
    filename = f"audio_{uuid4().hex}.mp3"
    tts = gTTS(text=text, lang="en")
    tts.save(filename)
    return filename

# ---------- API Endpoints ----------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    if not user_msg:
        return jsonify({"error": "No message"}), 400

    # Add user message
    session_messages.append({"role": "user", "content": user_msg})
    reply_text = openrouter_chat(session_messages)
    session_messages.append({"role": "assistant", "content": reply_text})

    # Generate TTS audio
    audio_file = generate_tts(reply_text)
    return jsonify({"reply_text": reply_text, "audio_file": audio_file})

@app.route("/audio/<filename>", methods=["GET"])
def get_audio(filename):
    path = os.path.abspath(filename)
    if os.path.exists(path):
        return send_file(path, mimetype="audio/mpeg")
    else:
        return "File not found", 404

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
