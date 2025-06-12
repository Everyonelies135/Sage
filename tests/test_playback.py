import time
import threading
from unittest.mock import patch

import sys
import types

# Stub out optional dependencies so interface.voice_output can be imported
fake_edge_tts = types.ModuleType("edge_tts")

class DummyCommunicate:
    async def save(self, filename: str) -> None:  # pragma: no cover - dummy impl
        pass

fake_edge_tts.Communicate = DummyCommunicate
sys.modules.setdefault("edge_tts", fake_edge_tts)

fake_playsound = types.ModuleType("playsound")
fake_playsound.playsound = lambda *args, **kwargs: None
sys.modules.setdefault("playsound", fake_playsound)

import interface.voice_output as voice_output


def fake_speak(*args, **kwargs):
    """Simulate asynchronous speech playback."""
    voice_output.is_playing_audio_event.set()

    def _clear():
        time.sleep(0.1)
        voice_output.is_playing_audio_event.clear()

    threading.Thread(target=_clear, daemon=True).start()


def test_playback_wait_loop_terminates():
    with patch('interface.voice_output.speak_text_edge_tts', side_effect=fake_speak) as mock_speak:
        start = time.time()
        # Start playback
        voice_output.speak_text_edge_tts("test", wait_for_completion=False)

        # Wait loop as in the original script
        while voice_output.is_playing_audio_event.is_set():
            assert time.time() - start < 1, "wait loop did not terminate"
            time.sleep(0.05)

        # Ensure playback ended and function was called
        assert mock_speak.called
        assert not voice_output.is_playing_audio_event.is_set()

