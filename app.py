import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from database import db, Video, Cost, Settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# configure the database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Fallback to SQLite for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///video_tracker.db"

# initialize the app with the extension
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Video status options
VIDEO_STATUSES = Video.VALID_STATUSES
VIDEO_TYPES = Video.VALID_TYPES
COST_TYPES = Cost.VALID_TYPES
CURRENCIES = Cost.VALID_CURRENCIES

def get_videos():
    """Get all videos from database"""
    try:
        videos = Video.query.all()
        return videos
    except Exception as e:
        logging.error(f"Error getting videos: {e}")
        return []

def get_costs():
    """Get all costs from database"""
    try:
        costs = Cost.query.all()
        return costs
    except Exception as e:
        logging.error(f"Error getting costs: {e}")
        return []

def get_budget():
    """Get budget from database"""
    try:
        setting = Settings.query.filter_by(key='budget').first()
        return float(setting.value) if setting else 0.0
    except Exception as e:
        logging.error(f"Error getting budget: {e}")
        return 0.0

def save_budget(budget):
    """Save budget to database"""
    try:
        setting = Settings.query.filter_by(key='budget').first()
        if setting:
            setting.value = str(budget)
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key='budget', value=str(budget))
            db.session.add(setting)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error saving budget: {e}")
        db.session.rollback()

@app.route('/')
def index():
    """Dashboard view"""
    videos = get_videos()
    costs = get_costs()
    budget = get_budget()
    
    # Calculate metrics
    total_videos = len(videos)
    completed_videos = len([v for v in videos if v.status == 'Final'])
    pending_videos = total_videos - completed_videos
    
    # Calculate costs by currency
    total_costs_usd = sum(c.amount for c in costs if c.currency == 'USD')
    total_costs_pkr = sum(c.amount for c in costs if c.currency == 'PKR')
    
    # Status distribution - handle both regular and testimonial statuses
    status_counts = {}
    all_statuses = set(VIDEO_STATUSES + Video.TESTIMONIAL_STATUSES)
    for status in all_statuses:
        status_counts[status] = len([v for v in videos if v.status == status])
    
    # Type distribution
    type_counts = {}
    for vtype in VIDEO_TYPES:
        type_counts[vtype] = len([v for v in videos if v.type == vtype])
    
    return render_template('index.html', 
                         videos=videos,
                         costs=costs,
                         budget=budget,
                         total_videos=total_videos,
                         completed_videos=completed_videos,
                         pending_videos=pending_videos,
                         total_costs_usd=total_costs_usd,
                         total_costs_pkr=total_costs_pkr,
                         status_counts=status_counts,
                         type_counts=type_counts)

@app.route('/videos')
def videos():
    """Videos management view"""
    videos = get_videos()
    return render_template('videos.html', videos=videos, 
                         video_statuses=VIDEO_STATUSES,
                         video_types=VIDEO_TYPES)

