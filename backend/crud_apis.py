from datetime import datetime
from flask import jsonify, request, session
from flask_restful import Resource, reqparse
from models import db, Channel, Video, Comment
from youtube_apis import YouTubeDataFetcher


# Initialize your YouTube API fetcher with an API key
API_KEY = "AIzaSyB3mMdqAykqnxOU0Zp8MLD8T3CXIwGlD0M"  # Replace with your API key
yt_fetcher = YouTubeDataFetcher(API_KEY)




class test(Resource):
    def get(self):
        return {"message":"Welcome to yt_archives"},200


class ChannelInfo(Resource):
    def get(self):
        """
        Endpoint to fetch channel info and video IDs by channel ID.
        """
        # Get the channel ID from query parameters
        channel_id = request.args.get('channel_id')
        
        if not channel_id:
            return {"error": "Channel ID is required."}, 400
        
        try:
            # Fetch channel information
            channel_info = yt_fetcher.get_channel_stats(channel_id)
            if not channel_info:
                return {"error": "Invalid channel ID or no data found."}, 404
            
            # Fetch video IDs from the channel's uploads playlist
            video_ids = yt_fetcher.get_video_ids(channel_info['playlist_id'])
            if not video_ids:
                return {
                    "channel_info": channel_info,
                    "video_ids": [],
                    "message": "No videos found for this channel."
                }, 200
            
            # Return combined data
            return {
                "channel_info": channel_info,
                "video_ids": video_ids
            }, 200
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500

class VideoInfo(Resource):
    def get(self):
        """
        Endpoint to fetch video details by a list of video IDs.
        """
        # Get the video IDs from query parameters (comma-separated)
        video_ids = request.args.get('video_ids')
        
        if not video_ids:
            return {"error": "Video IDs are required."}, 400
        
        video_ids = video_ids.split(",")  # Convert the comma-separated string to a list
        
        try:
            # Fetch video details
            videos = yt_fetcher.get_video_details(video_ids)
            if not videos:
                return {"error": "No valid videos found."}, 404
            
            # Return video data in a nicely formatted JSON
            return {"videos": videos}, 200
        
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500

class VideoComments(Resource):
    def get(self):
        """
        Endpoint to fetch comments for a list of video IDs.
        """
        # Get the video IDs from query parameters (comma-separated)
        video_ids = request.args.get('video_ids')
        
        if not video_ids:
            return {"error": "Video IDs are required."}, 400
        
        video_ids = video_ids.split(",")  # Convert the comma-separated string to a list
        
        try:
            all_comments = []
            
            # Fetch comments for each video
            for video_id in video_ids:
                comments = yt_fetcher.get_video_comments(video_id)
                if comments:
                    for comment in comments:
                        comment['video_id'] = video_id  # Add video_id to each comment
                    all_comments.extend(comments)  # Add to the main comment list
            
            if not all_comments:
                return {"error": "No valid comments found for these videos."}, 404
            
            # Return the comments in a nicely formatted JSON
            return {"comments": all_comments}, 200
        
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500
        
class SaveAll(Resource):
    def post(self):
        """
        Endpoint to save all data (channel, videos, comments) into the database.
        """
        channel_id = request.args.get('channel_id')
        if not channel_id:
            return {"error": "Channel ID is required."}, 400

        try:
            # Fetch all data from YouTube
            data = yt_fetcher.fetch_all_data(channel_id)
            if not data:
                return {"error": "Invalid channel ID or no data found."}, 404

            # Clean and transform channel data to match model
            channel_info = data['channel_info']
            print("hlooo")
            cleaned_channel_info = {
                'channel_id': channel_id,
                'channel_name': channel_info['channel_name'],
                'channel_description': channel_info['channel_description'],
                'subscribers': int(channel_info['subscribers']) if channel_info['subscribers'].isdigit() else 0,
                'total_videos': int(channel_info['total_videos']) if channel_info['total_videos'].isdigit() else 0,
                'view_count': int(channel_info['view_count']) if channel_info['view_count'].isdigit() else 0,
                'playlist_id': channel_info['playlist_id']
            }
            # print(cleaned_channel_info)
            # Save channel data
            channel = db.session.query(Channel).filter_by(channel_id=channel_id).first()
            if not channel:
                channel = Channel(**cleaned_channel_info)
                print("here")
                db.session.add(channel)
            else:
                for attr, value in cleaned_channel_info.items():
                    setattr(channel, attr, value)

            # Save videos and comments
            # print(data['videos'])
            try:
                for video_data in data['videos']:
                    if "playlist_id" not in video_data:

                        video_data["playlist_id"]=""
                    Comments = video_data.pop("comments")
                    video_data["published_date"]=datetime.strptime(video_data["published_date"],'%Y-%m-%d')
                    video_record = db.session.query(Video).filter_by(video_id=video_data['video_id']).first()
                    print(video_data)
                    if not video_record:
                        video_record = Video(**video_data)
                        # print("heere2")
                        db.session.add(video_record)
                        # print("bruhh")
                    else:
                        for attr, value in video_data.items():
                            setattr(video_record, attr, value)

                    # Save comments
                    for comment_data in Comments:# video_data.get('comments', []):
                        comment_data["published_at"]=datetime.strptime(comment_data["published_at"],'%Y-%m-%d')
                        comment_record = db.session.query(Comment).filter_by(comment_id=comment_data['comment_id']).first()######
                        if not comment_record:
                            db.session.add(Comment(**comment_data))
                            print("333")
            except Exception as e:  # Catch any exception
                print(f"An error occurred: {e}")


            db.session.commit()
            return {"message": "Data saved successfully."}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"An error occurred: {str(e)}"}, 50000

