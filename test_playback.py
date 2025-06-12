"""
Simple test script to verify audio playback functionality.
Run this directly with: python test_playback.py
"""

import os
import sys
import time

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import the voice output module
from interface.voice_output import speak_text_edge_tts, is_playing_audio_event

print("Starting audio test - will speak a message and wait for it to complete...")
speak_text_edge_tts("This is a test of the audio playback system. If you hear this complete sentence, the system is working properly.", wait_for_completion=False)

# Wait for audio to finish
print("Waiting for audio playback to finish...")
while is_playing_audio_event.is_set():
    print("Audio still playing...")
    time.sleep(1)

print("Audio playback completed!")
print("Test finished. The program will exit in 3 seconds.")
time.sleep(3)
print("Goodbye!")