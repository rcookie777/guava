import subprocess
import threading
import numpy as np
import whisper
import ffmpeg
import time

def capture_audio_stream(video_url):
    """
    Use yt-dlp to extract and stream live audio from a YouTube URL,
    then pipe it to ffmpeg to capture audio data.
    """
    # yt-dlp command to extract the best audio format and pipe it to stdout
    ytdlp_command = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--quiet',  # Suppress yt-dlp output
        '--no-playlist',  # In case URL is a playlist
        '-o', '-',  # Output to stdout (pipe)
        video_url
    ]

    try:
        # Start yt-dlp process to capture audio
        ytdlp_proc = subprocess.Popen(
            ytdlp_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        print("Error: yt-dlp is not installed or not found in PATH.")
        return None, None

    # Set up ffmpeg to read from yt-dlp's stdout and convert audio format
    try:
        ffmpeg_proc = (
            ffmpeg
            .input('pipe:0')  # Read from stdin (pipe)
            .output('pipe:1', format='s16le', acodec='pcm_s16le', ac=1, ar='16000')  # Mono, 16-bit PCM, 16kHz
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"ffmpeg error: {e.stderr.decode('utf-8')}")
        ytdlp_proc.terminate()
        return None, None

    return ytdlp_proc, ffmpeg_proc

def transcriber_thread(ffmpeg_proc, model, stop_event, chunk_duration=5):
    """
    Continuously capture audio from ffmpeg and run Whisper for transcription.
    """
    buffer = np.array([], dtype=np.float32)
    sample_rate = 16000  # 16kHz sample rate
    samples_per_chunk = sample_rate * chunk_duration  # e.g., 5 seconds worth of audio

    try:
        while not stop_event.is_set():
            # Read audio data in small chunks (e.g., 4096 bytes)
            in_bytes = ffmpeg_proc.stdout.read(4096)
            if not in_bytes:
                break

            # Convert bytes to NumPy array for Whisper
            audio_chunk = np.frombuffer(in_bytes, np.int16).astype(np.float32) / 32768.0
            buffer = np.concatenate((buffer, audio_chunk))

            # If enough samples are accumulated, process a chunk
            if len(buffer) >= samples_per_chunk:
                current_chunk = buffer[:samples_per_chunk]
                buffer = buffer[samples_per_chunk:]  # Keep the rest of the buffer

                # Transcribe the audio chunk using Whisper
                result = model.transcribe(current_chunk, fp16=False)
                if result and result["text"].strip():
                    print(f"Transcript: {result['text'].strip()}")  # Print transcription immediately

    except Exception as e:
        print(f"Transcriber thread error: {e}")
    finally:
        stop_event.set()

def main():
    video_url = "https://www.youtube.com/watch?v=8NMCnOONqvw"  # Replace with your video URL

    # Load Whisper model (use 'tiny' for faster processing)
    model = whisper.load_model("tiny")

    # Capture audio stream from YouTube
    ytdlp_proc, ffmpeg_proc = capture_audio_stream(video_url)
    if not ytdlp_proc or not ffmpeg_proc:
        print("Error starting yt-dlp or ffmpeg process.")
        return

    # Event to signal the transcriber thread to stop
    stop_event = threading.Event()

    # Start the transcriber thread to process audio and extract text
    transcriber = threading.Thread(target=transcriber_thread, args=(ffmpeg_proc, model, stop_event), daemon=True)
    transcriber.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
        stop_event.set()

    finally:
        # Clean up: terminate yt-dlp and ffmpeg processes
        ytdlp_proc.terminate()
        ffmpeg_proc.terminate()

        # Wait for the transcriber thread to finish
        transcriber.join(timeout=5)

        print("Shutdown complete.")

if __name__ == "__main__":
    main()
