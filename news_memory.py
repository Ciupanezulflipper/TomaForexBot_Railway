import json
import time
import os
import logging

logger = logging.getLogger(__name__)

class NewsMemory:
    def __init__(self, memory_file="bot_memory.json"):
        """Give the bot a memory notebook to store seen news."""
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        """Load memory from JSON file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"[NewsMemory] Failed to load memory: {e}")
            return {}

    def save_memory(self):
        """Save memory to JSON file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.warning(f"[NewsMemory] Failed to save memory: {e}")

    def already_sent(self, news_url: str) -> bool:
        """Check if the news URL was already processed."""
        return news_url in self.memory

    def remember_news(self, news_url: str):
        """Mark a news URL as seen."""
        self.memory[news_url] = time.time()
        self.save_memory()

    def forget_old_news(self, hours: int = 24):
        """Remove news entries older than the given number of hours."""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        old_news = [url for url, ts in self.memory.items() if ts < cutoff_time]

        for url in old_news:
            del self.memory[url]

        self.save_memory()

    def is_news_too_old(self, news_timestamp: float, hours: int = 12) -> bool:
        """Check if a news item is too old based on timestamp."""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        return news_timestamp < cutoff_time
