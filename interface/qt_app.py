import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QLineEdit,
    QFrame,
    QSplitter,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QTextBrowser,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap
from core.memory import Memory
from core.brain import generate_response
from core.weekly_sage import WeeklySage
from core.Idea_garden import IdeaGarden
from utils.async_operations import run_in_background, wait_for_task, background_task_status
from utils.task_queue import global_task_queue


class SageChatWindow(QWidget):
    """
    Main window for the Sage desktop GUI.
    Provides chat, advanced features, and a glowing avatar.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sage – Your Reflective AI Companion")
        self.setGeometry(200, 200, 900, 650)
        self.memory: Memory = Memory()  # Initialize memory for chat context
        
        # Initialize the async processing systems
        self.pending_tasks = {}
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.check_pending_tasks)
        self.processing_timer.start(500)  # Check every 500ms
        
        # Voice processing removed
        
        self.init_ui()  # Set up the UI

    def init_ui(self) -> None:
        """Initialize the UI layout and widgets."""
        main_layout = QVBoxLayout(self)
        # Top bar with glowing avatar
        top_bar = QHBoxLayout()
        self.avatar_glow = QLabel()  # Glowing effect label
        self.avatar_glow.setObjectName("avatarGlow")
        self.avatar_glow.setFixedSize(80, 80)
        avatar_img = QLabel()  # Avatar image label
        avatar_img.setObjectName("avatarImg")
        avatar_img.setFixedSize(60, 60)
        avatar_img_path = Path("static") / "sage_avatar.png"
        avatar_img.setPixmap(
            QPixmap(str(avatar_img_path)).scaled(
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        avatar_frame = QVBoxLayout()
        avatar_frame.addWidget(self.avatar_glow, alignment=Qt.AlignCenter)
        avatar_frame.addWidget(avatar_img, alignment=Qt.AlignCenter)
        avatar_frame.setSpacing(-60)
        top_bar.addLayout(avatar_frame)
        top_bar.addStretch(1)
        self.status_label = QLabel("Listening...")  # Status label
        self.status_label.setStyleSheet("color: #00ffd5; font-weight: bold; font-size: 1.2rem;")
        top_bar.addWidget(self.status_label)
        top_bar.addStretch(10)
        main_layout.addLayout(top_bar)

        # Splitter for chat and advanced features
        splitter = QSplitter(Qt.Horizontal)
        # Left: Chat (now using QTextBrowser for HTML bubbles)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        self.chat_browser = QTextBrowser()  # Chat display area
        self.chat_browser.setOpenExternalLinks(True)
        self.chat_browser.setStyleSheet(
            "border-radius: 12px; background: #23234b; padding: 8px; border: 1.5px solid #00ffd5;"
        )
        chat_layout.addWidget(self.chat_browser)
        
        # Progress bar for background tasks
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar {border: 1px solid #00ffd5; border-radius: 5px; text-align: center;} QProgressBar::chunk {background-color: #00ffd5;}")
        chat_layout.addWidget(self.progress_bar)
        
        input_layout = QHBoxLayout()
        self.input_box = QTextEdit()  # User input box
        self.input_box.setPlaceholderText("Speak your mind...")
        self.input_box.setFixedHeight(60)
        input_layout.addWidget(self.input_box)
        self.send_btn = QPushButton("Reflect")  # Send button
        self.send_btn.clicked.connect(self.handle_send)
        input_layout.addWidget(self.send_btn)
        chat_layout.addLayout(input_layout)
        splitter.addWidget(chat_widget)

        # Right: Advanced features
        adv_widget = QWidget()
        adv_layout = QVBoxLayout(adv_widget)
        # Weekly Reflection
        wr_label = QLabel("<b>Weekly Reflection</b>")
        self.wr_btn = QPushButton("Get Weekly Reflection")
        self.wr_btn.clicked.connect(self.get_weekly_reflection)
        self.wr_result = QLabel()
        self.wr_result.setWordWrap(True)
        adv_layout.addWidget(wr_label)
        adv_layout.addWidget(self.wr_btn)
        adv_layout.addWidget(self.wr_result)
        # Idea Garden
        ig_label = QLabel("<b>Idea Garden</b>")
        self.ig_input = QLineEdit()
        self.ig_input.setPlaceholderText("Enter idea or block...")
        ig_btns = QHBoxLayout()
        self.ig_grow_btn = QPushButton("Grow Idea")
        self.ig_grow_btn.clicked.connect(lambda: self.idea_garden("grow"))
        self.ig_reframe_btn = QPushButton("Reframe Block")
        self.ig_reframe_btn.clicked.connect(lambda: self.idea_garden("reframe"))
        self.ig_themes_btn = QPushButton("Map Themes")
        self.ig_themes_btn.clicked.connect(lambda: self.idea_garden("themes"))
        ig_btns.addWidget(self.ig_grow_btn)
        ig_btns.addWidget(self.ig_reframe_btn)
        ig_btns.addWidget(self.ig_themes_btn)
        self.ig_result = QLabel()
        self.ig_result.setWordWrap(True)
        adv_layout.addWidget(ig_label)
        adv_layout.addWidget(self.ig_input)
        adv_layout.addLayout(ig_btns)
        adv_layout.addWidget(self.ig_result)
        # Memory Summary
        ms_label = QLabel("<b>Memory Summary</b>")
        self.ms_btn = QPushButton("Show Memory Summary")
        self.ms_btn.clicked.connect(self.get_memory_summary)
        self.ms_result = QLabel()
        self.ms_result.setWordWrap(True)
        adv_layout.addWidget(ms_label)
        adv_layout.addWidget(self.ms_btn)
        adv_layout.addWidget(self.ms_result)
        
        # Clear Memory
        self.clear_btn = QPushButton("Clear Memory")
        self.clear_btn.clicked.connect(self.clear_memory)
        adv_layout.addWidget(self.clear_btn)
        adv_layout.addStretch(1)
        splitter.addWidget(adv_widget)
        splitter.setSizes([600, 300])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self.refresh_chat()
        self.update_avatar_glow()

    def refresh_chat(self) -> None:
        """Refresh the chat display with the latest conversation."""
        self.chat_browser.clear()
        # Display the last 20 messages in the chat
        for role, message in self.memory.get_context()[-20:]:
            if role == "sage":
                bubble = f"<div style='background:#00ffd5; color:#181824; border-radius:16px; padding:12px 18px; margin:8px 40px 8px 0; text-align:left; font-weight:bold;'>Sage: {message}</div>"
            else:
                bubble = f"<div style='background:#23234b; color:#00ffd5; border-radius:16px; padding:12px 18px; margin:8px 0 8px 40px; text-align:right;'>User: {message}</div>"
            self.chat_browser.append(bubble)
        self.chat_browser.verticalScrollBar().setValue(
            self.chat_browser.verticalScrollBar().maximum()
        )
        self.update_avatar_glow()

    @run_in_background(priority=10)
    def generate_sage_response(self, user_input: str):
        """
        Generate Sage's response in the background.
        This allows the UI to remain responsive while processing.
        """
        context = self.memory.get_context()
        response = generate_response(user_input, context=context)
        return response

    def handle_send(self) -> None:
        """Handle sending user input and generating Sage's response using async operations"""
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        
        # Log and display user input immediately
        self.memory.log_interaction("user", user_input)
        self.refresh_chat()
        self.input_box.clear()
        
        # Show processing indicator
        self.progress_bar.setVisible(True)
        self.status_label.setText("Thinking...")
        
        # Process in background
        task_id = self.generate_sage_response(user_input)
        self.pending_tasks[task_id] = "response"
        
    def check_pending_tasks(self):
        """Check status of pending background tasks and update UI accordingly"""
        tasks_to_remove = []
        
        for task_id, task_type in self.pending_tasks.items():
            status = background_task_status(task_id)
            
            if status["is_complete"]:
                if task_type == "response":
                    # Handle completed response
                    sage_reply = status["result"]
                    self.memory.log_interaction("sage", sage_reply)
                    self.refresh_chat()
                    
                    # Use optimized voice output with quick phrase detection
                    if len(sage_reply.split()) < 15:
                        # Short responses get faster processing
                        pass
                    else:
                        # Longer responses get background processing
                        pass
                        
                    self.progress_bar.setVisible(False)
                    self.status_label.setText("Listening...")
                    tasks_to_remove.append(task_id)
                    
                elif task_type == "weekly":
                    # Handle weekly reflection
                    reflection, title = status["result"]
                    self.wr_result.setText(
                        f"<b>Title:</b> {title}<br><b>Reflection:</b> {reflection}"
                    )
                    self.progress_bar.setVisible(False)
                    tasks_to_remove.append(task_id)
                    
                elif task_type == "idea_garden":
                    # Handle idea garden results
                    self.ig_result.setText(status["result"])
                    self.progress_bar.setVisible(False)
                    tasks_to_remove.append(task_id)
                    
                elif task_type == "memory_summary":
                    # Handle memory summary
                    self.ms_result.setText(status["result"])
                    self.progress_bar.setVisible(False)
                    tasks_to_remove.append(task_id)
            
            elif status["is_failed"]:
                self.progress_bar.setVisible(False)
                self.status_label.setText("Listening...")
                tasks_to_remove.append(task_id)
        
        # Remove processed tasks
        for task_id in tasks_to_remove:
            del self.pending_tasks[task_id]

    @run_in_background
    def get_weekly_reflection_task(self):
        """Background task for weekly reflection generation"""
        ws = WeeklySage(self.memory)
        reflection = ws.reflect_on_week()
        title = ws.generate_title_for_week()
        return reflection, title

    def get_weekly_reflection(self) -> None:
        """Fetch and display the weekly reflection and title."""
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating reflection...")
        
        task_id = self.get_weekly_reflection_task()
        self.pending_tasks[task_id] = "weekly"

    @run_in_background
    def process_idea_garden_task(self, action: str, idea: str = ""):
        """Background task for idea garden operations"""
        ig = IdeaGarden(self.memory)
        if action == "grow":
            result = ig.grow_idea(idea)
        elif action == "reframe":
            result = ig.reframe_block(idea)
        elif action == "themes":
            result = ig.map_weekly_themes()
        else:
            result = "Invalid action."
        return result

    def idea_garden(self, action: str) -> None:
        """Handle Idea Garden actions (grow, reframe, themes)."""
        idea = self.ig_input.text().strip()
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Processing idea garden...")
        
        task_id = self.process_idea_garden_task(action, idea)
        self.pending_tasks[task_id] = "idea_garden"

    @run_in_background
    def get_memory_summary_task(self):
        """Background task for memory summary"""
        return self.memory.summarize_recent(limit=20)

    def get_memory_summary(self) -> None:
        """Display a summary of recent memory."""
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating memory summary...")
        
        task_id = self.get_memory_summary_task()
        self.pending_tasks[task_id] = "memory_summary"

    def clear_memory(self) -> None:
        """Clear all memory and reset advanced feature displays."""
        self.memory.clear_memory()
        self.refresh_chat()
        self.wr_result.clear()
        self.ig_result.clear()
        self.ms_result.clear()
        QMessageBox.information(self, "Memory Cleared", "All memory has been cleared.")

    def update_avatar_glow(self) -> None:
        """Update the avatar's glow color based on last user mood."""
        # Get the last user message's mood color from memory
        last_color = "#00ffd5"
        try:
            for entry in reversed(self.memory.memory["log"]):
                if (
                    entry["role"] == "user"
                    and "metadata" in entry
                    and "color" in entry["metadata"]
                ):
                    last_color = entry["metadata"]["color"]
                    break
        except Exception:
            pass
        self.avatar_glow.setStyleSheet(
            f"""
            QLabel {{
                border-radius: 40px;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 {last_color}, stop:1 transparent);
                border: 2px solid {last_color};
            }}
        """
        )


def main():
    """
    Main entry point for the PyQt GUI application.
    Initializes and runs the Sage chat window.
    """
    app = QApplication(sys.argv)
    # Load QSS stylesheet
    with open(Path("static") / "sage_style.qss", "r") as f:
        app.setStyleSheet(f.read())
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#181824"))
    palette.setColor(QPalette.Base, QColor("#23234b"))
    palette.setColor(QPalette.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.Button, QColor("#00ffd5"))
    palette.setColor(QPalette.ButtonText, QColor("#181824"))
    app.setPalette(palette)
    window = SageChatWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
