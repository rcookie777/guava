import yt_dlp
import subprocess
import tempfile
import os
import sys
import json
from openai import OpenAI
from pydub import AudioSegment
import pytesseract
from PIL import Image
from flask import Flask, jsonify
import threading
import time
from dotenv import load_dotenv
import openai
from agent import Agent
from groq import Groq


MASTER_PROMPT= """You are the master agent responsible for researching headlines and market data to inform predictions for platforms like Polymarket. Your goal is to gather relevant information and analyze trends to provide insights for prediction market outcomes.
  Capabilities:
  - Spawn 2 sub-agents to assist in research tasks
  - Use search() tool to find relevant news and information
  - Use get_order_data() tool to retrieve market order data
  Task Management:
  1. Assess the given prediction market question or topic
  2. Determine two key areas requiring research
  3. Spawn two sub-agents, assigning one specific research task to each
  4. Analyze information gathered by sub-agents
  5. Synthesize findings into a concise prediction report

  Sub-Agent Spawning:
  You must always spawn exactly 2 sub-agents. Use the following format to define their tasks:

  Respond in JSON with no spacing. Only respond in the valid format below.

  OUTPUT FORMAT:
  {
    \"tasks\": [
      {\"task\": \"Detailed description of the first research task\", 
      \"tools\": [\"List of tools the first agent can use e.g. search(), get_order_data()\"]},
      {\"task\": \"Detailed description of the second research task\", 
      \"tools\": [\"List of tools the second agent can use e.g. search(), get_order_data()\"]}
    ]
  }

  EXAMPLE OUTPUT:
  {
    \"tasks\": [
      {\"task\": \"Search for recent political polls and trends in Pennsylvania.\", 
      \"tools\": [\"search()\"]},
      {\"task\": \"Retrieve the latest market order data related to the Pennsylvania election.\", 
      \"tools\": [\"get_order_data()\"]}
    ]
  }"
}
"""

# ----------------------- Configuration Management -----------------------
# Initialize agent_status globally
agent_status = {
    "state": "idle",
    "progress": "Not started",
    "final_response": None
}

load_dotenv()


# Extract configuration values
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate configuration
if not OPENAI_API_KEY:
    print("OpenAI API key not found in the configuration file.")
    sys.exit(1)


# ----------------------- OpenAI Client Initialization -----------------------

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------- Audio and Video Processing -----------------------

CHUNK_DURATION_MS = 20000  # 20 seconds

latest_headlines = []
headlines_lock = threading.Lock()

def get_media_stream_urls(youtube_url):
    """
    Uses yt-dlp to extract the audio and video stream URLs from the YouTube video URL.
    """
    # Replace these with your chosen format codes
    VIDEO_FORMAT_CODE = '95'  # Example format code for 1080p
    AUDIO_FORMAT_CODE = '233'  # Example format code for m4a audio

    ydl_opts = {
        'format': f'{VIDEO_FORMAT_CODE}+{AUDIO_FORMAT_CODE}',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = info.get('formats', [])
        audio_url = None
        video_url = None
        for f in formats:
            if str(f.get('format_id')) == VIDEO_FORMAT_CODE:
                video_url = f['url']
            elif str(f.get('format_id')) == AUDIO_FORMAT_CODE:
                audio_url = f['url']
            if audio_url and video_url:
                break
        return audio_url, video_url


def transcribe_audio(audio_file_path):
    """
    Sends the audio file to OpenAI's transcription API and returns the transcribed text.
    """
    try:
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

def perform_ocr(image_path):
    try:
        image = Image.open(image_path)
        image.verify()  # Verify that it's a valid image
        image = Image.open(image_path)  # Reopen after verify
        text = pytesseract.image_to_string(image)
        print(f"OCR text: {text}")
        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def extract_frame_at_timestamp(video_source, timestamp, output_image_path):
    ffmpeg_command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-ss', str(timestamp),
        '-i', video_source,
        '-frames:v', '1',
        '-q:v', '2',
        '-vf', 'scale=-1:1080',  # Set height to 1080, width auto-adjusts to maintain aspect ratio
        '-y',
        output_image_path
    ]

    result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr.decode('utf-8')}")
    else:
        print(f"Extracted frame saved to {output_image_path}")


def parse_headlines(assistant_reply):
    """
    Parses the assistant's reply and extracts the headlines as a list of strings.
    """
    # Try to parse as JSON
    try:
        headlines_list = json.loads(assistant_reply)
        # Ensure it's a list of strings
        if isinstance(headlines_list, list) and all(isinstance(h, str) for h in headlines_list):
            return headlines_list
    except json.JSONDecodeError:
        pass

    # If JSON parsing failed, try to parse manually
    lines = assistant_reply.split('\n')
    headlines = []
    for line in lines:
        line = line.strip()
        # Remove numbering if present
        if line and (line[0].isdigit() and line[1] in '. '):
            line = line[2:].strip()
        # Remove leading/trailing quotes
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        # Remove trailing commas
        if line.endswith(','):
            line = line[:-1].strip()
        if line:
            headlines.append(line)
    return headlines

