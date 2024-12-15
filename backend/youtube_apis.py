import re
from flask import jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import pandas as pd
import json

class YouTubeDataFetcher:
    def __init__(self, api_key):
        """Initialize the YouTube API client."""
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_channel_stats(self, channel_id):
        """Fetch basic channel statistics."""
        request = self.youtube.channels().list(
            part='snippet,contentDetails,statistics',
            id=channel_id
        )
        response = request.execute()
        # print("here",response)
        if "items" not in response:
            return None
            
        channel_data = response['items'][0]
        # print(response)
        stats = {
            'channel_name': channel_data['snippet']['title'],
            'subscribers': channel_data['statistics']['subscriberCount'],
            'total_videos': channel_data['statistics']['videoCount'],
            'playlist_id': channel_data['contentDetails']['relatedPlaylists']['uploads'],
            'view_count': channel_data['statistics']['viewCount'],
            'channel_description': channel_data['snippet']['description'],
            # 'status': channel_data['status'].get('privacyStatus', 'Not Available'),
            'channel_type': channel_data['snippet'].get('channelType', 'Not Available'),
        }
        return stats
    
    def get_video_ids(self, playlist_id):
        """Get all video IDs from a playlist."""
        video_ids = []
        try:
            request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50
            )
            
            while request:
                response = request.execute()
                
                for item in response['items']:
                    video_ids.append(item['contentDetails']['videoId'])
                    
                request = self.youtube.playlistItems().list_next(request, response)
        
        except HttpError as e:
            print(f"HTTP error occurred: {e}")
            return
            # Handle specific HTTP errors here
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return
        
        return video_ids
    
    def get_video_details(self, video_ids):
        """Get detailed information for each video."""
        all_video_stats = []
        
        # Process videos in chunks of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids[i:i + 50])
            )
            response = request.execute()
            
            for video in response['items']:
                try:
                    video_stats = {
                        'video_id': video['id'],
                        'video_name': video['snippet']['title'],
                        'channel_id': video['snippet']['channelId'],  # Add channel ID here
                        'video_description': video['snippet'].get('description', 'No description available'),
                        'published_date': video['snippet']['publishedAt'][:10],
                        'view_count': int(video['statistics'].get('viewCount', 0)),
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'dislike_count': int(video['statistics'].get('dislikeCount', 0)),
                        'favorite_count': int(video['statistics'].get('favoriteCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'duration': self.convert_duration(video['contentDetails']['duration']),
                        'thumbnail': video['snippet'].get('thumbnails', {}).get('default', {}).get('url', ''),
                        'caption_status': video['contentDetails'].get('caption', 'not available')  # Caption status
                    }
                    all_video_stats.append(video_stats)
                except ValueError as e:
                    # Log the error but continue processing other videos
                    print(f"Error processing video {video['id']}: {str(e)}")
                    continue
            
        
            return all_video_stats if len(all_video_stats) != 0 else None
    def convert_duration(self, duration):
        """
        Convert YouTube API ISO 8601 duration to seconds.
        Handles formats like:
        - PT1H2M30S -> 3750 seconds
        - P0D -> 0 seconds
        """
        try:
            # Handle special case P0D (0 duration)
            if duration == 'P0D':
                return 0
                
            # Match the ISO 8601 duration format
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            if not match:
                # If no match and not P0D, raise error
                raise ValueError(f"Invalid duration format: {duration}")
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            raise ValueError(f"Error parsing duration '{duration}': {str(e)}")
    def get_video_comments(self, video_id):
        """Get comments for a specific video."""
        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                textFormat='plainText'
            )
            response = request.execute()
            
            comments = []
            for item in response.get('items', []):
                comment_info = {
                    'comment_id': item['id'],
                    'video_id': video_id,
                    'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'published_at': item['snippet']['topLevelComment']['snippet']['publishedAt'][:10],
                    'likes': int(item['snippet']['topLevelComment']['snippet'].get('likeCount', 0)),
                    # 'reply_count': item['snippet'].get('totalReplyCount', 0)
                }
                comments.append(comment_info)
            return comments
            
        except HttpError as e:
            if 'commentsDisabled' in str(e):
                print(f"Comments are disabled for video {video_id}")
                return []  # Return empty list for videos with disabled comments
            elif 'quotaExceeded' in str(e):
                print(f"Quota exceeded while fetching comments for video {video_id}")
                return []
            else:
                print(f"Error fetching comments for video {video_id}: {str(e)}")
                return []
        except Exception as e:
            print(f"Unexpected error fetching comments for video {video_id}: {str(e)}")
            return []
        
    def fetch_all_data(self, channel_id):
        """Fetch all available data for a channel."""
        try:
            # Get channel statistics
            channel_stats = self.get_channel_stats(channel_id)
            if not channel_stats:
                return None
            
            # Get video IDs from uploads playlist
            video_ids = self.get_video_ids(channel_stats['playlist_id'])
            
            # Get video details
            videos = self.get_video_details(video_ids)
            
            # Get comments for each video (limited to first 100 comments per video)
            if videos:
                for video in videos:
                    try:
                        video['comments'] = self.get_video_comments(video['video_id'])
                    except Exception as e:
                        print(f"Error fetching comments for video {video['video_id']}: {str(e)}")
                        video['comments'] = []  # Set empty comments list on error
            
            # Combine all data
            channel_data = {
                'channel_info': channel_stats,
                'videos': videos if videos else []
            }
            
            return channel_data
        except Exception as e:
            print(f"Error in fetch_all_data: {str(e)}")
            raise
    
    def save_to_json(self, data, filename):
        """Save the data to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def save_to_csv(self, data, base_filename):
        """Save the data to CSV files."""
        # Save channel info
        channel_df = pd.DataFrame([data['channel_info']])
        channel_df.to_csv(f'{base_filename}_channel.csv', index=False)
        
        # Save video info
        videos_df = pd.DataFrame([{k:v for k,v in video.items() if k != 'comments'} 
                                for video in data['videos']])
        videos_df.to_csv(f'{base_filename}_videos.csv', index=False)
        
        # Save comments
        all_comments = []
        for video in data['videos']:
            for comment in video['comments']:
                comment['video_id'] = video['video_id']
                all_comments.append(comment)
        
        comments_df = pd.DataFrame(all_comments)
        comments_df.to_csv(f'{base_filename}_comments.csv', index=False)
    def get_video_ids_from_playlist(self, playlist_id):
        """Fetch the list of video IDs in a playlist."""
        video_ids = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                video_ids.append(item['snippet']['resourceId']['videoId'])

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return video_ids
    def get_video_details_from_playlist(self, playlist_id):
        """Fetch video details for all videos in a given playlist."""
        all_video_stats = []
        
        # Fetch the video IDs from the playlist
        video_ids = self.get_video_ids_from_playlist(playlist_id)
        
        if not video_ids:
            return {"error": "No videos found in the playlist."}

        # Process videos in chunks of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids[i:i + 50])
            )
            response = request.execute()
            
            for video in response['items']:
                try:
                    video_stats = {
                        'video_id': video['id'],
                        'video_name': video['snippet']['title'],
                        'channel_id': video['snippet']['channelId'],  # Add channel ID here
                        'video_description': video['snippet'].get('description', 'No description available'),
                        'published_date': video['snippet']['publishedAt'][:10],
                        'view_count': int(video['statistics'].get('viewCount', 0)),
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'dislike_count': int(video['statistics'].get('dislikeCount', 0)),
                        'favorite_count': int(video['statistics'].get('favoriteCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'duration': self.convert_duration(video['contentDetails']['duration']),
                        'thumbnail': video['snippet'].get('thumbnails', {}).get('default', {}).get('url', ''),
                        'caption_status': video['contentDetails'].get('caption', 'not available')  # Caption status
                    }
                    all_video_stats.append(video_stats)
                except ValueError as e:
                    # Log the error but continue processing other videos
                    print(f"Error processing video {video['id']}: {str(e)}")
                    continue

        return all_video_stats if len(all_video_stats) != 0 else None




#Test
if __name__ == '__main__':
    yt=YouTubeDataFetcher("AIzaSyB9aLq6v3lgGamfwMj2byDw9nEHDbJOMLI")
    # print(yt.get_video_ids("PLOzRYVm0a65dFqcSScAAtAjOMGrG7luhz"))
    # print(yt.get_video_details(['4uRATAPWKOU']))
    # print(yt.get_video_comments('4uRAAPWKOU'))#UCi9h1k_Y9sRago1TMnmMo-Q
    # print(yt.get_video_ids("b"))
    # print(yt.get_channel_stats("ggrbgdfe"))
    print(yt.fetch_all_data("UCi9h1k_Y9sRago1TMnmMo-Q"))
