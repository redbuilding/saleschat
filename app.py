from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file, make_response
import requests
import uuid
from dotenv import load_dotenv
import os
import json
import logging
import re
from groq import Groq
from deepgram import (DeepgramClient, SpeakOptions,)
import io
from elevenlabs.client import ElevenLabs, VoiceSettings
from flask_session import Session


load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Set the Ollama URL
ollama_api_url = os.getenv('OLLAMA_API_URL')

# Set ElevenLabs API key
client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY")
)

# Initialize the Deepgram client
deepgram_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

# Initialize the Groq client
groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize conversation history
def init_session():
    session['conversation'] = [{'sender': 'System', 'message': 'Conversation started.'}]
    session['coach_feedback'] = []
    if 'prospect_tone' not in session:
        session['prospect_tone'] = 'Neutral'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        session['prospect_business'] = request.form['prospect_business']
        session['prospect_job_title'] = request.form['prospect_job_title']
        session['prospect_responsibilities'] = request.form['prospect_responsibilities']
        session['seller_business'] = request.form['seller_business']
        session['seller_product'] = request.form['seller_product']
        session['prospect_tone'] = request.form['prospect_tone']
        session['model_choice'] = request.form['model_choice']
        session['tts_model_choice'] = request.form['tts_model_choice']

        # Initialize session data
        init_session()

        return redirect(url_for('chat'))

    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'prospect_business' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.form['message']

    # Ensure conversation history exists
    if 'conversation' not in session:
        init_session()

    # Log the current state of the conversation
    logging.info(f"Current conversation state: {session['conversation']}")

    # Copy of conversation history before adding the seller's latest message
    conversation_history_for_coach = session['conversation'][:]

    # Append user's message to conversation history
    session['conversation'].append({'sender': 'User', 'message': user_message})

    # Get sales coach feedback
    try:
        score, feedback = get_coach_feedback(user_message, conversation_history_for_coach)
        session.setdefault('coach_feedback', []).append({
            'message': user_message,
            'score': score,
            'feedback': feedback
        })
    except Exception as e:
        score, feedback = 0, "Unable to provide feedback at the moment."
        logging.error(f"Error getting coach feedback: {e}")

    # Get AI prospect's response
    try:
        prospect_response = get_prospect_response(user_message)
    except Exception as e:
        prospect_response = "I'm sorry, but I'm unable to respond at the moment."
        logging.error(f"Error getting prospect response: {e}")

    # Append prospect's response to conversation history
    session['conversation'].append({'sender': 'Prospect', 'message': prospect_response})

    # Log the updated conversation state
    logging.info(f"Updated conversation state: {session['conversation']}")

    # Explicitly save the session
    session.modified = True

    return jsonify({
        'prospect_response': prospect_response,
        'score': score,
        'feedback': feedback
    })

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

@app.route('/tts_prospect', methods=['POST'])
def tts_prospect():
    text = request.form['text']

    try:
        tts_model_choice = session.get('tts_model_choice', 'deepgram')  # Default to Deepgram

        if tts_model_choice == 'deepgram':
            # Deepgram TTS code
            SPEAK_OPTIONS = {"text": text}
            filename_p = "prospect.wav"

            options = SpeakOptions(
                model="aura-athena-en",
                encoding="linear16",
                container="wav"
            )

            # Generate speech
            deepgram_client.speak.rest.v("1").save(filename_p, SPEAK_OPTIONS, options)
            # Return the audio data as a response
            return send_file(
                filename_p,
                mimetype='audio/wav',
                as_attachment=False,
                download_name='prospect.wav'
            )
        elif tts_model_choice == 'elevenlabs':
            # ElevenLabs TTS code
            save_file_path = "prospect.mp3"

            # Generate speech and save to file
            response = client.text_to_speech.convert(
                voice_id="WLKp2jV6nrS8aMkPPDRO",  # 'Rachel' voice ID 21m00Tcm4TlvDq8ikWAM
                optimize_streaming_latency="0",
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5,
                    style=0.5,
                    use_speaker_boost=False,
                ),
            )

            # Write the audio stream to the file
            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            # Return the audio file as a response
            return send_file(
                save_file_path,
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name='prospect.mp3'
            )

        else:
            return make_response("Invalid TTS model selected", 400)

    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return make_response("Error generating audio", 500)

@app.route('/tts_coach', methods=['POST'])
def tts_coach():
    text = request.form['text']

    try:
        tts_model_choice = session.get('tts_model_choice', 'deepgram')  # Default to Deepgram

        if tts_model_choice == 'deepgram':
            # Deepgram TTS code
            SPEAK_OPTIONS = {"text": text}
            filename_c = "coach.wav"

            options = SpeakOptions(
                model="aura-zeus-en",
                encoding="linear16",
                container="wav"
            )

            # Generate speech
            deepgram_client.speak.rest.v("1").save(filename_c, SPEAK_OPTIONS, options)
            # Return the audio data as a response
            return send_file(
                filename_c,
                mimetype='audio/wav',
                as_attachment=False,
                download_name='coach.wav'
            )
        elif tts_model_choice == 'elevenlabs':
            # ElevenLabs TTS code
            save_file_path = "coach.mp3"

            # Generate speech and save to file
            response = client.text_to_speech.convert(
                voice_id="ILgPX10hGFRhOTGUqbZX",
                optimize_streaming_latency="0",
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5,
                    style=0.5,
                    use_speaker_boost=False,
                ),
            )

            # Write the audio stream to the file
            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            # Return the audio file as a response
            return send_file(
                save_file_path,
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name='coach.mp3'
            )

        else:
            return make_response("Invalid TTS model selected", 400)

    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return make_response("Error generating audio", 500)

