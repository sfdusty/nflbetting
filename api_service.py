# api_service.py
import requests
from datetime import datetime
from typing import Dict, List, Any

class APIService:
    def __init__(self, base_url: str, headers: Dict, bookie_map: Dict):
        self.base_url = base_url
        self.headers = headers
        self.bookie_map = bookie_map
        
    def fetch_events(self, sport="NFL", week=18, season=2024) -> Dict[str, Any]:
        """Fetch active events"""
        params = {
            "sport": sport,
            "week": week,
            "season": season
        }
        try:
            response = requests.get(
                f"{self.base_url}/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            events = response.json().get('events', [])
            
            event_info = {}
            for event in events:
                event_id = str(event['id'])
                event_info[event_id] = {
                    'event_id': event_id,
                    'home': event['participants'][1]['name'],
                    'away': event['participants'][0]['name'],
                    'scheduled': event['scheduled'],
                    'status': event.get('status', '').lower()
                }
            print(f"Fetched {len(event_info)} events.")
            return event_info
        except Exception as e:
            print(f"Error fetching events: {e}")
            return {}

    def fetch_market_odds(self, market_type: str, market_id: int, event_ids: List[str]) -> List[Dict]:
        """Fetch odds for a specific market"""
        if not event_ids:
            return []
            
        event_id_str = ','.join(event_ids)
        params = {
            "sport": "NFL",
            "market_id": market_id,
            "event_id": event_id_str,
            "location": "OH",
            "limit": 100
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/offers",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            offers = data.get("offers", [])
            processed_lines = []
            
            for offer in offers:
                # Handle different market types
                if market_type == 'game_lines':
                    processed_lines.extend(self._process_game_lines(offer, market_id))
                else:  # props
                    processed_lines.extend(self._process_props(offer, market_id))
                
            print(f"Processed {len(processed_lines)} lines for market {market_id}")
            return processed_lines
            
        except Exception as e:
            print(f"Error fetching market {market_id}: {e}")
            return []

    def _process_game_lines(self, offer: Dict, market_id: int) -> List[Dict]:
        """Process game lines markets (moneyline, spread, totals)"""
        processed_lines = []
        event_id = str(offer.get("event_id"))
        
        for selection in offer.get('selections', []):
            for book in selection.get('books', []):
                bookie_name = self.bookie_map.get(book['id'])
                if not bookie_name:
                    continue
                    
                for line in book.get('lines', []):
                    if not (line.get('active') and not line.get('replaced')):
                        continue
                    
                    side = selection.get('label', '')
                    line_value = line.get('line')
                    odds = line.get('cost')
                    
                    # Format the display string based on market type and side
                    if market_id == 1:  # Moneyline
                        display = f"{side} ({odds})"
                    elif market_id == 2:  # Total
                        display = f"{side} {line_value} ({odds})"
                    else:  # Spread
                        display = f"{side} {line_value:+g} ({odds})"
                        
                    line_data = {
                        'event_id': event_id,
                        'market_id': market_id,
                        'bookie': bookie_name,
                        'bookie_id': book['id'],
                        'selection': side,
                        'line_value': line_value,
                        'odds': odds,
                        'display': display,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    processed_lines.append(line_data)
        
        return processed_lines

    def _process_props(self, offer: Dict, market_id: int) -> List[Dict]:
        """Process player prop markets"""
        processed_lines = []
        event_id = str(offer.get("event_id"))
        
        # Get player info if available
        player_name = "Unknown"
        if offer.get('participants'):
            player = offer['participants'][0].get('player', {})
            player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}"
        
        for selection in offer.get('selections', []):
            for book in selection.get('books', []):
                bookie_name = self.bookie_map.get(book['id'])
                if not bookie_name:
                    continue
                    
                for line in book.get('lines', []):
                    if not (line.get('active') and not line.get('replaced')):
                        continue
                        
                    side = selection.get('label', '')
                    line_value = line.get('line')
                    odds = line.get('cost')
                    
                    display = f"{player_name} - {side} {line_value} ({odds})"
                        
                    line_data = {
                        'event_id': event_id,
                        'market_id': market_id,
                        'bookie': bookie_name,
                        'bookie_id': book['id'],
                        'player_name': player_name,
                        'selection': side,
                        'line_value': line_value,
                        'odds': odds,
                        'display': display,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    processed_lines.append(line_data)
        
        return processed_lines
