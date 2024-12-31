# config.py
class Config:
    API_BASE_URL = "https://api.bettingpros.com/v3"
    API_KEY = "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    
    BOOKIE_MAP = {
        0: "BettingPros",
        10: "Fanduel",
        12: "DraftKings",
        13: "Caesars",
        19: "BetMGM",
        24: "Bet365",
        33: "ESPNBet",
    }
    
    MARKET_CONFIG = {
        'game_lines': {
            'moneyline': 1,
            'spread': 3,
            'total': 2
        },
        'props': {
            102: "Passing Touchdowns",
            103: "Passing Yards",
            333: "Pass Attempts",
            100: "Completions",
            101: "Interceptions",
            106: "Rush Attempts",
            107: "Rush Yards",
            104: "Receptions",
            105: "Receiving Yards",
            253: "Fantasy Points",
        }
    }
