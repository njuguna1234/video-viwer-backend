from extensions import db

class Video(db.Model):
    """Model for storing video metadata."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Video {self.title}>'
