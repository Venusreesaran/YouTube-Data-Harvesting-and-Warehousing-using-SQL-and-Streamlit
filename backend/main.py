from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from crud_apis import * #ChannelResource, VideoResource, CommentResource
from config import app_config
from  database import db
from models import *
# Initialize the Flask app
app = Flask(__name__)

# Configure the SQLite database
app.config.from_object(app_config)

# Initialize database and API
db.init_app(app)
api = Api(app)

# Import models to create tables
from models import Channel, Video, Comment

# Register the API resources
api.add_resource(test,"/test")
api.add_resource(ChannelInfo, '/api/channel')                  # Fetch channel information
api.add_resource(VideoInfo, '/api/videos')                     # Fetch video details
api.add_resource(VideoComments, '/api/comments')               # Fetch video comments
api.add_resource(SaveAll, '/api/save_all')                     # Save all data (channel, videos, comments)
api.add_resource(FetchVideoDetails, '/api/video_details')      # Fetch video details, channel info, and comments
api.add_resource(SaveVideoDetails, '/api/save_video')          # Save video details, channel info, and comments
api.add_resource(ChannelDetailsFromDB, '/api/db/channel')      # Fetch channel details from database
api.add_resource(VideoDetailsFromDB, '/api/db/videos')          # Fetch video details from database
api.add_resource(VideoCommentsFromDB, '/api/db/comments')      # Fetch comments from database
api.add_resource(VideoDetailsFromPlaylist,'/api/videos_from_playlist')
api.add_resource(AnalyticsResource, '/analytics')

# # Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)