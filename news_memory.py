import json
import time
import os

class NewsMemory:
    def __init__(self, memory_file="bot_memory.json"):
        """This is like giving your bot a notebook to remember things"""
        self.memory_file = memory_file
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load the bot's memory from its notebook"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def save_memory(self):
        """Save the bot's memory to its notebook"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except:
            pass
    
    def already_sent(self, news_url):
        """Check if bot already told this news"""
        return news_url in self.memory
    
    def remember_news(self, news_url):
        """Make bot remember it sent this news"""
        self.memory[news_url] = time.time()
        self.save_memory()
    
    def forget_old_news(self, hours=24):
        """Make bot forget news older than 24 hours"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        # Remove old memories
        old_news = [url for url, timestamp in self.memory.items() 
                   if timestamp < cutoff_time]
        
        for url in old_news:
            del self.memory[url]
        
        self.save_memory()
    
    def is_news_too_old(self, news_timestamp, hours=12):
        """Check if news is too old to care about"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        return news_timestamp < cutoff_time
