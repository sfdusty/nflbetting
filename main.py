# main.py
from config import Config
from api_service import APIService
from database import Database
from line_tracker import LineTracker
from scheduler import UpdateScheduler
import threading
from typing import Dict, List
from datetime import datetime
import time
from pprint import pprint

def format_market_data(lines: List[Dict]) -> Dict[str, Dict]:
    """Format market data by bookie for display"""
    formatted = {}
    for line in lines:
        bookie = line['bookie']
        if bookie not in formatted:
            formatted[bookie] = {}
        formatted[bookie][line['selection']] = line['display']
    return formatted

def test_markets():
    """Test market fetching and display functionality"""
    # Initialize components
    config = Config()
    api_service = APIService(
        base_url=config.API_BASE_URL,
        headers=config.HEADERS,
        bookie_map=config.BOOKIE_MAP
    )
    db = Database()
    line_tracker = LineTracker(db)
    
    # Fetch and store events
    print("\nFetching events...")
    events = api_service.fetch_events()
    
    if not events:
        print("No events found")
        return
        
    # Store events in database
    for event_data in events.values():
        db.save_event(event_data)
    
    # Print available events
    print("\nAvailable Events:")
    for event_id, info in events.items():
        print(f"{info['away']} @ {info['home']} (ID: {event_id})")
    
    # Get first event for testing
    test_event_id = list(events.keys())[0]
    test_event = events[test_event_id]
    print(f"\nFetching markets for: {test_event['away']} @ {test_event['home']}")
    
    # Test game lines markets
    market_types = {
        'Moneyline': ('game_lines', config.MARKET_CONFIG['game_lines']['moneyline']),
        'Spread': ('game_lines', config.MARKET_CONFIG['game_lines']['spread']),
        'Total': ('game_lines', config.MARKET_CONFIG['game_lines']['total'])
    }
    
    for market_name, (market_type, market_id) in market_types.items():
        print(f"\n{market_name} Market:")
        print("-" * 40)
        
        # Fetch current lines
        lines = api_service.fetch_market_odds(market_type, market_id, [test_event_id])
        
        # Store lines in database
        db.save_lines(lines)
        
        # Display lines
        formatted = format_market_data(lines)
        for bookie, offerings in formatted.items():
            print(f"\n{bookie}:")
            for selection, display in offerings.items():
                print(f"  {display}")
        
        # Show line history
        print("\nLine History:")
        history = db.get_line_history(test_event_id, market_id)
        for line in history:
            print(f"  {line.timestamp}: {line.selection} {line.line_value} ({line.odds})")
        
        # Check for significant movements
        movements = line_tracker.check_line_movements(test_event_id)
        if movements:
            print("\nSignificant Line Movements Detected:")
            for move in movements:
                print(f"  {move['selection']}: {move['previous_odds']} → {move['current_odds']}")
    
    # Test props
    print("\nPassing Touchdowns Props:")
    print("-" * 40)
    
    lines = api_service.fetch_market_odds('props', 102, [test_event_id])
    db.save_lines(lines)
    
    formatted = format_market_data(lines)
    for bookie, offerings in formatted.items():
        print(f"\n{bookie}:")
        for selection, display in offerings.items():
            print(f"  {display}")
            
    return events, line_tracker

def run_scheduler():
    """Run the scheduler in a separate thread"""
    config = Config()
    api_service = APIService(
        base_url=config.API_BASE_URL,
        headers=config.HEADERS,
        bookie_map=config.BOOKIE_MAP
    )
    db = Database()
    line_tracker = LineTracker(db)
    
    scheduler = UpdateScheduler(api_service, db, line_tracker)
    scheduler.start(interval_minutes=5)

def main():
    try:
        # Test market functionality first
        print("Testing market functionality...")
        events, line_tracker = test_markets()
        
        print("\nStarting continuous updates...")
        
        # Start scheduler in a separate thread
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Keep the main thread alive and occasionally check movements
        while True:
            time.sleep(60)  # Check every minute
            for event_id in events.keys():
                movements = line_tracker.check_line_movements(event_id)
                if movements:
                    print("\nNew Line Movements Detected:")
                    for move in movements:
                        print(f"  {move['selection']}: {move['previous_odds']} → {move['current_odds']}")
    
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error in main: {e}")
        raise
    finally:
        print("Exiting...")

if __name__ == "__main__":
    main()
