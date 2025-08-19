"""
Background Task Manager for A1 Call Taxi
Handles periodic cleanup tasks and maintenance operations.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
# Session cleanup removed - pure JWT doesn't need session cleanup

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
        from app import app, db, get_ist_time
        
        # Wait 10 minutes after startup before first cleanup to allow proper initialization
        logging.info("Background cleanup starting in 10 minutes...")
        time.sleep(600)
        
        while self.running:
            try:
                with app.app_context():
                    # Mark drivers offline if they haven't been seen for too long
                    # Use 60 minutes threshold to be much less aggressive 
                    threshold = get_ist_time() - timedelta(minutes=60)
                    
                    from models import Driver
                    stale_drivers = Driver.query.filter(
                        Driver.is_online == True,
                        Driver.last_seen < threshold
                    ).all()
                    
                    for driver in stale_drivers:
                        driver.is_online = False
                        logging.info(f"Marked driver {driver.name} ({driver.phone}) as offline due to inactivity")
                    
                    if stale_drivers:
                        db.session.commit()
                        logging.info(f"Background cleanup completed - marked {len(stale_drivers)} stale drivers offline")
                
                # Sleep for 15 minutes before next cleanup
                time.sleep(900)
                
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