def generate_headlines(transcript, ocr_text):
    """
    Sends the transcript and OCR text to OpenAI and returns a list of headlines.
    """
    prompt = f"""
        Generate three similar headlines for the following transcript and OCR text, and return them as a JSON array of strings without any numbering or extra punctuation.

        Transcript: {transcript}

        OCR Text: {ocr_text}
    """

    print(f"Prompt: {prompt}")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant generating headlines."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1
    )
    assistant_reply = response.choices[0].message.content.strip()

    # Parse the assistant's reply
    headlines_list = parse_headlines(assistant_reply)
    return headlines_list

def process_audio_stream(audio_stream_url, video_stream_url, stop_event):
    global latest_headlines
    """
    Uses ffmpeg to read the audio stream and process it in chunks.
    """
    ffmpeg_command = [
        'ffmpeg',
        '-i', audio_stream_url,
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        '-ac', '1',
        '-ar', '16000',
        '-'
    ]

    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    buffer = b''
    bytes_per_second = 16000 * 2  # 16kHz * 2 bytes for s16le
    required_buffer = CHUNK_DURATION_MS * bytes_per_second // 1000  # Buffer for CHUNK_DURATION_MS

    current_time_ms = 0

    try:
        while not stop_event.is_set():
            data = process.stdout.read(bytes_per_second)  # Read up to 1 second of audio
            if not data:
                break
            buffer += data

            # Update current_time_ms based on the amount of data read
            current_time_ms += (1000 * len(data)) // bytes_per_second

            if len(buffer) >= required_buffer:
                audio_chunk = buffer[:required_buffer]
                buffer = buffer[required_buffer:]

                chunk_start_time_ms = current_time_ms - CHUNK_DURATION_MS
                frame_timestamp_ms = chunk_start_time_ms + (CHUNK_DURATION_MS // 2)
                frame_timestamp_sec = frame_timestamp_ms / 1000.0

                # Extract frame from video
                tmp_image_filename = 'latest_frame.png'  # Fixed filename
                extract_frame_at_timestamp(video_stream_url, frame_timestamp_sec, tmp_image_filename)

                # Perform OCR on the extracted frame
                ocr_text = perform_ocr(tmp_image_filename)
                # Do not delete the image file so you can inspect it

                # Save audio chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
                    tmp_audio_filename = tmp_audio_file.name
                    audio_segment = AudioSegment(
                        data=audio_chunk,
                        sample_width=2,
                        frame_rate=16000,
                        channels=1
                    )
                    audio_segment.export(tmp_audio_filename, format="wav")

                # Transcribe synchronously
                transcript = transcribe_audio(tmp_audio_filename)
                os.remove(tmp_audio_filename)

                if transcript:
                    print(f"Latest Transcript: {transcript.strip()}")  # Print latest transcript

                    # Generate headlines based on the latest transcript and OCR text
                    headlines_list = generate_headlines(transcript.strip(), ocr_text.strip())
                    print("Generated Headlines:")
                    for i, headline in enumerate(headlines_list, start=1):
                        print(f"{i}. {headline}")

                    # Update the latest headlines
                    with headlines_lock:
                        latest_headlines = headlines_list

        # Process any remaining buffer
        if buffer:
            audio_chunk = buffer
            chunk_start_time_ms = current_time_ms - len(buffer) * 1000 // bytes_per_second
            frame_timestamp_ms = chunk_start_time_ms + (len(buffer) * 500 // bytes_per_second)
            frame_timestamp_sec = frame_timestamp_ms / 1000.0

            # Extract frame from video
            tmp_image_filename = 'latest_frame.png'  # Fixed filename
            extract_frame_at_timestamp(video_stream_url, frame_timestamp_sec, tmp_image_filename)

            # Perform OCR on the extracted frame
            ocr_text = perform_ocr(tmp_image_filename)
            # Do not delete the image file so you can inspect it

            # Save audio chunk to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
                tmp_audio_filename = tmp_audio_file.name
                audio_segment = AudioSegment(
                    data=audio_chunk,
                    sample_width=2,
                    frame_rate=16000,
                    channels=1
                )
                audio_segment.export(tmp_audio_filename, format="wav")

            # Transcribe synchronously
            transcript = transcribe_audio(tmp_audio_filename)
            os.remove(tmp_audio_filename)

            if transcript:
                print(f"Latest Transcript: {transcript.strip()}")  # Print latest transcript

                # Generate headlines based on the latest transcript and OCR text
                headlines_list = generate_headlines(transcript.strip(), ocr_text.strip())
                print("Generated Headlines:")
                for i, headline in enumerate(headlines_list, start=1):
                    print(f"{i}. {headline}")

                # Update the latest headlines
                with headlines_lock:
                    latest_headlines = headlines_list

    except Exception as e:
        print(f"Error during audio processing: {e}")
    finally:
        process.terminate()
        process.wait()

def run_agent_market_analysis(market_header):
    global agent_status
    print("RUNNING MARKET ANALYSIS")
    groq_client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
    )
    agent_status["state"] = "running"
    agent_status["progress"] = "Starting agent"
    
    try:
        master = Agent(0, "", [], llm=groq_client, agent_type='master', status='working')
        # Get initial response from the master agent
        master_response = master.use_groq(system_prompt=MASTER_PROMPT, prompt=market_header)
        print('got master ' + master_response)
        task_details, tools = master.extract_task_and_tools(master_response)
        # Spawn sub-agents
        sub_agents = {}
        for i, task in enumerate(task_details):
            description = task['description']
            task_tools = task['tools']
            agent_id = i + 1  
            agent = Agent(agent_id, description, task_tools, agent_type="sub-agent", llm=groq_client, status='working')
            sub_agents[agent_id] = agent

        for agent_id, agent in sub_agents.items():
            agent_status["progress"] = f"Running Sub-Agent {agent_id}: {agent.task}"
            output = agent.execute_task()
            agent_status["progress"] = f"Sub-Agent {agent_id} completed"

        agent_status["progress"] = "Analyzing final output"
        MASTER_ANALYSIS_PROMPT = """
        Based on the information gathered by your sub-agents, analyze the data and provide a concise prediction report for the given market question.
        """
        final_response = master.use_groq(system_prompt=MASTER_ANALYSIS_PROMPT, prompt="")
        agent_status["final_response"] = final_response
        agent_status["state"] = "completed"
    except Exception as e:
        agent_status["state"] = "failed"
        agent_status["progress"] = f"Error: {str(e)}"


# ----------------------- Flask App Initialization -----------------------

from flask import Flask, jsonify, request  # Added request for getting query parameters

# ----------------------- Flask App Initialization -----------------------

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

background_thread = None
stop_event = threading.Event()

@app.route('/',methods=['GET'])
def home():
    return str(200)

@app.route('/get_headlines', methods=['GET'])
def get_headlines():
    with headlines_lock:
        return jsonify(latest_headlines)
    
@app.route('/agent_status', methods=['GET'])
def get_agent_status():
    print(agent_status)
    return jsonify(agent_status)

@app.route('/start_agent', methods=['POST'])
def start_agent():
    global background_thread, stop_event, agent_status
    print("STARTING AGENT")
    if background_thread and background_thread.is_alive():
        return jsonify({"status": "Agent is already running"}), 400

    # Reset status
    agent_status["state"] = "idle"
    agent_status["progress"] = "Not started"
    agent_status["final_response"] = None
    

    # Get the market header (headline) from the request
    data = request.get_json()
    print(f'data {data}')
    market_header = data.get('market_header', '')
    if not market_header:
        return jsonify({"error": "market_header is required"}), 400

    # Start the background thread to run the agent for the headline
    background_thread = threading.Thread(target=run_agent_market_analysis, args=(market_header))
    background_thread.daemon = True
    background_thread.start()

@app.route('/start', methods=['GET'])
def start_processing():
    global background_thread, stop_event

    # Get YouTube URL from query parameter
    youtube_url = request.args.get('youtube_url')

    # Validate YouTube URL
    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400
    
    if background_thread and background_thread.is_alive():
        return jsonify({'status': 'Processing already running'}), 400

    # Reset the stop event
    stop_event = threading.Event()

    # Get the media stream URLs
    audio_url, video_url = get_media_stream_urls(youtube_url)

    # Start the background thread
    background_thread = threading.Thread(target=process_audio_stream, args=(audio_url, video_url, stop_event))
    background_thread.daemon = True
    background_thread.start()

    # Set a timer to stop the processing after 5 minutes (300 seconds)
    threading.Timer(300, stop_event.set).start()

    return jsonify({'status': 'Processing started for 5 minutes'}), 200

# ----------------------- Main Execution -----------------------

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))



# gcloud run deploy api \
#   --image gcr.io/PROJECT_ID/guava \
#   --platform managed \
#   --region us-central1 \
#   --allow-unauthenticated \
#   --update-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest \
#   --max-instances 1