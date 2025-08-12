"""
Background Task Manager for A1 Call Taxi
Handles periodic cleanup tasks and maintenance operations.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from utils.session_manager import cleanup_expired_sessions, cleanup_stale_connections

class BackgroundTaskManager:
    def __init__(self):
        self.running = False
        self.cleanup_thread = None
        
    def start_cleanup_tasks(self):
        """Start background cleanup tasks"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self.cleanup_thread.start()
            logging.info("Background cleanup tasks started")
    
    def stop_cleanup_tasks(self):
        """Stop background cleanup tasks"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logging.info("Background cleanup tasks stopped")
    
    def _cleanup_worker(self):
        """Worker thread that runs cleanup tasks periodically"""
        from app import app
        while self.running:
            try:
                with app.app_context():
                    # Run session cleanup every 5 minutes
                    cleanup_expired_sessions()
                    
                    # Run stale connection cleanup every 2 minutes
                    cleanup_stale_connections()
                
                # Sleep for 2 minutes before next cleanup
                time.sleep(120)
                
            except Exception as e:
                logging.error(f"Error in background cleanup worker: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

# Global instance
task_manager = BackgroundTaskManager()

def initialize_background_tasks():
    """Initialize and start background tasks"""
    task_manager.start_cleanup_tasks()

def shutdown_background_tasks():
    """Shutdown background tasks"""
    task_manager.stop_cleanup_tasks()