@app.route('/add_video', methods=['POST'])
def add_video():
    """Add new video"""
    try:
        video_id = request.form.get('video_id', '').strip()
        video_type = request.form.get('video_type', '')
        status = request.form.get('status', 'Conceptualization & Script')
        
        if not video_id or not video_type:
            flash('Video ID and Type are required', 'error')
            return redirect(url_for('videos'))
        
        # Check if video ID already exists
        existing_video = Video.query.filter_by(id=video_id).first()
        if existing_video:
            flash('Video ID already exists', 'error')
            return redirect(url_for('videos'))
        
        # Validate inputs
        if video_type not in VIDEO_TYPES:
            flash('Invalid video type', 'error')
            return redirect(url_for('videos'))
        
        # Validate status based on video type
        if video_type == 'Testimonial':
            valid_statuses = Video.TESTIMONIAL_STATUSES
        else:
            valid_statuses = VIDEO_STATUSES
        
        if status not in valid_statuses:
            flash('Invalid video status', 'error')
            return redirect(url_for('videos'))
        
        new_video = Video(id=video_id, type=video_type, status=status)
        db.session.add(new_video)
        db.session.commit()
        
        flash('Video added successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error adding video: {e}")
        flash('Error adding video', 'error')
        db.session.rollback()
    
    return redirect(url_for('videos'))

@app.route('/update_video_status', methods=['POST'])
def update_video_status():
    """Update video status"""
    try:
        video_id = request.form.get('video_id')
        new_status = request.form.get('status')
        
        if not video_id or not new_status:
            flash('Invalid request', 'error')
            return redirect(url_for('videos'))
        
        video = Video.query.filter_by(id=video_id).first()
        if not video:
            flash('Video not found', 'error')
            return redirect(url_for('videos'))
        
        # Validate status based on video type
        if video.type == 'Testimonial':
            valid_statuses = Video.TESTIMONIAL_STATUSES
        else:
            valid_statuses = VIDEO_STATUSES
        
        if new_status not in valid_statuses:
            flash('Invalid video status', 'error')
            return redirect(url_for('videos'))
        
        video.status = new_status
        video.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Video status updated successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error updating video status: {e}")
        flash('Error updating video status', 'error')
        db.session.rollback()
    
    return redirect(url_for('videos'))

@app.route('/delete_video', methods=['POST'])
def delete_video():
    """Delete video"""
    try:
        video_id = request.form.get('video_id')
        
        if not video_id:
            flash('Invalid request', 'error')
            return redirect(url_for('videos'))
        
        video = Video.query.filter_by(id=video_id).first()
        if not video:
            flash('Video not found', 'error')
            return redirect(url_for('videos'))
        
        db.session.delete(video)
        db.session.commit()
        
        flash('Video deleted successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error deleting video: {e}")
        flash('Error deleting video', 'error')
        db.session.rollback()
    
    return redirect(url_for('videos'))

@app.route('/costs')
def costs():
    """Costs management view"""
    costs = get_costs()
    budget = get_budget()
    
    # Calculate totals by currency
    total_usd = sum(c.amount for c in costs if c.currency == 'USD')
    total_pkr = sum(c.amount for c in costs if c.currency == 'PKR')
    
    return render_template('costs.html', 
                         costs=costs,
                         budget=budget,
                         total_usd=total_usd,
                         total_pkr=total_pkr,
                         cost_types=COST_TYPES,
                         currencies=CURRENCIES)

@app.route('/add_cost', methods=['POST'])
def add_cost():
    """Add new cost entry"""
    try:
        cost_type = request.form.get('cost_type', '')
        cost_name = request.form.get('cost_name', '').strip()
        amount = float(request.form.get('amount', 0))
        currency = request.form.get('currency', 'USD')
        notes = request.form.get('notes', '').strip()
        
        if not cost_type or amount <= 0:
            flash('Cost type and valid amount are required', 'error')
            return redirect(url_for('costs'))
        
        if cost_type not in COST_TYPES:
            flash('Invalid cost type', 'error')
            return redirect(url_for('costs'))
        
        if currency not in CURRENCIES:
            flash('Invalid currency', 'error')
            return redirect(url_for('costs'))
        
        # Name is required for Tool and Freelancer types
        if cost_type in ['Tool', 'Freelancer'] and not cost_name:
            flash(f'Name is required for {cost_type} type', 'error')
            return redirect(url_for('costs'))
        
        new_cost = Cost(
            type=cost_type,
            name=cost_name if cost_type in ['Tool', 'Freelancer'] else None,
            amount=amount,
            currency=currency,
            notes=notes
        )
        
        db.session.add(new_cost)
        db.session.commit()
        
        flash('Cost entry added successfully', 'success')
        
    except ValueError:
        flash('Invalid amount entered', 'error')
    except Exception as e:
        logging.error(f"Error adding cost: {e}")
        flash('Error adding cost entry', 'error')
        db.session.rollback()
    
    return redirect(url_for('costs'))

@app.route('/delete_cost', methods=['POST'])
def delete_cost():
    """Delete cost entry"""
    try:
        cost_id = int(request.form.get('cost_id'))
        
        cost = Cost.query.filter_by(id=cost_id).first()
        if not cost:
            flash('Cost entry not found', 'error')
            return redirect(url_for('costs'))
        
        db.session.delete(cost)
        db.session.commit()
        
        flash('Cost entry deleted successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error deleting cost: {e}")
        flash('Error deleting cost entry', 'error')
        db.session.rollback()
    
    return redirect(url_for('costs'))

@app.route('/update_budget', methods=['POST'])
def update_budget():
    """Update budget"""
    try:
        budget = float(request.form.get('budget', 0))
        
        if budget < 0:
            flash('Budget cannot be negative', 'error')
            return redirect(url_for('costs'))
        
        save_budget(budget)
        flash('Budget updated successfully', 'success')
        
    except ValueError:
        flash('Invalid budget amount', 'error')
    except Exception as e:
        logging.error(f"Error updating budget: {e}")
        flash('Error updating budget', 'error')
    
    return redirect(url_for('costs'))

@app.route('/api/dashboard_data')
def api_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        videos = get_videos()
        costs = get_costs()
        
        # Status distribution
        status_counts = {}
        for status in VIDEO_STATUSES:
            status_counts[status] = len([v for v in videos if v.get('status') == status])
        
        # Type distribution
        type_counts = {}
        for vtype in VIDEO_TYPES:
            type_counts[vtype] = len([v for v in videos if v.get('type') == vtype])
        
        return jsonify({
            'status_counts': status_counts,
            'type_counts': type_counts,
            'total_videos': len(videos),
            'completed_videos': len([v for v in videos if v.get('status') == 'Final'])
        })
    
    except Exception as e:
        logging.error(f"Error fetching dashboard data: {e}")
        return jsonify({'error': 'Failed to fetch data'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
