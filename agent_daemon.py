#!/usr/bin/env python3
"""
24/7 Local Agent Daemon
Runs continuously in the background for always-on assistance.
"""

import sys
sys.path.insert(0, "/home/killer123/Desktop/vpn")

from local_agent import LocalAgent
import time
import json
from datetime import datetime
import signal

class AgentDaemon:
    """Daemon process for 24/7 agent operation."""
    
    def __init__(self):
        self.agent = LocalAgent()
        self.running = True
        self.start_time = datetime.now()
        self.queries_processed = 0
        self.log_file = "/home/killer123/Desktop/vpn/agent_daemon.log"
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        self.running = False
        self._log("🛑 Received shutdown signal. Closing gracefully...")
        self._print_statistics()
        exit(0)
    
    def _log(self, message: str):
        """Log message to file and stdout."""
        timestamp = datetime.now().isoformat()
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")
        except:
            pass
    
    def _print_statistics(self):
        """Print daemon statistics."""
        uptime = datetime.now() - self.start_time
        self._log(f"\n{'='*50}")
        self._log(f"📊 Daemon Statistics")
        self._log(f"{'='*50}")
        self._log(f"Uptime: {uptime}")
        self._log(f"Queries Processed: {self.queries_processed}")
        self._log(f"Start Time: {self.start_time.isoformat()}")
        self._log(f"{'='*50}\n")
    
    def run(self):
        """Main daemon loop."""
        self._log("🚀 Starting Local Agent Daemon")
        self.agent.show_status()
        
        self._log("✓ Daemon is running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                # Perform periodic tasks
                health = self.agent.health_check()
                
                if not health["ollama_running"]:
                    self._log("⚠️ Ollama not responding")
                
                if not health["memory_available"]:
                    self._log("⚠️ Memory system not responding")
                
                # Log memory stats periodically
                memory_stats = health.get("memory_stats", {})
                for col_name, col_stats in memory_stats.items():
                    if "error" not in col_stats:
                        point_count = col_stats.get("point_count", 0)
                        if point_count > 0:
                            self._log(f"  📚 {col_name}: {point_count} stored items")
                
                # Sleep for check interval (30 seconds)
                time.sleep(30)
        
        except Exception as e:
            self._log(f"❌ Daemon error: {e}")
            self._print_statistics()
            raise

def main():
    """Entry point for the daemon."""
    daemon = AgentDaemon()
    daemon.run()

if __name__ == "__main__":
    main()
