"""
Data models for Video Production Tracker
Using PostgreSQL with SQLAlchemy
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
import json
import logging
from app import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class Video(db.Model):
    """Video data model with validation"""
    
    __tablename__ = 'videos'
    
    VALID_STATUSES = ['Script', 'VO', 'Visuals', 'Editing', 'Final']
    VALID_TYPES = ['Brand', 'System', 'Testimonial']
    
    id = db.Column(db.String(100), primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Script')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, id: str, type: str, status: str = 'Script'):
        self.id = self._validate_id(id)
        self.type = self._validate_type(type)
        self.status = self._validate_status(status)
    
    def _validate_id(self, id: str) -> str:
        """Validate video ID"""
        if not id or not isinstance(id, str):
            raise ValidationError("Video ID must be a non-empty string")
        
        # Remove extra whitespace
        id = id.strip()
        
        if not id:
            raise ValidationError("Video ID cannot be empty or only whitespace")
        
        if len(id) > 100:
            raise ValidationError("Video ID cannot exceed 100 characters")
        
        return id
    
    def _validate_type(self, type: str) -> str:
        """Validate video type"""
        if not type or type not in self.VALID_TYPES:
            raise ValidationError(f"Video type must be one of: {', '.join(self.VALID_TYPES)}")
        
        return type
    
    def _validate_status(self, status: str) -> str:
        """Validate video status"""
        if not status or status not in self.VALID_STATUSES:
            raise ValidationError(f"Video status must be one of: {', '.join(self.VALID_STATUSES)}")
        
        return status
    
    def update_status(self, new_status: str) -> None:
        """Update video status with validation"""
        self.status = self._validate_status(new_status)
        self.updated_at = datetime.now().isoformat()
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage based on current status"""
        try:
            status_index = self.VALID_STATUSES.index(self.status)
            return ((status_index + 1) / len(self.VALID_STATUSES)) * 100
        except ValueError:
            return 0.0
    
    def is_completed(self) -> bool:
        """Check if video is completed"""
        return self.status == 'Final'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VideoModel':
        """Create instance from dictionary"""
        return cls(
            id=data['id'],
            type=data['type'],
            status=data.get('status', 'Script'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __str__(self) -> str:
        return f"Video(id={self.id}, type={self.type}, status={self.status})"
    
    def __repr__(self) -> str:
        return self.__str__()

class CostModel:
    """Cost entry data model with validation"""
    
    VALID_TYPES = ['Tool', 'Freelancer', 'Other']
    VALID_CURRENCIES = ['USD', 'PKR']
    
    def __init__(self, id: Optional[int] = None, type: str = '', amount: float = 0.0, 
                 currency: str = 'USD', notes: str = '', created_at: Optional[str] = None):
        self.id = id
        self.type = self._validate_type(type)
        self.amount = self._validate_amount(amount)
        self.currency = self._validate_currency(currency)
        self.notes = self._validate_notes(notes)
        self.created_at = created_at or datetime.now().isoformat()
    
    def _validate_type(self, type: str) -> str:
        """Validate cost type"""
        if not type or type not in self.VALID_TYPES:
            raise ValidationError(f"Cost type must be one of: {', '.join(self.VALID_TYPES)}")
        
        return type
    
    def _validate_amount(self, amount: Union[float, int, str]) -> float:
        """Validate cost amount"""
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValidationError("Cost amount must be a valid number")
        
        if amount < 0:
            raise ValidationError("Cost amount cannot be negative")
        
        if amount > 1000000:  # Reasonable upper limit
            raise ValidationError("Cost amount cannot exceed 1,000,000")
        
        return round(amount, 2)
    
    def _validate_currency(self, currency: str) -> str:
        """Validate currency"""
        if not currency or currency not in self.VALID_CURRENCIES:
            raise ValidationError(f"Currency must be one of: {', '.join(self.VALID_CURRENCIES)}")
        
        return currency
    
    def _validate_notes(self, notes: str) -> str:
        """Validate notes"""
        if not isinstance(notes, str):
            notes = str(notes) if notes else ''
        
        # Limit notes length
        if len(notes) > 500:
            raise ValidationError("Notes cannot exceed 500 characters")
        
        return notes.strip()
    
    def get_formatted_amount(self) -> str:
        """Get formatted amount with currency symbol"""
        if self.currency == 'USD':
            return f"${self.amount:.2f}"
        elif self.currency == 'PKR':
            return f"₨{self.amount:.2f}"
        else:
            return f"{self.amount:.2f} {self.currency}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'type': self.type,
            'amount': self.amount,
            'currency': self.currency,
            'notes': self.notes,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CostModel':
        """Create instance from dictionary"""
        return cls(
            id=data.get('id'),
            type=data['type'],
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            notes=data.get('notes', ''),
            created_at=data.get('created_at')
        )
    
    def __str__(self) -> str:
        return f"Cost(id={self.id}, type={self.type}, amount={self.get_formatted_amount()})"
    
    def __repr__(self) -> str:
        return self.__str__()

class ProjectStats:
    """Project statistics calculator"""
    
    def __init__(self, videos: List[VideoModel], costs: List[CostModel], budget: float = 0.0):
        self.videos = videos
        self.costs = costs
        self.budget = budget
    
    def get_total_videos(self) -> int:
        """Get total number of videos"""
        return len(self.videos)
    
    def get_completed_videos(self) -> int:
        """Get number of completed videos"""
        return len([v for v in self.videos if v.is_completed()])
    
    def get_pending_videos(self) -> int:
        """Get number of pending videos"""
        return self.get_total_videos() - self.get_completed_videos()
    
    def get_completion_rate(self) -> float:
        """Get completion rate as percentage"""
        total = self.get_total_videos()
        if total == 0:
            return 0.0
        return (self.get_completed_videos() / total) * 100
    
    def get_status_distribution(self) -> Dict[str, int]:
        """Get distribution of videos by status"""
        distribution = {status: 0 for status in VideoModel.VALID_STATUSES}
        for video in self.videos:
            distribution[video.status] += 1
        return distribution
    
    def get_type_distribution(self) -> Dict[str, int]:
        """Get distribution of videos by type"""
        distribution = {type: 0 for type in VideoModel.VALID_TYPES}
        for video in self.videos:
            distribution[video.type] += 1
        return distribution
    
    def get_total_costs_by_currency(self) -> Dict[str, float]:
        """Get total costs grouped by currency"""
        totals = {}
        for cost in self.costs:
            if cost.currency not in totals:
                totals[cost.currency] = 0.0
            totals[cost.currency] += cost.amount
        return totals
    
    def get_cost_distribution_by_type(self) -> Dict[str, float]:
        """Get cost distribution by type (USD only for consistency)"""
        distribution = {type: 0.0 for type in CostModel.VALID_TYPES}
        for cost in self.costs:
            if cost.currency == 'USD':  # Only count USD for distribution
                distribution[cost.type] += cost.amount
        return distribution
    
    def get_budget_status(self) -> Dict[str, Union[float, bool]]:
        """Get budget status information"""
        usd_spent = sum(c.amount for c in self.costs if c.currency == 'USD')
        remaining = self.budget - usd_spent
        
        return {
            'budget': self.budget,
            'spent': usd_spent,
            'remaining': remaining,
            'percentage_used': (usd_spent / self.budget * 100) if self.budget > 0 else 0,
            'over_budget': remaining < 0,
            'near_budget': remaining < (self.budget * 0.1) if self.budget > 0 else False
        }
    
    def get_average_cost_per_video(self) -> Dict[str, float]:
        """Get average cost per video by currency"""
        total_videos = self.get_total_videos()
        if total_videos == 0:
            return {'USD': 0.0, 'PKR': 0.0}
        
        cost_totals = self.get_total_costs_by_currency()
        return {
            'USD': cost_totals.get('USD', 0.0) / total_videos,
            'PKR': cost_totals.get('PKR', 0.0) / total_videos
        }
    
    def get_recent_activity(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """Get recent videos and costs"""
        # Sort videos by created_at (most recent first)
        recent_videos = sorted(self.videos, 
                             key=lambda v: v.created_at or '', 
                             reverse=True)[:limit]
        
        # Sort costs by created_at (most recent first)
        recent_costs = sorted(self.costs, 
                            key=lambda c: c.created_at or '', 
                            reverse=True)[:limit]
        
        return {
            'videos': [v.to_dict() for v in recent_videos],
            'costs': [c.to_dict() for c in recent_costs]
        }
    
    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        return {
            'total_videos': self.get_total_videos(),
            'completed_videos': self.get_completed_videos(),
            'pending_videos': self.get_pending_videos(),
            'completion_rate': self.get_completion_rate(),
            'status_distribution': self.get_status_distribution(),
            'type_distribution': self.get_type_distribution(),
            'total_costs_by_currency': self.get_total_costs_by_currency(),
            'cost_distribution_by_type': self.get_cost_distribution_by_type(),
            'budget_status': self.get_budget_status(),
            'average_cost_per_video': self.get_average_cost_per_video()
        }

class DataManager:
    """Data manager for handling video and cost operations"""
    
    def __init__(self, db_instance):
        self.db = db_instance
    
    def get_videos(self) -> List[VideoModel]:
        """Get all videos from database"""
        try:
            videos_data = self.db.get('videos', '[]')
            if isinstance(videos_data, str):
                videos_data = json.loads(videos_data)
            
            videos = []
            for video_dict in videos_data:
                try:
                    video = VideoModel.from_dict(video_dict)
                    videos.append(video)
                except ValidationError as e:
                    logger.error(f"Invalid video data: {e}")
                    continue
            
            return videos
        except Exception as e:
            logger.error(f"Error loading videos: {e}")
            return []
    
    def save_videos(self, videos: List[VideoModel]) -> bool:
        """Save videos to database"""
        try:
            videos_data = [video.to_dict() for video in videos]
            self.db['videos'] = json.dumps(videos_data)
            return True
        except Exception as e:
            logger.error(f"Error saving videos: {e}")
            return False
    
    def add_video(self, video: VideoModel) -> bool:
        """Add a new video"""
        try:
            videos = self.get_videos()
            
            # Check for duplicate ID
            if any(v.id == video.id for v in videos):
                raise ValidationError(f"Video with ID '{video.id}' already exists")
            
            videos.append(video)
            return self.save_videos(videos)
        except Exception as e:
            logger.error(f"Error adding video: {e}")
            return False
    
    def update_video(self, video_id: str, **kwargs) -> bool:
        """Update a video"""
        try:
            videos = self.get_videos()
            
            for video in videos:
                if video.id == video_id:
                    if 'status' in kwargs:
                        video.update_status(kwargs['status'])
                    if 'type' in kwargs:
                        video.type = video._validate_type(kwargs['type'])
                        video.updated_at = datetime.now().isoformat()
                    
                    return self.save_videos(videos)
            
            return False  # Video not found
        except Exception as e:
            logger.error(f"Error updating video: {e}")
            return False
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video"""
        try:
            videos = self.get_videos()
            original_count = len(videos)
            videos = [v for v in videos if v.id != video_id]
            
            if len(videos) < original_count:
                return self.save_videos(videos)
            
            return False  # Video not found
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            return False
    
    def get_costs(self) -> List[CostModel]:
        """Get all costs from database"""
        try:
            costs_data = self.db.get('costs', '[]')
            if isinstance(costs_data, str):
                costs_data = json.loads(costs_data)
            
            costs = []
            for cost_dict in costs_data:
                try:
                    cost = CostModel.from_dict(cost_dict)
                    costs.append(cost)
                except ValidationError as e:
                    logger.error(f"Invalid cost data: {e}")
                    continue
            
            return costs
        except Exception as e:
            logger.error(f"Error loading costs: {e}")
            return []
    
    def save_costs(self, costs: List[CostModel]) -> bool:
        """Save costs to database"""
        try:
            costs_data = [cost.to_dict() for cost in costs]
            self.db['costs'] = json.dumps(costs_data)
            return True
        except Exception as e:
            logger.error(f"Error saving costs: {e}")
            return False
    
    def add_cost(self, cost: CostModel) -> bool:
        """Add a new cost"""
        try:
            costs = self.get_costs()
            
            # Generate ID if not provided
            if cost.id is None:
                max_id = max([c.id for c in costs if c.id is not None], default=0)
                cost.id = max_id + 1
            
            costs.append(cost)
            return self.save_costs(costs)
        except Exception as e:
            logger.error(f"Error adding cost: {e}")
            return False
    
    def delete_cost(self, cost_id: int) -> bool:
        """Delete a cost"""
        try:
            costs = self.get_costs()
            original_count = len(costs)
            costs = [c for c in costs if c.id != cost_id]
            
            if len(costs) < original_count:
                return self.save_costs(costs)
            
            return False  # Cost not found
        except Exception as e:
            logger.error(f"Error deleting cost: {e}")
            return False
    
    def get_budget(self) -> float:
        """Get budget from database"""
        try:
            return float(self.db.get('budget', 0))
        except Exception as e:
            logger.error(f"Error loading budget: {e}")
            return 0.0
    
    def set_budget(self, budget: float) -> bool:
        """Set budget in database"""
        try:
            if budget < 0:
                raise ValidationError("Budget cannot be negative")
            
            self.db['budget'] = str(budget)
            return True
        except Exception as e:
            logger.error(f"Error setting budget: {e}")
            return False
    
    def get_project_stats(self) -> ProjectStats:
        """Get project statistics"""
        videos = self.get_videos()
        costs = self.get_costs()
        budget = self.get_budget()
        
        return ProjectStats(videos, costs, budget)
    
    def export_data(self) -> Dict:
        """Export all data"""
        return {
            'videos': [v.to_dict() for v in self.get_videos()],
            'costs': [c.to_dict() for c in self.get_costs()],
            'budget': self.get_budget(),
            'export_date': datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict) -> bool:
        """Import data (with validation)"""
        try:
            # Validate and import videos
            if 'videos' in data:
                videos = []
                for video_dict in data['videos']:
                    video = VideoModel.from_dict(video_dict)
                    videos.append(video)
                self.save_videos(videos)
            
            # Validate and import costs
            if 'costs' in data:
                costs = []
                for cost_dict in data['costs']:
                    cost = CostModel.from_dict(cost_dict)
                    costs.append(cost)
                self.save_costs(costs)
            
            # Import budget
            if 'budget' in data:
                self.set_budget(float(data['budget']))
            
            return True
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
