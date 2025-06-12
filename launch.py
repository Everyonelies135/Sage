# launch.py

import os
import sys
import subprocess
import time
import threading
import signal
import asyncio
from bootstrap import needs_bootstrap, bootstrap
from pathlib import Path


def run_cli() -> None:
    """
    Launch the Sage CLI with proper process handling to prevent premature exit
    and ensure audio completes playing before the application exits.
    """
    print("🧠 Launching Sage CLI...")
    
    # Create a barrier thread that keeps the main process alive
    # This is crucial for preventing premature termination
    keep_alive_event = threading.Event()
    
    def keep_alive():
        """Thread that keeps the process alive until explicitly terminated"""
        while not keep_alive_event.is_set():
            time.sleep(0.5)
    
    # Start the keep-alive thread as non-daemon so it keeps the process running
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=False)
    keep_alive_thread.start()
    
    # Set up signal handler to ensure clean shutdown
    def handle_exit(signum, frame):
        print("\n🛑 Received exit signal. Cleaning up resources...")
        try:
            # Signal the keep-alive thread to exit
            keep_alive_event.set()
            
            # If we've already imported the voice input module, clean it up
            if 'interface.voice_input' in sys.modules:
                from interface.voice_input import stop_audio_processing
                stop_audio_processing()
                print("✅ Audio processing stopped.")
                
            # If there are any active voice output threads, wait for them
            active_threads = [t for t in threading.enumerate() 
                             if t.is_alive() and not t.daemon and t != threading.current_thread()
                             and t != keep_alive_thread]
            if active_threads:
                print(f"⏳ Waiting for {len(active_threads)} active threads to complete...")
                for thread in active_threads:
                    thread.join(timeout=3.0)  # Wait up to 3 seconds per thread
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        finally:
            print("👋 Goodbye!")
            sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        # Add the current directory to Python path so imports work properly
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import the main function
        from main import main
        
        # Run the main function in the current process
        print("🚀 Starting Sage CLI...")
        asyncio.run(main())
        
        # After main exits, ensure proper cleanup
        print("\n🔚 Sage execution completed, cleaning up...")
        
        # Signal the keep-alive thread to exit since main has completed
        keep_alive_event.set()
        
        # Wait for any non-daemon threads to finish
        active_threads = [t for t in threading.enumerate() 
                         if t.is_alive() and not t.daemon and t != threading.current_thread()
                         and t != keep_alive_thread]
        
        if active_threads:
            print(f"⏳ Waiting for {len(active_threads)} active threads to complete...")
            for thread in active_threads:
                thread.join(timeout=3.0)  # Wait up to 3 seconds per thread
            
        # Final cleanup of voice-related resources
        if 'interface.voice_input' in sys.modules:
            from interface.voice_input import stop_audio_processing
            stop_audio_processing()
            print("✅ Audio processing stopped.")
        
    except KeyboardInterrupt:
        print("\n🛑 Sage CLI stopped by user.")
        keep_alive_event.set()
    except Exception as e:
        print(f"\n❌ Error running Sage CLI: {e}")
        import traceback
        traceback.print_exc()
        keep_alive_event.set()
    finally:
        # Final safety check for threads
        active_threads = [t for t in threading.enumerate() 
                         if t.is_alive() and not t.daemon and t != threading.current_thread()
                         and t != keep_alive_thread]
        if active_threads:
            print(f"⚠️ {len(active_threads)} non-daemon threads still active at exit.")
            
        # Join the keep_alive thread to ensure proper termination
        keep_alive_thread.join(timeout=3.0)


def run_gui() -> None:
    print("🌐 Launching Sage PyQt GUI...")
    try:
        # Import and run directly instead of using subprocess
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from interface.qt_app import main as run_qt_app
        run_qt_app()
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        import traceback
        traceback.print_exc()


def run_scheduler() -> None:
    print("⏳ Starting Weekly Scheduler...")
    try:
        # Import and run directly instead of using subprocess
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from core.weekly_sage import main as run_weekly_scheduler
        run_weekly_scheduler()
    except Exception as e:
        print(f"❌ Error running scheduler: {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    if needs_bootstrap():
        bootstrap()
    print("\n✨ Welcome to Sage — Your Reflective AI Companion")
    print("Choose a launch mode:")
    print("1. CLI Mode (terminal)")
    print("2. GUI Mode (PyQt desktop)")
    print("3. Scheduler (weekly reflections)")
    print("0. Exit")
    choice = input("Enter number: ").strip()
    if choice == "1":
        run_cli()
    elif choice == "2":
        run_gui()
    elif choice == "3":
        run_scheduler()
    elif choice == "0":
        print("👋 Goodbye for now.")
        sys.exit()
    else:
        print("❌ Invalid choice.")
        main()


if __name__ == "__main__":
    main()
