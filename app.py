# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import Config
from api_service import APIService
from database import Database
from line_tracker import LineTracker

# Initialize components
config = Config()
api_service = APIService(
    base_url=config.API_BASE_URL,
    headers=config.HEADERS,
    bookie_map=config.BOOKIE_MAP
)
db = Database()
line_tracker = LineTracker(db)

# Page config
st.set_page_config(
    page_title="NFL Betting Lines Tracker",
    page_icon="🏈",
    layout="wide"
)

def format_odds(odds: int) -> str:
    """Format odds for display"""
    return f"+{odds}" if odds > 0 else str(odds)

def plot_line_history(history_data: list) -> go.Figure:
    """Create line movement plot"""
    fig = go.Figure()
    
    bookies = set(h.bookie_id for h in history_data)
    for bookie_id in bookies:
        bookie_data = [h for h in history_data if h.bookie_id == bookie_id]
        bookie_name = config.BOOKIE_MAP.get(bookie_id, str(bookie_id))
        
        fig.add_trace(go.Scatter(
            x=[h.timestamp for h in bookie_data],
            y=[h.odds for h in bookie_data],
            name=bookie_name,
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title="Line Movement History",
        xaxis_title="Time",
        yaxis_title="Odds",
        height=400
    )
    
    return fig

def main():
    st.title("NFL Betting Lines Tracker")
    
    # Fetch current events
    events = api_service.fetch_events()
    if not events:
        st.error("No events found")
        return
    
    # Event selection
    event_options = {
        f"{info['away']} @ {info['home']}": event_id 
        for event_id, info in events.items()
    }
    selected_event = st.selectbox(
        "Select Event",
        options=list(event_options.keys())
    )
    event_id = event_options[selected_event]
    
    # Market type tabs
    tab1, tab2 = st.tabs(["Game Lines", "Player Props"])
    
    with tab1:
        st.header("Game Lines")
        
        # Game lines markets
        for market_name, market_id in [
            ("Moneyline", config.MARKET_CONFIG['game_lines']['moneyline']),
            ("Spread", config.MARKET_CONFIG['game_lines']['spread']),
            ("Total", config.MARKET_CONFIG['game_lines']['total'])
        ]:
            st.subheader(market_name)
            
            # Get current lines
            current_lines = db.get_current_lines(event_id, market_id)
            if current_lines:
                # Format data for display
                data = []
                for line in current_lines:
                    data.append({
                        'Bookie': config.BOOKIE_MAP.get(line.bookie_id),
                        'Selection': line.selection,
                        'Line': line.line_value,
                        'Odds': format_odds(line.odds)
                    })
                
                # Show as dataframe
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # Line movement chart
                history = db.get_line_history(event_id, market_id)
                if history:
                    fig = plot_line_history(history)
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Player Props")
        
        # Props markets
        for market_id, market_name in config.MARKET_CONFIG['props'].items():
            with st.expander(market_name):
                current_lines = db.get_current_lines(event_id, market_id)
                if current_lines:
                    data = []
                    for line in current_lines:
                        data.append({
                            'Player': line.player_name,
                            'Bookie': config.BOOKIE_MAP.get(line.bookie_id),
                            'Selection': line.selection,
                            'Line': line.line_value,
                            'Odds': format_odds(line.odds)
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    history = db.get_line_history(event_id, market_id)
                    if history:
                        fig = plot_line_history(history)
                        st.plotly_chart(fig, use_container_width=True)
    
    # Line Movement Alerts
    st.sidebar.header("Recent Line Movements")
    movements = line_tracker.check_line_movements(event_id)
    
    if movements:
        for move in movements:
            with st.sidebar.expander(
                f"{move['selection']} ({config.BOOKIE_MAP.get(move['bookie_id'])})",
                expanded=True
            ):
                st.write(f"**Market ID:** {move['market_id']}")
                if move['player_name']:
                    st.write(f"**Player:** {move['player_name']}")
                st.write(f"**Odds Movement:** {move['previous_odds']} → {move['current_odds']}")
                if move['line_movement']:
                    st.write(f"**Line Movement:** {move['previous_line']} → {move['current_line']}")
                st.write(f"**Time:** {move['timestamp']}")
    else:
        st.sidebar.info("No significant line movements detected")

if __name__ == "__main__":
    main()
