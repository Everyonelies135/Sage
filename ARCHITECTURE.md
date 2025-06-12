# Sage Technical Architecture

This document provides a detailed technical overview of the Sage AI assistant architecture, explaining how the various components interact and function together.

## System Architecture

Sage follows a modular architecture with clearly defined components that communicate through well-established interfaces. This design allows for flexibility, extensibility, and maintainability.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Interface │◄────►     Core        │◄────►    External     │
│    Components   │     │  Intelligence   │     │    Services     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Data Storage   │◄────►    Utilities    │◄────►    Bootstrap    │
│    & Memory     │     │                 │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Component Descriptions

### 1. User Interface Layer

The UI layer handles all user interactions and consists of multiple interface options:

#### Command Line Interface (CLI)
- Implemented in `interface/cli.py`
- Provides text-based interaction
- Formats and displays Sage's responses with appropriate styling

#### Voice Interface
- Input: `interface/voice_input.py` - Handles speech recognition using optimized batch processing
- Output: `interface/voice_output.py` - Converts text to speech using Edge TTS with caching
- Features automatic intent detection to determine if speech is directed at Sage

#### Qt Graphical Interface
- Implemented in `interface/qt_app.py`
- Provides a visual interface with avatar representation
- Uses QSS styling defined in `static/sage_style.qss`

### 2. Core Intelligence

The brain of the system that processes user input and generates appropriate responses:

#### Brain (`core/brain.py`)
- Main response generation engine
- Interfaces with LLM (Language Model) APIs or local models
- Applies context, memory, and personality to create coherent responses

#### Memory System (`core/memory.py`)
- Short-term memory: Recent conversation tracking
- Long-term memory: Persistent user preferences and important information
- Implements context retrieval for improved response relevance

#### Prompt Engine (`core/prompt_engine.py`)
- Dynamically builds prompts based on context
- Manages system instructions and conversation history formatting
- Optimizes token usage for LLM interactions

#### Weekly Review (`core/weekly_sage.py`)
- Generates weekly summaries of interactions
- Identifies patterns and user preferences
- Updates the personality profile based on observations

#### Idea Garden (`core/Idea_garden.py`)
- Collects creative ideas mentioned during conversations
- Organizes and develops ideas over time
- Suggests related concepts when relevant

#### Classification (`core/classification.py`)
- Categorizes user input by intent and content type
- Helps route requests to appropriate handling logic
- Supports the intent detection system

### 3. Data Storage

Persistent storage for various types of data:

#### Memory Files
- `data/memory.json`: Short-term conversation memory
- `data/long_term_memory.json`: Persistent important information
- `data/personality_profile.json`: User preferences and personality model

#### Idea Storage
- `data/ideas/seeds.json`: Initial ideas and concepts
- Additional dynamically generated idea files

#### TTS Cache
- `data/tts_cache/`: Cached audio files for frequently used phrases
- Improves response time for common utterances

### 4. Utilities

Supporting functions and services:

#### Async Operations (`utils/async_operations.py`)
- Background processing for non-blocking operations
- Task queuing and management
- Parallel execution for improved responsiveness

#### Logging (`utils/logger.py`)
- Comprehensive event tracking
- Error and warning management
- Diagnostic information for troubleshooting

#### Tools (`utils/tools.py`)
- Interface with external APIs and services
- Client for LM Studio or OpenAI API
- Utility functions for common operations

#### Task Management
- `utils/scheduler.py`: Scheduled task execution
- `utils/task_queue.py`: Priority-based task handling

### 5. Bootstrap System

Initial setup and configuration:

#### Bootstrap (`bootstrap.py`)
- First-time setup detection
- Environment configuration
- Dependency verification
- Initial data structure creation

#### Configuration (`config.py`)
- User preferences
- System settings
- Environment variables
- Feature toggles

### 6. External Services

Third-party services and APIs:

#### Language Models
- OpenAI API or local LM Studio
- Used for response generation and classification

#### Text-to-Speech Services
- Microsoft Edge TTS (primary)
- ElevenLabs (optional high-quality voice)

#### Speech Recognition
- Local speech recognition engine
- Enhanced with background noise filtering

## Data Flow

1. User input is received through CLI, voice input, or GUI
2. Input is processed through intent classification if voice input
3. The prompt engine prepares context and formats the conversation
4. The brain generates a response using the LLM
5. Memory systems record the interaction
6. Response is displayed and/or spoken through the appropriate interface

## Key Design Patterns

1. **Observer Pattern**: For event notifications across components
2. **Factory Pattern**: For creating different types of responses
3. **Strategy Pattern**: For selecting different processing approaches
4. **Singleton Pattern**: For memory and configuration management
5. **Decorator Pattern**: For enhancing responses with additional capabilities

## Extension Points

Sage is designed with several extension points for future development:

1. **New Interface Types**: Additional UI options can be added by implementing the base interface
2. **Alternative LLM Providers**: The system can work with different LLM backends
3. **Plugin System**: Planned for Phase 3 to add custom capabilities
4. **External Integrations**: API endpoints for third-party integration

## Performance Considerations

- Voice processing is optimized with batch processing
- Text-to-speech uses caching for common phrases
- Background processing prevents UI freezing
- Memory contexts are optimized for token efficiency

## Security Notes

- API keys are stored in environment variables (keys.env - see keys.example.env)
- Personal data remains local by default
- No automatic cloud syncing of conversation history
- Consider implementing encryption for sensitive memory data in future versions
