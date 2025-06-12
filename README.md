# Sage - Your Personal AI Companion

Sage is an advanced AI assistant designed to understand, learn, and adapt to your needs through natural conversation. It features memory management and intelligent response generation.

## 🌟 Features

### Core Intelligence
- **Brain**: Advanced response generation system powered by LLMs
- **Memory Management**: Short-term and long-term memory storage
- **Prompt Engineering**: Dynamic context-aware prompt creation
- **Intent Classification**: Determines if text is directed at Sage
- **Weekly Learning**: Summarizes interactions and learns from patterns

### Voice I/O (Optional)
- **Speech-to-Text (STT)**: Capture voice input using SpeechRecognition and Google Web Speech API
- **Text-to-Speech (TTS)**: Natural, high-quality speech via Microsoft Edge TTS (edge-tts)
- **Configurable**: Voice mode is toggled in `config.py`

### Interface Options
- **Command Line**: Text-based interaction through terminal
- **Qt GUI**: Graphical user interface with avatar and styling

### Extended Capabilities
- **Idea Garden**: Collects and nurtures creative ideas
- **Personality Profile**: Adapts to user preferences over time
- **Task Management**: Schedules and manages tasks
- **Asynchronous Operations**: Background processing for responsive experience
- **Error Resilience**: Graceful handling of network or service disruptions

### Technical Features
- **Bootstrapping**: Automatic first-time setup and configuration
- **Logging**: Comprehensive event tracking and diagnostics
- **Async Tools**: Background execution of time-intensive operations
- **TTS Caching**: Efficient text-to-speech with local caching

## 📋 Project Structure

```
sage/
├── bootstrap.py          # Initial setup and configuration
├── config.py             # User preferences and system settings
├── keys.example.env              # Example API key file (copy to keys.env)
├── launch.py             # Alternative entry point with additional options
├── main.py               # Primary application entry point
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
│
├── core/                 # Core intelligence components
│   ├── brain.py          # Main response generation logic
│   ├── classification.py # Content and intent classification
│   ├── Idea_garden.py    # Idea collection and development
│   ├── memory.py         # Conversation memory management
│   ├── prompt_engine.py  # Dynamic prompt creation
│   └── weekly_sage.py    # Weekly summaries and learning
│
├── interface/            # User interaction components
│   ├── cli.py            # Command-line interface
│   ├── qt_app.py         # PyQt graphical interface
│   └── voice_output.py   # Text-to-speech generation
│
├── data/                 # Data storage
│   ├── memory.json       # Short-term memory storage
│   ├── long_term_memory.json # Long-term memory storage
│   ├── personality_profile.json # User preference data
│   ├── weekly_review_log.txt    # Weekly learning logs
│   ├── ideas/            # Storage for idea garden
│   │   └── seeds.json    # Initial ideas and concepts
│   └── tts_cache/        # Cached speech audio files
│
├── utils/                # Utility functions and helpers
│   ├── async_operations.py # Background processing utilities
│   ├── logger.py         # Logging functionality
│   ├── scheduler.py      # Task scheduling
│   ├── task_queue.py     # Task management
│   └── tools.py          # External API utilities
│
├── static/               # Static assets
│   ├── sage_avatar.png   # Avatar image for GUI
│   ├── sage_style.qss    # Qt stylesheets
│   ├── styles.css        # Web interface styles
│   └── techback.png      # Background image
│
├── logs/                 # Application logs
│   └── sage.log          # Main log file
│
└── tests/                # Test suite
    ├── audio_playback_test.py  # Audio output tests
    ├── elevenlabs_test.py      # ElevenLabs TTS tests
    ├── pydub_playback_test.py  # Audio processing tests
    ├── test_core.py            # Core functionality tests
    ├── tts_test.py             # Text-to-speech tests
    └── voice_test.py           # Voice recognition tests
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PyQt5 (for GUI mode)
- Internet connection (for some LLM operations)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/sage.git
   cd sage
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   *Note for Windows users:* PyAudio is required for speech input. If installation fails:
   1. Download the appropriate PyAudio wheel for your Python version and architecture from:
      https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
   2. Install it manually, e.g.:
      ```
      pip install <path_to_downloaded_wheel>.whl
      ```

3. Copy keys.example.env to keys.env and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ```

4. Run Sage:
   ```
   python main.py
   ```

### Launch Options

- Text-only mode: `python main.py`
- GUI mode: `python main.py --qt`

## 🛠️ Development Roadmap

### Phase 1: Core Functionality
- [x] Basic conversation capabilities
- [x] Memory system implementation
- [x] Command-line interface

### Phase 2: Advanced Features
- [x] Personality profiling
- [x] Idea garden
- [x] Qt GUI implementation
- [x] Weekly learning review

### Phase 3: Extensions (Upcoming)
- [ ] Mobile companion app
- [ ] Web interface
- [ ] API for third-party integrations
- [ ] Plugin system for extended capabilities
- [ ] Advanced analytics dashboard

## 📚 Documentation

Additional documentation can be found in the `/docs` directory (coming soon).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for AI capabilities
- Microsoft Edge TTS for voice generation
- The PyQt team for GUI components.
