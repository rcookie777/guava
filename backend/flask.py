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

# ----------------------- Configuration Management -----------------------

load_dotenv()

def load_config(config_path='config.json'):
    """
    Loads the configuration from a JSON file.
    """
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from the configuration file: {e}")
        sys.exit(1)

# Load configuration
config = load_config()

# Extract configuration values
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_URL = config.get("YOUTUBE_URL")

# Validate configuration
if not OPENAI_API_KEY:
    print("OpenAI API key not found in the configuration file.")
    sys.exit(1)

if not YOUTUBE_URL:
    print("YouTube URL not found in the configuration file.")
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

# ----------------------- Flask App Initialization -----------------------

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

background_thread = None
stop_event = threading.Event()

@app.route('/get_headlines', methods=['GET'])
def get_headlines():
    with headlines_lock:
        return jsonify(latest_headlines)

@app.route('/start', methods=['GET'])
def start_processing():
    global background_thread, stop_event

    # Check if the processing is already running
    if background_thread and background_thread.is_alive():
        return jsonify({'status': 'Processing already running'}), 400

    # Reset the stop event
    stop_event = threading.Event()

    # Get the media stream URLs
    audio_url, video_url = get_media_stream_urls(YOUTUBE_URL)

    # Start the background thread
    background_thread = threading.Thread(target=process_audio_stream, args=(audio_url, video_url, stop_event))
    background_thread.daemon = True
    background_thread.start()

    # Set a timer to stop the processing after 5 minutes (300 seconds)
    threading.Timer(300, stop_event.set).start()

    return jsonify({'status': 'Processing started for 5 minutes'}), 200

# ----------------------- Main Execution -----------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
