# scheduler.py
import schedule
import time
from datetime import datetime
from api_service import APIService
from database import Database
from line_tracker import LineTracker
from typing import List, Dict

class UpdateScheduler:
    def __init__(self, api_service: APIService, db: Database, line_tracker: LineTracker):
        self.api_service = api_service
        self.db = db
        self.line_tracker = line_tracker
        self.movements = []  # Store recent movements
        
    def update_markets(self):
        """Update all markets and check for movements"""
        try:
            print(f"\nUpdating markets at {datetime.now()}")
            
            # Fetch and store events
            events = self.api_service.fetch_events()
            for event_data in events.values():
                self.db.save_event(event_data)
            
            for event_id in events.keys():
                # Update game lines
                for market_type, market_id in [
                    ('game_lines', 1),  # Moneyline
                    ('game_lines', 2),  # Total
                    ('game_lines', 3),  # Spread
                    ('props', 102),     # Passing TDs
                    ('props', 103),     # Passing Yards
                    # Add other markets as needed
                ]:
                    lines = self.api_service.fetch_market_odds(
                        market_type, market_id, [event_id]
                    )
                    if lines:
                        self.db.save_lines(lines)
                
                # Check for movements
                new_movements = self.line_tracker.check_line_movements(event_id)
                if new_movements:
                    print(f"\nFound {len(new_movements)} significant line movements!")
                    self.movements.extend(new_movements)
                    # Keep only recent movements (last 100)
                    self.movements = self.movements[-100:]
        
        except Exception as e:
            print(f"Error in update: {e}")
    
    def start(self, interval_minutes: int = 5):
        """Start the scheduler"""
        print(f"Starting scheduler with {interval_minutes} minute interval")
        
        # Run initial update
        self.update_markets()
        
        # Schedule regular updates
        schedule.every(interval_minutes).minutes.do(self.update_markets)
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def get_recent_movements(self) -> List[Dict]:
        """Get recent line movements"""
        return self.movements
