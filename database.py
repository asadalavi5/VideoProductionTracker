"""
Database models for Video Production Tracker
"""

from datetime import datetime
from typing import Dict, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Video(db.Model):
    """Video data model"""
    
    __tablename__ = 'videos'
    
    VALID_STATUSES = ['Conceptualization & Script', 'VO', 'Visuals', 'Animations & Editing', 'Final']
    VALID_TYPES = ['Brand', 'System', 'Testimonial', 'About']
    TESTIMONIAL_STATUSES = ['Conceptualization & Script', 'Avatar Creation', 'Avatar Video Generation', 'VO', 'Visuals', 'Animations & Editing', 'Final']
    
    id = db.Column(db.String(100), primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Conceptualization & Script')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage based on current status"""
        try:
            # Use different status lists based on video type
            if self.type == 'Testimonial':
                statuses = self.TESTIMONIAL_STATUSES
            else:
                statuses = self.VALID_STATUSES
            
            status_index = statuses.index(self.status)
            return ((status_index + 1) / len(statuses)) * 100
        except ValueError:
            return 0.0
    
    def is_completed(self) -> bool:
        """Check if video is completed"""
        return self.status == 'Final'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return f"Video(id={self.id}, type={self.type}, status={self.status})"

class Cost(db.Model):
    """Cost entry data model"""
    
    __tablename__ = 'costs'
    
    VALID_TYPES = ['Tool', 'Freelancer', 'Other']
    VALID_CURRENCIES = ['USD', 'PKR']
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=True)  # Name for Tool/Freelancer
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='USD')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_formatted_amount(self) -> str:
        """Get formatted amount with currency symbol"""
        if self.currency == 'USD':
            return f"${self.amount:.2f}"
        elif self.currency == 'PKR':
            return f"₨{self.amount:.2f}"
        else:
            return f"{self.amount:.2f} {self.currency}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'amount': self.amount,
            'currency': self.currency,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __str__(self) -> str:
        return f"Cost(id={self.id}, type={self.type}, amount={self.get_formatted_amount()})"

class Settings(db.Model):
    """Settings/configuration data model"""
    
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __str__(self) -> str:
        return f"Settings(key={self.key}, value={self.value})"