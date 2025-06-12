# utils/scheduler.py

import schedule
import time
import threading
from datetime import datetime
from core.memory import Memory
from core.weekly_sage import WeeklySage
from typing import NoReturn


def run_weekly_reflection() -> None:
    print("\n📅 Sunday Weekly Sage Check-In\n")
    memory = Memory()
    sage = WeeklySage(memory, mode="philosopher")
    title = sage.generate_title_for_week()
    reflection = sage.reflect_on_week()
    print(f"\n📖 Week Title: {title}\n")
    print(f"\n🧠 Weekly Reflection:\n{reflection}\n")
    with open("data/weekly_review_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n\n=== {datetime.now().strftime('%Y-%m-%d')} Weekly Review ===\n")
        f.write(f"Week Title: {title}\n\n{reflection}\n")


def start_scheduler() -> NoReturn:
    print("⏳ Sage Scheduler running... Will reflect every Sunday at 6pm.")
    schedule.every().sunday.at("18:00").do(run_weekly_reflection)

    def run_scheduler() -> NoReturn:
        while True:
            schedule.run_pending()
            time.sleep(60)

    threading.Thread(target=run_scheduler, daemon=True).start()
    while True:
        time.sleep(3600)
