# Sales Coach App 💼🎙️🚀

This Sales Coach app is an interactive tool designed to help sales professionals improve their skills through simulated conversations with AI-generated prospects. The app provides real-time feedback and scoring on the salesperson's performance, along with text-to-speech capabilities for an accessible experience.

## Features

- AI-powered prospect simulation
- Real-time sales coach feedback
- Performance scoring
- Text-to-speech integration
- Choice of language model providers: local Ollama (Llama3.1 8b) or Groq (Llama3.1 70b)
- Choice of text-to-speech providers: Deepgram or ElevenLabs

## Requirements

- Python 3.11+
- Flask
- Groq API key
- Deepgram API key
- ElevenLabs API key
- Ollama with Llama3.1 8b

## Installation

1. Clone the repository:
git clone https://github.com/redbuilding/saleschat.git
cd saleschat



2. Create a virtual environment and activate it:
python -m venv venv
source venv/bin/activate # On Windows, use venv\Scripts\activate



3. Install the required packages:
pip install -r requirements.txt



4. Create a `.env` file in the root directory and add:
OLLAMA_API_URL=http://localhost:11434/api/generate
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key



5. Run the application:
python app.py



6. Open a web browser and navigate to `http://127.0.0.1:5000` to use the app.

## Usage

1. Enter the prospect and seller information on the home page.
2. Choose your preferred language model and text-to-speech provider.
3. Start the chat and engage in a conversation with the AI-generated prospect.
4. Receive real-time feedback and scores from the AI sales coach.
5. Use the text-to-speech feature to hear the prospect's responses and coach feedback.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
