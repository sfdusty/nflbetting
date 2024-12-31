# line_tracker.py
from datetime import datetime, timedelta
from typing import List, Dict

class LineTracker:
    def __init__(self, db, significant_move: int = 15):
        self.db = db
        self.significant_move = significant_move  # Threshold for significant moves in odds points
    
    def check_line_movements(self, event_id: str, lookback_hours: int = 1) -> List[Dict]:
        """Check for significant line movements in the past hour"""
        movements = []
        
        with self.db.SessionLocal() as session:
            # Get unique market IDs for this event
            markets = session.query(self.db.BettingLine.market_id).filter(
                self.db.BettingLine.event_id == event_id
            ).distinct().all()
            
            for (market_id,) in markets:
                # Get lines from last update
                recent_lines = session.query(self.db.BettingLine).filter(
                    self.db.BettingLine.event_id == event_id,
                    self.db.BettingLine.market_id == market_id,
                    self.db.BettingLine.timestamp >= datetime.utcnow() - timedelta(hours=lookback_hours)
                ).order_by(self.db.BettingLine.timestamp.desc()).all()
                
                if not recent_lines:
                    continue
                
                # Group by bookie and selection
                latest_timestamp = recent_lines[0].timestamp
                latest_lines = {
                    f"{l.bookie_id}-{l.selection}": l 
                    for l in recent_lines 
                    if l.timestamp == latest_timestamp
                }
                
                previous_lines = {
                    f"{l.bookie_id}-{l.selection}": l 
                    for l in recent_lines 
                    if l.timestamp < latest_timestamp
                }
                
                # Check for movements
                for key, latest in latest_lines.items():
                    if key in previous_lines:
                        prev = previous_lines[key]
                        odds_move = latest.odds - prev.odds
                        line_move = latest.line_value - prev.line_value if latest.line_value and prev.line_value else 0
                        
                        if abs(odds_move) >= self.significant_move:
                            movements.append({
                                'event_id': event_id,
                                'market_id': market_id,
                                'bookie_id': latest.bookie_id,
                                'selection': latest.selection,
                                'player_name': latest.player_name,
                                'previous_odds': prev.odds,
                                'current_odds': latest.odds,
                                'odds_movement': odds_move,
                                'previous_line': prev.line_value,
                                'current_line': latest.line_value,
                                'line_movement': line_move,
                                'timestamp': latest.timestamp
                            })
        
        return movements
    
    def get_best_odds(self, event_id: str, market_id: int) -> Dict:
        """Get best available odds for each selection"""
        with self.db.SessionLocal() as session:
            latest_time = session.query(self.db.BettingLine.timestamp).\
                filter(self.db.BettingLine.event_id == event_id,
                       self.db.BettingLine.market_id == market_id).\
                order_by(self.db.BettingLine.timestamp.desc()).\
                first()
            
            if not latest_time:
                return {}
            
            current_lines = session.query(self.db.BettingLine).\
                filter(self.db.BettingLine.event_id == event_id,
                       self.db.BettingLine.market_id == market_id,
                       self.db.BettingLine.timestamp == latest_time[0]).\
                all()
            
            best_odds = {}
            for line in current_lines:
                selection = line.selection
                if selection not in best_odds or \
                   (line.odds > 0 and line.odds > best_odds[selection]['odds']) or \
                   (line.odds < 0 and line.odds > best_odds[selection]['odds']):
                    best_odds[selection] = {
                        'bookie_id': line.bookie_id,
                        'odds': line.odds,
                        'line_value': line.line_value
                    }
            
            return best_odds# line_tracker.py
from datetime import datetime, timedelta
from typing import List, Dict

class LineTracker:
    def __init__(self, db, significant_move: int = 15):
        self.db = db
        self.significant_move = significant_move  # Threshold for significant moves in odds points
    
    def check_line_movements(self, event_id: str, lookback_hours: int = 1) -> List[Dict]:
        """Check for significant line movements in the past hour"""
        movements = []
        
        with self.db.SessionLocal() as session:
            # Get unique market IDs for this event
            markets = session.query(self.db.BettingLine.market_id).filter(
                self.db.BettingLine.event_id == event_id
            ).distinct().all()
            
            for (market_id,) in markets:
                # Get lines from last update
                recent_lines = session.query(self.db.BettingLine).filter(
                    self.db.BettingLine.event_id == event_id,
                    self.db.BettingLine.market_id == market_id,
                    self.db.BettingLine.timestamp >= datetime.utcnow() - timedelta(hours=lookback_hours)
                ).order_by(self.db.BettingLine.timestamp.desc()).all()
                
                if not recent_lines:
                    continue
                
                # Group by bookie and selection
                latest_timestamp = recent_lines[0].timestamp
                latest_lines = {
                    f"{l.bookie_id}-{l.selection}": l 
                    for l in recent_lines 
                    if l.timestamp == latest_timestamp
                }
                
                previous_lines = {
                    f"{l.bookie_id}-{l.selection}": l 
                    for l in recent_lines 
                    if l.timestamp < latest_timestamp
                }
                
                # Check for movements
                for key, latest in latest_lines.items():
                    if key in previous_lines:
                        prev = previous_lines[key]
                        odds_move = latest.odds - prev.odds
                        line_move = latest.line_value - prev.line_value if latest.line_value and prev.line_value else 0
                        
                        if abs(odds_move) >= self.significant_move:
                            movements.append({
                                'event_id': event_id,
                                'market_id': market_id,
                                'bookie_id': latest.bookie_id,
                                'selection': latest.selection,
                                'player_name': latest.player_name,
                                'previous_odds': prev.odds,
                                'current_odds': latest.odds,
                                'odds_movement': odds_move,
                                'previous_line': prev.line_value,
                                'current_line': latest.line_value,
                                'line_movement': line_move,
                                'timestamp': latest.timestamp
                            })
        
        return movements
    
    def get_best_odds(self, event_id: str, market_id: int) -> Dict:
        """Get best available odds for each selection"""
        with self.db.SessionLocal() as session:
            latest_time = session.query(self.db.BettingLine.timestamp).\
                filter(self.db.BettingLine.event_id == event_id,
                       self.db.BettingLine.market_id == market_id).\
                order_by(self.db.BettingLine.timestamp.desc()).\
                first()
            
            if not latest_time:
                return {}
            
            current_lines = session.query(self.db.BettingLine).\
                filter(self.db.BettingLine.event_id == event_id,
                       self.db.BettingLine.market_id == market_id,
                       self.db.BettingLine.timestamp == latest_time[0]).\
                all()
            
            best_odds = {}
            for line in current_lines:
                selection = line.selection
                if selection not in best_odds or \
                   (line.odds > 0 and line.odds > best_odds[selection]['odds']) or \
                   (line.odds < 0 and line.odds > best_odds[selection]['odds']):
                    best_odds[selection] = {
                        'bookie_id': line.bookie_id,
                        'odds': line.odds,
                        'line_value': line.line_value
                    }
            
            return best_odds
