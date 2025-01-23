from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os

# Import db and ma from extensions
from extensions import db, ma

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['VIDEO_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB file size limit

# Ensure upload directories exist
os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
ma.init_app(app)

# Import models after initializing db
from models import Video

# Video schema for serialization
class VideoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Video

video_schema = VideoSchema()
videos_schema = VideoSchema(many=True)

# Routes
@app.route('/videos', methods=['GET'])
def get_videos():
    """Fetch all videos."""
    videos = Video.query.all()
    return videos_schema.jsonify(videos)

@app.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Fetch a specific video by ID."""
    video = Video.query.get_or_404(video_id)
    return video_schema.jsonify(video)

@app.route('/videos', methods=['POST'])
def add_video():
    """Add a new video."""
    try:
        title = request.form.get('title')
        video_file = request.files.get('file')

        # Validate input
        if not title or not video_file:
            return jsonify({'error': 'Title and video file are required.'}), 400

        # Validate file type (optional, e.g., only allow .mp4, .mov)
        allowed_extensions = {'mp4', 'mov', 'avi'}
        file_extension = video_file.filename.rsplit('.', 1)[-1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Allowed types are mp4, mov, avi.'}), 400

        # Save the video file
        video_filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['VIDEO_FOLDER'], video_filename)
        video_file.save(video_path)

        # Create a new video entry in the database
        new_video = Video(
            title=title,
            url=f'/videos/{video_filename}'  # Dynamic path to serve the video
        )
        db.session.add(new_video)
        db.session.commit()

        return video_schema.jsonify(new_video), 201
    except Exception as e:
        app.logger.error(f"Error adding video: {str(e)}")
        return jsonify({'error': 'An error occurred while adding the video.'}), 500

@app.route('/videos/<filename>', methods=['GET'])
def serve_video(filename):
    """Serve video files dynamically."""
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large. Maximum size is 50MB.'}), 413

# Enable CORS
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

# Run the Flask server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
