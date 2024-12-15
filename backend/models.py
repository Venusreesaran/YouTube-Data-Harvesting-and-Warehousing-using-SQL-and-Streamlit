from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Channel Model
class Channel(db.Model):
    __tablename__ = 'channel'
    
    channel_id = db.Column(db.String(255), primary_key=True)
    channel_name = db.Column(db.String(255), nullable=False)
    channel_description = db.Column(db.Text, nullable=True)
    subscribers = db.Column(db.Integer, nullable=False, default=0)
    total_videos = db.Column(db.Integer, nullable=False, default=0)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    playlist_id = db.Column(db.String(255), nullable=True)
    # channel_status = db.Column(db.String(255), nullable=True)  # Channel status (e.g., 'active', 'suspended')

    # Relationship with video
    videos = db.relationship('Video', back_populates='channel', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Channel(channel_id={self.channel_id}, channel_name={self.channel_name})>"

# Video Model
class Video(db.Model):
    __tablename__ = 'video'
    
    video_id = db.Column(db.String(255), primary_key=True)
    channel_id = db.Column(db.String(255), db.ForeignKey('channel.channel_id', ondelete='CASCADE'), nullable=False)
    playlist_id = db.Column(db.String(255), nullable=True)  # Assuming this references another table
    video_name = db.Column(db.String(255), nullable=False)
    video_description = db.Column(db.Text, nullable=True)
    published_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    dislike_count = db.Column(db.Integer, nullable=False, default=0)
    favorite_count = db.Column(db.Integer, nullable=False, default=0)  # New field for favorite count
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    duration = db.Column(db.Integer, nullable=False, default=0)  # Duration in seconds
    thumbnail = db.Column(db.String(255), nullable=True)  # Thumbnail URL or path
    caption_status = db.Column(db.String(255), nullable=True)  # New field for caption status (e.g., 'available', 'not available')

    # Relationship with channel
    channel = db.relationship('Channel', back_populates='videos')

    def __repr__(self):
        return f"<Video(video_id={self.video_id}, video_name={self.video_name})>"

# Comment Model
class Comment(db.Model):
    __tablename__ = 'comment'
    
    comment_id = db.Column(db.String(255), primary_key=True)
    video_id = db.Column(db.String(255), db.ForeignKey('video.video_id', ondelete='CASCADE'), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, nullable=False, default=0)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship with video
    video = db.relationship('Video', backref=db.backref('comments', lazy=True))

    def __repr__(self):
        return f"<Comment(comment_id={self.comment_id}, author={self.author})>"

# Example to create the database tables (e.g., in an application startup):
# db.create_all()  # Run this in the Flask app context after setting up the database URI