class FetchVideoDetails(Resource):
    def get(self):
        """
        Fetch channel details and comments for a given video ID.
        """
        video_id = request.args.get('video_id')
        if not video_id:
            return {"error": "Video ID is required."}, 400

        try:
            # Fetch video details from the YouTube API
            video_details = yt_fetcher.get_video_details([video_id])
            if not video_details:
                return {"error": "Invalid video ID or no data found."}, 404

            video_data = video_details[0]
            channel_data = yt_fetcher.get_channel_stats(video_data['channel_id'])
            comments = yt_fetcher.get_video_comments(video_id)
            channel_data["channel_id"]=video_data["channel_id"]
            return {
                "video_details": video_data,
                "channel_info": channel_data,
                "comments": comments,
            }, 200
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500


class SaveVideoDetails(Resource):
    def post(self):
        """
        Save video details, its channel info, and comments to the database.
        """
        video_id = request.json.get('video_id')  # Expecting JSON payload
        if not video_id:
            return {"error": "Video ID is required."}, 400

        try:
            # Fetch video details
            video_details = yt_fetcher.get_video_details([video_id])

            if not video_details:
                return {"error": "Invalid video ID or no data found."}, 404
            
            video_data = video_details[0]
            if "playlist_id" not in video_data:
                video_data["playlist_id"]=""
                # Comments = video_data.pop("comments")
            video_data["published_date"]=datetime.strptime(video_data["published_date"],'%Y-%m-%d')
                    
            # print(video_details)
            # Fetch channel data
            channel_data = yt_fetcher.get_channel_stats(video_data['channel_id'])
            comments = yt_fetcher.get_video_comments(video_id)

            # Save channel data
            channel = db.session.query(Channel).filter_by(channel_id=video_data['channel_id']).first()
            if not channel:
                print(channel_data)
                channel_data.pop('channel_type')
                channel_data["channel_id"]=video_data["channel_id"]
                channel = Channel(**channel_data)
                db.session.add(channel)
            else:
                for attr, value in channel_data.items():
                    setattr(channel, attr, value)

            # Save video data
            video_record = db.session.query(Video).filter_by(video_id=video_id).first()
            if not video_record:
                db.session.add(Video(**video_data))
            else:
                for attr, value in video_data.items():
                    setattr(video_record, attr, value)

            # Save comments
            for comment_data in comments:
                comment_data["published_at"]=datetime.strptime(comment_data["published_at"],'%Y-%m-%d')

                if not db.session.query(Comment).filter_by(comment_id=comment_data['comment_id']).first():
                    db.session.add(Comment(**comment_data))

            db.session.commit()
            return {"message": "Video details, channel info, and comments saved successfully."}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"An error occurred: {str(e)}"}, 500


class ChannelDetailsFromDB(Resource):
    def get(self):
        """
        Fetch channel details and associated video IDs from the database.
        """
        channel_id = request.args.get('channel_id')
        if not channel_id:
            return {"error": "Channel ID is required."}, 400

        try:
            # Fetch channel details from the database
            channel = db.session.query(Channel).filter_by(channel_id=channel_id).first()
            if not channel:
                return {"error": "Channel not found."}, 404

            # Fetch associated video IDs from the Video model (assuming 'channel_id' is a foreign key in the Video table)
            video_ids = db.session.query(Video.video_id).filter_by(channel_id=channel_id).all()
            video_ids_list = [video.video_id for video in video_ids]  # Extract video IDs from the result

            # Return channel details and video IDs
            return {
                "channel_info": {
                    "channel_id": channel.channel_id,
                    "channel_name": channel.channel_name,
                    "subscribers": channel.subscribers,
                    "total_videos": channel.total_videos,
                    "view_count": channel.view_count,
                    "channel_description": channel.channel_description,
                },
                "video_ids": video_ids_list
            }, 200

        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500

