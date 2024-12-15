import requests
import streamlit as st
class Fetcher:
    def __init__(_self, base_url="http://127.0.0.1:5000"):
        _self.base_url = base_url
    @st.cache_data(ttl=600)
    def get_channel_info(_self, channel_id):
        """Fetch channel info and video IDs."""
        try:
            response = requests.get(f"{_self.base_url}/api/channel", params={"channel_id": channel_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def get_video_details(_self, video_id):
        """Fetch video details."""
        try:
            response = requests.get(f"{_self.base_url}/api/videos", params={"video_ids": video_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def get_video_comments(_self, video_id):
        """Fetch comments for a video."""
        try:
            response = requests.get(f"{_self.base_url}/api/comments", params={"video_ids": video_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)        
    def get_channel_info_db(_self, channel_id):
        """Fetch channel info and video IDs."""
        try:
            response = requests.get(f"{_self.base_url}/api/db/channel", params={"channel_id": channel_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def get_video_details_db(_self, video_id):
        """Fetch video details."""
        try:
            response = requests.get(f"{_self.base_url}/api/db/videos", params={"video_ids": video_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def get_video_comments_db(_self, video_id):
        """Fetch comments for a video."""
        try:
            response = requests.get(f"{_self.base_url}/api/db/comments", params={"video_id": video_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def get_video_details_playlist(_self,playlist_id):
        """Fetch video details for all videos in the playlist."""
        try:
            # Send a request to the backend to fetch video details for the given playlist ID
            response = requests.get(f"{_self.base_url}/api/videos_from_playlist", params={"playlist_id": playlist_id})
            
            # Raise an error if the request was unsuccessful
            response.raise_for_status()

            # Return the JSON response containing the video details
            return response.json()

        except requests.RequestException as e:
            # Handle any errors that occur during the request
            return {"error": str(e)}
    def save_all_data(_self,channel_id):
        """Save all data (channel, videos, comments) for the channel ID."""
        try:
            response = requests.post(f"{_self.base_url}/api/save_all", params={"channel_id": channel_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    def save_video_data(_self,video_id):
        """Save videos, comments for the video ID."""
        try:
            response = requests.post(f"{_self.base_url}/api/save_video", json={"video_id": video_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    @st.cache_data(ttl=600)
    def fetch_analytics(_self):
        try:
            response = requests.get(f"{_self.base_url}/analytics")
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

if __name__ == "__main__":
    ft=Fetcher()
    # print(ft.get_channel_info_db("UCi9h1k_Y9sRago1TMnmMo-Q"))
    # print(ft.get_video_details_db("1X4GmEitrxo,ppU4xn9DZvI"))
    # print(ft.get_video_comments_db("pdzA5QUBzDs"))
    # print(ft.save_all_data("UCi9h1k_Y9sRago1TMnmMo-Q"))
    print(ft.fetch_analytics())
