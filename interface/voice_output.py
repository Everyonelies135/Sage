# interface/voice_output.py
import os
import tempfile
import asyncio
import edge_tts
from playsound import playsound  # type: ignore
import threading

# Event flag indicating audio playback status
is_playing_audio_event = threading.Event()

def speak_text_edge_tts(text: str, voice: str = "en-US-AriaNeural", wait_for_completion: bool = True) -> None:
    """Generate and play speech asynchronously using Edge TTS, with optional blocking."""
    def _play_task():
        is_playing_audio_event.set()
        # Generate speech to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            filename = f.name
        asyncio.run(edge_tts.Communicate(text, voice).save(filename))
        playsound(filename)
        try:
            os.remove(filename)
        except OSError:
            pass
        is_playing_audio_event.clear()
    # Start playback thread
    thread = threading.Thread(target=_play_task, daemon=True)
    thread.start()
    if wait_for_completion:
        thread.join()

# Override speak_text to use edge-tts with blocking playback

def speak_text(text: str, voice: str = "en-US-AriaNeural") -> None:
    """Generate and play speech synchronously using Edge TTS."""
    speak_text_edge_tts(text, voice, wait_for_completion=True)
