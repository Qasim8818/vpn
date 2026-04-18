#!/usr/bin/env python3
"""
24/7 Local Agent Daemon
Runs continuously in the background for always-on assistance.
"""

import sys
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

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
        self.log_file = os.path.join(_BASE_DIR, "agent_daemon.log")
        
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
        except Exception:
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
    
    def _attempt_reconnect(self):
        """Try to reconnect Qdrant if it went offline."""
        try:
            self.agent.memory._connect()
            self.agent.rag._connect()
            if self.agent.memory.available:
                self._log("✓ Qdrant reconnected")
        except Exception as e:
            self._log(f"Reconnect failed: {e}")

    def run(self):
        """Main daemon loop."""
        self._log("🚀 Starting Local Agent Daemon")
        self.agent.show_status()
        self._log("✓ Daemon is running. Press Ctrl+C to stop.")

        consecutive_ollama_failures = 0
        consecutive_memory_failures = 0

        try:
            while self.running:
                health = self.agent.health_check()

                # Ollama failure tracking
                if not health["ollama_running"]:
                    consecutive_ollama_failures += 1
                    self._log(f"⚠️ Ollama not responding (failure #{consecutive_ollama_failures})")
                    if consecutive_ollama_failures >= 3:
                        self._log("❌ Ollama has been down for 3+ cycles. Check: ollama serve")
                else:
                    if consecutive_ollama_failures > 0:
                        self._log("✓ Ollama recovered")
                    consecutive_ollama_failures = 0

                # Memory failure tracking + reconnect attempt
                if not health["memory_available"]:
                    consecutive_memory_failures += 1
                    self._log(f"⚠️ Memory system not responding (failure #{consecutive_memory_failures})")
                    if consecutive_memory_failures % 3 == 0:
                        self._log("↺ Attempting Qdrant reconnect...")
                        self._attempt_reconnect()
                else:
                    if consecutive_memory_failures > 0:
                        self._log("✓ Memory system recovered")
                    consecutive_memory_failures = 0

                # Log memory stats
                memory_stats = health.get("memory_stats", {})
                for col_name, col_stats in memory_stats.items():
                    if "error" not in col_stats:
                        point_count = col_stats.get("point_count", 0)
                        if point_count > 0:
                            self._log(f"  📚 {col_name}: {point_count} stored items")

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
