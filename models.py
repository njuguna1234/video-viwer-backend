from extensions import db

class Video(db.Model):
    """Model for storing video metadata."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Video {self.title}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

    # Relationship for easier access to video details
    video = db.relationship('Video', backref='favorites')