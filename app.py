from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['VIDEO_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB file size limit

# Ensure upload directories exist
os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

# Initialize extensions with app
db.init_app(app)
ma.init_app(app)
migrate.init_app(app, db)

# Enable CORS
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

# Models
class Video(db.Model):
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


# Schemas
class VideoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Video


video_schema = VideoSchema()
videos_schema = VideoSchema(many=True)

# Routes
@app.route('/videos', methods=['GET'])
def get_videos():
    videos = Video.query.all()
    return videos_schema.jsonify(videos)


@app.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    video = Video.query.get_or_404(video_id)
    return video_schema.jsonify(video)


@app.route('/videos', methods=['POST'])
def add_video():
    try:
        title = request.form.get('title')
        video_file = request.files.get('file')

        if not title or not video_file:
            return jsonify({'error': 'Title and video file are required.'}), 400

        allowed_extensions = {'mp4', 'mov', 'avi'}
        file_extension = video_file.filename.rsplit('.', 1)[-1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Allowed types are mp4, mov, avi.'}), 400

        video_filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['VIDEO_FOLDER'], video_filename)
        video_file.save(video_path)

        new_video = Video(title=title, url=f'/videos/{video_filename}')
        db.session.add(new_video)
        db.session.commit()

        return video_schema.jsonify(new_video), 201
    except Exception as e:
        app.logger.error(f"Error adding video: {str(e)}")
        return jsonify({'error': 'An error occurred while adding the video.'}), 500


@app.route('/videos/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    try:
        video = Video.query.get_or_404(video_id)
        video_file_path = os.path.join(app.config['VIDEO_FOLDER'], os.path.basename(video.url))
        if os.path.exists(video_file_path):
            os.remove(video_file_path)

        db.session.delete(video)
        db.session.commit()

        return jsonify({'message': f'Video with ID {video_id} deleted successfully.'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting video: {str(e)}")
        return jsonify({'error': 'An error occurred while deleting the video.'}), 500


@app.route('/videos/<filename>', methods=['GET'])
def serve_video(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@app.route('/favorites', methods=['GET'])
def get_favorites():
    favorites = Favorite.query.all()
    favorite_videos = [favorite.video for favorite in favorites]
    return videos_schema.jsonify(favorite_videos)


@app.route('/favorites', methods=['POST'])
def add_favorite():
    try:
        video_id = request.json.get('video_id')
        video = Video.query.get_or_404(video_id)

        existing_favorite = Favorite.query.filter_by(video_id=video_id).first()
        if existing_favorite:
            return jsonify({'error': 'Video is already in favorites.'}), 400

        favorite = Favorite(video_id=video_id)
        db.session.add(favorite)
        db.session.commit()

        return jsonify({'message': 'Video added to favorites!'}), 201
    except Exception as e:
        app.logger.error(f"Error adding favorite: {str(e)}")
        return jsonify({'error': 'Failed to add favorite.'}), 500


@app.route('/favorites/<int:video_id>', methods=['DELETE'])
def remove_favorite(video_id):
    try:
        favorite = Favorite.query.filter_by(video_id=video_id).first()
        if not favorite:
            return jsonify({'error': 'Video not found in favorites.'}), 404

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({'message': 'Video removed from favorites.'}), 200
    except Exception as e:
        app.logger.error(f"Error removing favorite: {str(e)}")
        return jsonify({'error': 'Failed to remove favorite.'}), 500


# Error Handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large. Maximum size is 50MB.'}), 413


# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
