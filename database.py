# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, unique=True)
    home_team = Column(String)
    away_team = Column(String)
    start_time = Column(DateTime)
    status = Column(String)
    lines = relationship("BettingLine", back_populates="event")

class BettingLine(Base):
    __tablename__ = 'betting_lines'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('events.event_id'))
    market_id = Column(Integer)
    market_type = Column(String)  # 'game_lines' or 'props'
    bookie_id = Column(Integer)
    player_name = Column(String, nullable=True)  # For props
    selection = Column(String)
    line_value = Column(Float)
    odds = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event", back_populates="lines")

class Database:
    def __init__(self, database_url="sqlite:///betting_lines.db"):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        
        # Make models available to other classes
        self.Event = Event
        self.BettingLine = BettingLine
        
    def save_event(self, event_data):
        """Save or update event information"""
        with self.SessionLocal() as session:
            existing = session.query(Event).filter_by(
                event_id=event_data['event_id']
            ).first()
            
            if existing:
                existing.home_team = event_data['home']
                existing.away_team = event_data['away']
                existing.start_time = datetime.fromisoformat(event_data['scheduled'].replace('Z', '+00:00'))
                existing.status = event_data['status']
            else:
                event = Event(
                    event_id=event_data['event_id'],
                    home_team=event_data['home'],
                    away_team=event_data['away'],
                    start_time=datetime.fromisoformat(event_data['scheduled'].replace('Z', '+00:00')),
                    status=event_data['status']
                )
                session.add(event)
            
            session.commit()
    
    def save_lines(self, lines):
        """Save betting lines to database"""
        with self.SessionLocal() as session:
            for line_data in lines:
                line = BettingLine(
                    event_id=line_data['event_id'],
                    market_id=line_data['market_id'],
                    market_type=line_data.get('market_type', 'game_lines'),
                    bookie_id=line_data['bookie_id'],
                    player_name=line_data.get('player_name'),
                    selection=line_data['selection'],
                    line_value=line_data['line_value'],
                    odds=line_data['odds'],
                    timestamp=datetime.fromisoformat(line_data['timestamp'])
                )
                session.add(line)
            session.commit()
    
    def get_line_history(self, event_id, market_id, selection=None, hours=24):
        """Get line history for a specific market"""
        with self.SessionLocal() as session:
            query = session.query(BettingLine).filter(
                BettingLine.event_id == event_id,
                BettingLine.market_id == market_id,
                BettingLine.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            )
            
            if selection:
                query = query.filter(BettingLine.selection == selection)
                
            return query.order_by(BettingLine.timestamp).all()
    
    def get_current_lines(self, event_id, market_id):
        """Get current lines for a specific market"""
        with self.SessionLocal() as session:
            # Get the most recent timestamp for this market
            latest_time = session.query(BettingLine.timestamp).\
                filter(BettingLine.event_id == event_id,
                       BettingLine.market_id == market_id).\
                order_by(BettingLine.timestamp.desc()).\
                first()
            
            if not latest_time:
                return []
                
            # Get all lines from that timestamp
            return session.query(BettingLine).\
                filter(BettingLine.event_id == event_id,
                       BettingLine.market_id == market_id,
                       BettingLine.timestamp == latest_time[0]).\
                all()