class VideoDetailsFromDB(Resource):
    def get(self):
        """
        Fetch video details from the database for multiple video IDs.
        Accepts a comma-separated list of video IDs.
        """
        video_ids = request.args.get('video_ids')
        if not video_ids:
            return {"error": "Video IDs are required."}, 400

        try:
            # Split the comma-separated video IDs into a list
            video_ids_list = video_ids.split(',')

            # Query the database to fetch details for all the video IDs
            videos = db.session.query(Video).filter(Video.video_id.in_(video_ids_list)).all()
            if not videos:
                return {"error": "No videos found for the provided video IDs."}, 404

            # Prepare the response with video details
            video_details = []
            for video in videos:
                video_details.append({
                    "video_id": video.video_id,
                    "channel_id": video.channel_id,
                    "video_name": video.video_name,
                    "video_description": video.video_description,
                    "published_date": video.published_date.isoformat(),
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "dislike_count": video.dislike_count,
                    "favorite_count": video.favorite_count,
                    "comment_count": video.comment_count,
                    "duration": video.duration,
                    "thumbnail": video.thumbnail,
                })

            return {"video_details": video_details}, 200

        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500


class VideoCommentsFromDB(Resource):
    def get(self):
        """
        Fetch video comments from the database.
        """
        video_id = request.args.get('video_id')
        if not video_id:
            return {"error": "Video ID is required."}, 400

        try:
            comments = db.session.query(Comment).filter_by(video_id=video_id).all()
            if not comments:
                return {"error": "No comments found for this video."}, 404

            return {
                "video_id": video_id,
                "comments": [
                    {
                        "comment_id": comment.comment_id,
                        "author": comment.author,
                        "text": comment.text,
                        "likes": comment.likes,
                        "published_at": comment.published_at.isoformat(),
                    }
                    for comment in comments
                ],
            }, 200
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500

class VideoDetailsFromPlaylist(Resource):
    def get(self):
        """
        Fetch video details for all videos in a given playlist and return as JSON.
        """
        # Get the playlist ID from the query parameters
        playlist_id = request.args.get('playlist_id')
        
        if not playlist_id:
            return {"error": "Playlist ID is required."}, 400

        try:
            # Fetch video details from the playlist using the YouTube API
            video_details = yt_fetcher.get_video_details_from_playlist(playlist_id)
            
            if not video_details:
                return {"error": "No videos found in the playlist."}, 404
            
            # Return the video details as a JSON response
            return {"videos": video_details}, 200
        
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500
class AnalyticsResource(Resource):
    def get(self):
        # 1. Channels with the most videos
        most_videos = db.session.query(
            Channel.channel_name, db.func.count(Video.video_id).label("video_count")
        ).join(Video).group_by(Channel.channel_id).order_by(db.desc("video_count")).limit(10).all()
        most_videos_data = [
            {"channel_name": row.channel_name, "video_count": row.video_count}
            for row in most_videos
        ]

        # 2. Top 10 most viewed videos and their channels
        most_viewed_videos = db.session.query(
            Video.video_name, Video.view_count, Channel.channel_name
        ).join(Channel).order_by(db.desc(Video.view_count)).limit(10).all()
        most_viewed_videos_data = [
            {"video_name": row.video_name, "view_count": row.view_count, "channel_name": row.channel_name}
            for row in most_viewed_videos
        ]

        
        # 4. Top 10 Videos with the highest likes
        most_liked_videos = db.session.query(
            Video.video_name, Video.like_count, Channel.channel_name
        ).join(Channel).order_by(db.desc(Video.like_count)).limit(10).all()
        most_liked_videos_data = [
            {"video_name": row.video_name, "like_count": row.like_count, "channel_name": row.channel_name}
            for row in most_liked_videos
        ]

        

       

        # 7. Channels that published videos in 2022
        published_in_2022 = db.session.query(Channel.channel_name).join(Video).filter(
            db.func.extract('year', Video.published_date) == 2022
        ).distinct().all()
        published_in_2022_data = [row.channel_name for row in published_in_2022]

        

        # 9. Top 10 Videos with the highest comments
        most_commented_videos = db.session.query(
            Video.video_name, db.func.count(Comment.comment_id).label("comment_count"), Channel.channel_name
        ).join(Comment).join(Channel).group_by(Video.video_id, Channel.channel_id).order_by(
            db.desc("comment_count")
        ).limit(10).all()
        most_commented_videos_data = [
            {"video_name": row.video_name, "comment_count": row.comment_count, "channel_name": row.channel_name}
            for row in most_commented_videos
        ]

        # Combine all analytics into a single JSON
        analytics = {
            "most_videos": most_videos_data,
            "T10_most_viewed_videos": most_viewed_videos_data,
            "T10_most_liked_videos": most_liked_videos_data,
            "published_in_2022": published_in_2022_data,
            "T10_most_commented_videos": most_commented_videos_data,
        }

        return jsonify(analytics)

