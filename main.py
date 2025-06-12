"""
main.py (streamlined & modernized)

This is the entry point for the Sage application. It initializes the system, handles user input (voice or text), and processes responses using Sage's core logic.
"""

# Import standard libraries
import sys  # Provides access to system-specific parameters and functions
import argparse  # For parsing command-line arguments
from typing import Optional  # For type hinting optional values
import time  # For time-related operations
import asyncio  # Modern async event loop

# Import custom modules for CLI, core logic, memory, prompt engine, config, logging, and tools
from interface.cli import CLI  # Command-line interface class
from core.brain import generate_response  # Core function to generate Sage's response
from core.memory import Memory  # Memory class for storing interactions
from core.prompt_engine import PromptEngine  # Prompt engine for context and prompt management
from config import USER_NAME, USE_VOICE  # User configuration
from utils.logger import log_event, get_logger  # Logging utility
from bootstrap import bootstrap, needs_bootstrap  # Functions for initial setup
from utils.tools import client  # Client for LM Studio or LLM API
from interface.voice_input import get_voice_input  # Voice input function
from interface.voice_output import speak_text  # Voice output function


async def is_input_for_sage(user_input: str) -> bool:
    """
    Determines if the input is directed at Sage by querying LM Studio.
    Runs in background for better responsiveness.
    
    Args:
        user_input (str): The user's input string.
    Returns:
        bool: True if input is for Sage, False otherwise.
    """
    # Compose a prompt for the intent classifier
    prompt = (
        "You are an intent classifier. Decide if the following sentence is directed at a personal AI assistant named Sage. "
        "Respond only with 'yes' or 'no'.\n\n"
        f'Input: "{user_input}"\n\nAnswer:'
    )
    # Prepare messages for the LLM
    messages = [
        {
            "role": "system",
            "content": "You classify user intent to see if the message is for Sage.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        # Check if simple keyword detection can determine intent first
        # (fallback mechanism that doesn't require LM Studio)
        simple_keywords = ["sage", "hey sage", "hi sage", "okay sage", "hey assistant"]
        if any(keyword in user_input.lower() for keyword in simple_keywords):
            log_event("Intent detected via keyword matching.")
            return True
            
        # Try to query the LLM for intent classification
        try:
            # Add timeout to prevent hanging
            import requests.exceptions
            response = client.chat.completions.create(
                model="local-model", messages=messages, temperature=0, max_tokens=10, 
                timeout=3  # Add 3 second timeout
            )
            answer = response.choices[0].message.content.strip().lower()  # Extract and normalize answer
            return "yes" in answer  # Return True if answer contains 'yes'
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            log_event(f"⚠️ LM Studio connection error: {e}", level="warning")
            # Fall back to simple heuristics for intent detection
            log_event("Falling back to basic intent detection")
            # Very basic intent detection - if input contains question words or ends with "?"
            return any(word in user_input.lower() for word in ["?", "what", "how", "why", "where", "when", "who"]) or "sage" in user_input.lower()
    except Exception as e:
        log_event(f"❌ Intent detection failed: {e}", level="error")
        # Don't crash the program - return default value
        return True  # Default to assuming input is for Sage when detection fails completely


async def main() -> None:
    """
    The main function that initializes and runs the Sage application.
    """
    logger = get_logger()
    # Check if initial setup is needed
    if needs_bootstrap():
        try:
            bootstrap()  # Run bootstrap if required
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            print("❌ Failed to initialize Sage. Please check logs.")
            return
    # Set up argument parser for CLI options
    parser = argparse.ArgumentParser(description="Sage – Your Personal AI Companion")
    parser.add_argument(
        "--qt", action="store_true", help="Launch the PyQt GUI"
    )
    args = parser.parse_args()  # Parse command-line arguments
    
    if args.qt:
        # Launch the PyQt GUI if --qt flag is set
        try:
            import interface.qt_app
        except Exception as e:
            logger.error(f"Failed to launch PyQt GUI: {e}")
            print("❌ Failed to launch GUI. See logs for details.")
        return
        
    # Voice mode controlled by USE_VOICE flag
    
    try:
        memory = Memory()  # Initialize memory for conversation history
    except Exception as e:
        logger.error(f"Failed to initialize memory: {e}")
        print("❌ Failed to initialize memory. See logs for details.")
        return
        
    cli = CLI(memory)  # Initialize CLI interface
    
    try:
        prompt_engine = PromptEngine()  # Initialize prompt engine
    except Exception as e:
        logger.error(f"Failed to initialize prompt engine: {e}")
        print("❌ Failed to initialize prompt engine. See logs for details.")
        return
        
    log_event(
        "Sage is running in always-listening mode. Voice=OFF."
    )
    
    # Welcome message (text-only)
    welcome_message = (
        f"\n👋 Hello {USER_NAME}, Sage is {'listening via voice' if USE_VOICE else 'awaiting text input'}. "
        f"{'Speak' if USE_VOICE else 'Type'} something to Sage to start."
    )
    print(welcome_message)
        
    try:
        # Create a main loop counter to track iterations and reinitialization needs
        loop_counter = 0
        error_count = 0
        
        while True:
            loop_counter += 1
            log_event(f"[LISTENING] 🎤 Listening for user input... (loop #{loop_counter})")
                
            try:
                # Get user input (voice or text)
                if USE_VOICE:
                    user_input = get_voice_input()
                else:
                    user_input = cli.get_input()
                log_event(f"[DEBUG] Received user input: {user_input}")
            except Exception as e:
                log_event(f"⚠️ Input error: {e}", level="error")
                print(f"⚠️ Input error: {e}")
                # Track errors but don't exit
                error_count += 1
                # Add small non-blocking delay before retrying
                await asyncio.sleep(1)
                continue  # Continue listening
                
            if not user_input:
                log_event("[LISTENING] 🔇 No input detected. Continuing to listen...")
                # Add small non-blocking delay to prevent CPU spinning when no input
                await asyncio.sleep(0.5)
                continue  # Skip if no input
            
            # Reset error count when we successfully get input
            error_count = 0
            
            log_event(f"[INPUT] 🗣️ User input received: {user_input}")
            
            # Check if input is for Sage - run in background for better responsiveness
            intent_task = asyncio.create_task(is_input_for_sage(user_input))
            try:
                is_for_sage = await asyncio.wait_for(intent_task, timeout=5)
            except asyncio.TimeoutError:
                log_event("⚠️ Intent detection timed out, defaulting to True", level="warning")
                is_for_sage = True
            
            if is_for_sage:  # Check if input is for Sage
                log_event(f"[INPUT] 🧭 Input directed at Sage: {user_input}")
                try:
                    memory.log_interaction("user", user_input)  # Log user input in memory
                    log_event("[MEMORY] 📚 User interaction logged in memory.")
                except Exception as e:
                    log_event(f"[MEMORY] Error logging user interaction: {e}", level="error")
                    print(f"❌ Error logging user input: {e}")
                    continue
                    
                context = memory.get_context()  # Retrieve conversation context
                log_event(f"[DEBUG] Retrieved context: {context}")
                
                try:
                    # Generate Sage's response using core logic
                    sage_reply = generate_response(user_input, context=context, prompt_engine=prompt_engine)
                    log_event(f"[RESPONSE] 💬 Sage response generated: {sage_reply}")
                except Exception as e:
                    log_event(f"⚠️ Response generation error: {e}", level="error")
                    print(f"❌ Error generating Sage's response: {e}")
                    continue
                    
                try:
                    memory.log_interaction("sage", sage_reply)  # Log Sage's response
                    log_event("[MEMORY] 📚 Sage interaction logged in memory.")
                except Exception as e:
                    log_event(f"[MEMORY] Error logging Sage interaction: {e}", level="error")
                    print(f"❌ Error logging Sage's response: {e}")
                    
                try:
                    cli.display_response(sage_reply)  # Display response in CLI
                    log_event("[OUTPUT] 🖥️ Response displayed in CLI.")
                    # Speak response if voice mode
                    if USE_VOICE:
                        speak_text(sage_reply)
                except Exception as e:
                    log_event(f"[OUTPUT] Error displaying response: {e}", level="error")
                    print(f"❌ Error displaying response: {e}")
            else:
                log_event(f"[INPUT] 🤫 Casual speech detected: {user_input}")
                print("🤫 Not directed at Sage — ignoring.")  # Ignore non-Sage input
    except KeyboardInterrupt:
        log_event("🛑 Session manually stopped by user.", level="warning")  # Log manual stop
        print("\n🛑 Session manually stopped.")
    except Exception as e:
        log_event(f"⚠️ Unexpected error occurred: {e}", level="error")  # Log unexpected error
        print(f"⚠️ Unexpected error: {e}")
        import traceback
        log_event(f"Error traceback: {traceback.format_exc()}", level="error")
        print(f"Error details: {traceback.format_exc()}")
    finally:
        # Voice cleanup removed
         
        log_event("🔒 Shutting down Sage application.", level="info")  # Log shutdown
        print("🔒 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())  # Run the async main via asyncio event loop

