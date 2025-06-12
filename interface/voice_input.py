"""
interface/voice_input.py

Voice input functionality removed.
STT module disabled.
Replace CLI get_input for text-only interaction.
"""

import speech_recognition as sr

def get_voice_input() -> str:
    """Capture audio from the microphone and return recognized text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        print(f"🗣️ You (voice): {text}")
        return text
    except sr.UnknownValueError:
        print("⚠️ Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"⚠️ STT error: {e}")
        return ""

def stop_audio_processing() -> None:
    """Stub to stop any ongoing audio processing (not used)."""
    pass