def get_prospect_response(user_message):
    # Build system message for the prospect
    system_message = f"""
You are {session['prospect_job_title']} at {session['prospect_business']}.
Your responsibilities include {session['prospect_responsibilities']}.
You have a {session['prospect_tone']} tone.

You are having a conversation with a sales representative.
Generally, you are wary of sales representatives and prefer to present objections to their pitches.
You do not know anything about the sales representative's company or product unless they tell you during the conversation.
Respond realistically to the conversation, providing appropriate replies.
"""

    # Build conversation history
    messages = [{'role': 'system', 'content': system_message}]
    # Limit to the last 12 messages to keep the prompt manageable
    for msg in session['conversation'][-12:]:
        if msg['sender'] == 'User':
            messages.append({'role': 'user', 'content': msg['message']})
        elif msg['sender'] == 'Prospect':
            messages.append({'role': 'assistant', 'content': msg['message']})

    # Choose the model based on user's selection
    if session.get('model_choice') == 'local':
        logging.info("Using local model via Ollama API for prospect response.")
        # Convert messages into a single prompt for the local model
        prompt = ''
        for m in messages:
            if m['role'] == 'system':
                prompt += m['content'].strip() + '\n'
            elif m['role'] == 'user':
                prompt += f"Sales Rep: {m['content'].strip()}\n"
            elif m['role'] == 'assistant':
                prompt += f"Prospect: {m['content'].strip()}\n"
        prompt += "Prospect:"

        # Use local model via Ollama API
        data = {
            "model": "llama3.1",
            "prompt": prompt,
            "options": {
                "temperature": 0.7
            },
            "stream": False
        }

        response = requests.post(ollama_api_url, json=data)
        response.raise_for_status()
        ai_response = response.json()['response'].strip()
    else:
        logging.info("Using Groq model via Groq SDK for prospect response.")
        # Use Groq model via Groq SDK
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.1-70b-versatile",
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                stream=False,
            )
            ai_response = chat_completion.choices[0].message.content.strip()
        except Exception as e:
            ai_response = "I'm sorry, but I'm unable to respond at the moment."
            logging.error(f"Groq SDK Error: {e}")

    # Ensure the response is only the prospect's reply
    return ai_response.strip()

def get_coach_feedback(user_message, conversation_history):
    logging.info(f"Received conversation history: {conversation_history}")

    # Build conversation history string
    conversation_history_str = ''
    if conversation_history:
        for msg in conversation_history[-12:]:  # Limit to the last 12 messages
            conversation_history_str += f"{msg['sender']}: {msg['message']}\n"
    else:
        conversation_history_str = "No previous conversation history.\n"

    logging.info(f"Processed conversation history: {conversation_history_str}")

    # Construct the prompt for the sales coach AI agent
    prompt = f"""
You are an expert sales coach. Your job is to grade the seller's **latest message** based on persuasiveness and effectiveness on a scale of 1 to 10, where 1 is terrible and 10 is terrific.

**Focus only on the seller's latest message for grading, but use the previous conversation for context.**

Consider factors such as:
- **Clarity**: Is the message clear and understandable?
- **Relevance**: Does the pitch deliver value to the prospect and address the prospect's potential needs?
- **Brevity**: Is the message concise without unnecessary information?
- **Engagement**: Does it capture the prospect's interest?
- **Rapport-building**: Does it establish a connection with the prospect?
- **Introduction**: Did the seller properly introduce themselves and their company at the beginning of the conversation?
- **Approach**: Is the approach appropriate for the conversation so far?

Penalize pitches that:
- Are overly lengthy or provide too much information.
- Fail to introduce the seller or the company.
- Do not engage the prospect effectively.

Provide a brief justification for the score.

**Here is the conversation so far (excluding the seller's latest message):**
"{conversation_history_str}"

**Seller's latest message to grade:**
"{user_message}"

Score (1-10): (Example formatting, print the score like this: Score: 8/10)
Justification:
    """

    if session.get('model_choice') == 'local':
        logging.info("Using local model via Ollama API for coach feedback.")
        # Use local model via Ollama API
        data = {
            "model": "llama3.1",
            "prompt": prompt,
            "options": {
                "temperature": 0.5
            },
            "stream": False
        }
        logging.info(prompt)

        response = requests.post(ollama_api_url, json=data)
        response.raise_for_status()
        ai_response = response.json()['response'].strip()
        logging.info(ai_response)

    else:
        logging.info("Using Groq model via Groq SDK for coach feedback.")
        # Use Groq model via Groq SDK
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-70b-versatile",
                temperature=0.5,
                max_tokens=2000,
                top_p=1,
                stream=False,
            )
            logging.info(prompt)

            ai_response = chat_completion.choices[0].message.content.strip()
            logging.info(ai_response)
        except Exception as e:
            ai_response = "Unable to provide feedback at the moment."
            logging.error(f"Groq SDK Error: {e}")

    # Parse the score and justification
    lines = ai_response.split('\n')
    score_line = next((line for line in lines if 'Score' in line), '')
    justification_lines = lines[lines.index(score_line)+1:] if score_line in lines else lines

    # Use regular expression to find score
    score_match = re.search(r'\bScore\s*\(?\s*(\d+)\s*/\s*10\s*\)?', score_line, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))
    else:
        # Fallback to finding any standalone number between 1 and 10
        score_numbers = re.findall(r'\b[1-9]\b|10\b', score_line)
        if score_numbers:
            score = int(score_numbers[0])
        else:
            score = 0

    justification = '\n'.join(justification_lines).strip()

    return score, justification

if __name__ == '__main__':
    app.run(debug=True)
