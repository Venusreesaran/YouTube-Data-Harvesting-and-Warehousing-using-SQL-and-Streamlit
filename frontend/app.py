
import pandas as pd
import streamlit as st
from streamlit_navigation_bar import st_navbar
from helper import Fetcher
import matplotlib.pyplot as plt
ft = Fetcher()

# Initialize session states
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None
if 'videos' not in st.session_state:
    st.session_state.videos = []
if 'channel_info' not in st.session_state:
    st.session_state.channel_info = None


def load_about():
    with open('about.txt', 'r') as f:
        about_content = f.read()
    return about_content
# Custom CSS for dark theme and styling
with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def show_video_comments(com_data):
    st.markdown("### Comments")
    for comment in com_data["comments"]:
        st.markdown(f"""
        <div class="comment-card">
            <strong>{comment['author']}</strong> • 👍 {comment['likes']} • {comment['published_at']}<br>
            {comment['text']}
        </div>
        """, unsafe_allow_html=True)

def show_video_details(video, data_source="web"):
    st.markdown('<div class="video-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(video["thumbnail"], use_column_width=True)
    with col2:
        st.markdown(f"### {video['video_name']}")
        st.markdown(f'#### Channel ID: {video["channel_id"]}')
        st.markdown(f"Views: **{video['view_count']}** • Likes: **{video['like_count']}** \
                    • Dislikes: **{video['dislike_count']}** • Duration: **{video['duration']}** secs")
        st.markdown(f"Published: {video['published_date']} • Comments **{video['comment_count']}**")
        st.markdown(f"Description: {video['video_description']}")
    st.markdown('</div>', unsafe_allow_html=True)
    com_data = ft.get_video_comments(video["video_id"]) if data_source == "Web" else ft.get_video_comments_db(video["video_id"])
    if 'error' in com_data:
        st.markdown("No comments found")
        st.markdown(f"Error: {com_data['error']}")
    else:
        show_video_comments(com_data)

def search_section(placeholder_text):
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        search_id = st.text_input("Enter ID", placeholder=placeholder_text)
    with col2:
        data_source = st.radio("Data Source", ["Web", "Database"], horizontal=True)
    
    search_clicked = st.button("Search", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return search_id, data_source, search_clicked

def main():
    # Check if redirected to "Video" page
    query_params = st.query_params
    page = query_params.get("page", ["Channel"])[0]
    if 'export_state' not in st.session_state:
        st.session_state['export_state'] = {}
    
    # Navigation bar logic
    page = st_navbar(["Channel", "Video", "Playlist","Insights", "About"], 
                    options={"use_padding": False, "hide_nav": True},adjust=True)#,styles=styles)
    # st.write(page)
    
    # Automatically switch to "Video" page if a video is selected
    if st.session_state.selected_video and page != "Video":
        page = "Video"

    if page == "Channel":
        channel_id, data_source, search_clicked = search_section("UCxxx...")
        
        if search_clicked:
            if channel_id:
                if data_source == "Web":
                    with st.spinner('Fetching channel data...'):
                        data = ft.get_channel_info(channel_id)
                        if "error" in data:
                            st.error(data["error"])
                        else:
                            st.session_state.channel_info = data["channel_info"]
                            vid_ids = data["video_ids"]
                            with st.spinner('Fetching video details...'):
                                videos_data = ft.get_video_details(",".join(vid_ids))
                                if "error" in videos_data:
                                    st.error(videos_data["error"])
                                else:
                                    
                                    st.session_state.videos = videos_data["videos"]
                                    def export_to_db():
                                        with st.spinner("Exporting channel and video data to the database..."):
                                            try:
                                                result = ft.save_all_data(channel_id)
                                                if "error" in result:
                                                    st.error(f"Error exporting channel data: {result['error']}")
                                                else:
                                                    st.success("Channel and video data exported to the database successfully!")
                                            except Exception as e:
                                                st.error(f"An unexpected error occurred: {str(e)}")
                                    
                                    # Create button with the callback
                                    st.button(
                                        "Export to DB",
                                        on_click=export_to_db,
                                        key=f"export_btn_{channel_id}",
                                        use_container_width=True
                                    )
                else:
                    # Database fetch logic here
                    with st.spinner('Fetching channel data...'):
                        data = ft.get_channel_info_db(channel_id)
                        if "error" in data:
                            st.error(data["error"])
                        else:
                            # print(data)
                            st.session_state.channel_info = data["channel_info"]
                            vid_ids = data["video_ids"]
                            with st.spinner('Fetching video details...'):
                                videos_data = ft.get_video_details_db(",".join(vid_ids))
                                if "error" in videos_data:
                                    st.error(videos_data["error"])
                                else:

                                    st.session_state.videos = videos_data["video_details"]
            else:
                st.error("Please enter a Channel ID")

        if st.session_state.channel_info:
            st.markdown('<div class="channel-header">', unsafe_allow_html=True)
            info = st.session_state.channel_info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Channel Name", info["channel_name"])
            with col2:
                st.metric("Subscribers", info["subscribers"])
            with col3:
                st.metric("Total Views", info["view_count"])
            with col4:
                st.metric("Videos", info["total_videos"])
            st.write(f"### Description:\n{info['channel_description']}")
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.videos:
            for video in st.session_state.videos:
                with st.container():
                    st.markdown('<div class="video-card">', unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(video["thumbnail"], use_column_width=True)
                    with col2:
                        st.markdown(f"### {video['video_name']}")
                        st.markdown(f"Views: **{video['view_count']}** • Likes: **{video['like_count']}**")
                        st.markdown(f"Published: {video['published_date']}")
                        if st.button("View Details", key=f"video_{video['video_id']}", use_container_width=True):
                            st.session_state.selected_video = video
                            st.query_params = {"page": "Video"}  # Redirect to "Video"
                            st.experimental_rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Video":
        video_id, data_source, search_clicked = search_section("Video ID...")
        
        if search_clicked:
            if video_id:
                if data_source == "Web":
                    with st.spinner('Fetching video data...'):
                        video_data = ft.get_video_details(video_id)
                        if "error" in video_data:
                            st.error(video_data["error"])
                        else:
                            # print(video_data)
                            st.session_state.selected_video = video_data["videos"][0]
                            def export_video_info_to_db():
                                with st.spinner("Exporting video data to the database..."):
                                    try:
                                        result = ft.save_video_data(video_id)
                                        if "error" in result:
                                            st.error(f"Error exporting channel data: {result['error']}")
                                        else:
                                            st.success("Channel and video data exported to the database successfully!")
                                    except Exception as e:
                                        st.error(f"An unexpected error occurred: {str(e)}")
                            
                            # Create button with the callback
                            st.button(
                                "Export to DB",
                                on_click=export_video_info_to_db,
                                key=f"export_btn_{video_id}",
                                use_container_width=True
                            )
                else:
                    # Database fetch logic here
                    with st.spinner('Fetching video data...'):
                        video_data = ft.get_video_details_db(video_id)
                        if "error" in video_data:
                            st.error(video_data["error"])
                        else:
                            st.session_state.selected_video = video_data["video_details"][0]
            else:
                st.error("Please enter a Video ID")

        if st.session_state.selected_video:
            if st.button("← Back to Channel"):
                st.session_state.selected_video = None
                st.experimental_rerun()
            show_video_details(st.session_state.selected_video, data_source)

    elif page == "Playlist":
        playlist_id, data_source, search_clicked = search_section("Playlist ID...")
        
        if search_clicked:
            if playlist_id:
                if data_source == "Web":
                    with st.spinner('Fetching playlist data...'):
                        playlist_data = ft.get_video_details_playlist(playlist_id)
                        if "error" in playlist_data:
                            st.error(playlist_data["error"])
                        else:
                            st.session_state.videos = playlist_data["videos"]
                else:
                    # Database fetch logic here
                    pass
            else:
                st.error("Please enter a Playlist ID")

        if st.session_state.videos and not st.session_state.selected_video:
            for video in st.session_state.videos:
                with st.container():
                    st.markdown('<div class="video-card">', unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(video["thumbnail"], use_column_width=True)
                    with col2:
                        st.markdown(f"### {video['video_name']}")
                        st.markdown(f"Views: **{video['view_count']}** • Likes: **{video['like_count']}**")
                        st.markdown(f"Published: {video['published_date']}")
                        if st.button("View Details", key=f"video_{video['video_id']}", use_container_width=True):
                            st.session_state.selected_video = video
                            st.experimental_rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.selected_video:
            if st.button("← Back to Playlist"):
                st.session_state.selected_video = None
                st.experimental_rerun()
            show_video_details(st.session_state.selected_video, data_source)
    elif page == "Insights":
        # Title
        
        analytics = ft.fetch_analytics()
        if "error" not in analytics:
            st.title("YouTube Analytics Dashboard")
            # Section 1: Channels with the Most Videos
            st.header("Channels with the Most Videos")
            most_videos_df = pd.DataFrame(analytics["most_videos"])
            st.table(most_videos_df)

            # Bar chart for "Channels with the Most Videos"
            st.subheader("Bar Chart: Channels with the Most Videos")
            fig, ax = plt.subplots()
            ax.bar(most_videos_df["channel_name"], most_videos_df["video_count"], color="skyblue")
            ax.set_title("Channels with the Most Videos")
            ax.set_xlabel("Channel Name")
            ax.set_ylabel("Number of Videos")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)

            # Section 2: Top 10 Most Viewed Videos
            st.header("Top 10 Most Viewed Videos")
            most_viewed_df = pd.DataFrame(analytics["T10_most_viewed_videos"])
            st.table(most_viewed_df)

            # Horizontal bar chart for "Top 10 Most Viewed Videos"
            st.subheader("Bar Chart: Top 10 Most Viewed Videos")
            most_viewed_df = most_viewed_df.sort_values("view_count", ascending=True)  # For better visualization
            fig, ax = plt.subplots()
            ax.barh(most_viewed_df["video_name"], most_viewed_df["view_count"], color="orange")
            ax.set_title("Top 10 Most Viewed Videos")
            ax.set_xlabel("View Count")
            ax.set_ylabel("Video Name")
            st.pyplot(fig)

            # Section 3: Top 10 Most Liked Videos
            st.header("Top 10 Most Liked Videos")
            most_liked_df = pd.DataFrame(analytics["T10_most_liked_videos"])
            st.table(most_liked_df)

            # Pie chart for "Top 10 Most Liked Videos"
            st.subheader("Pie Chart: Top 10 Most Liked Videos")
            fig, ax = plt.subplots()
            ax.pie(
                most_liked_df["like_count"],
                labels=most_liked_df["video_name"],
                autopct="%1.1f%%",
                startangle=90,
                colors=plt.cm.Paired.colors,
            )
            ax.set_title("Most Liked Videos")
            st.pyplot(fig)

            # Section 4: Channels Published Videos in 2022
            st.header("Channels Published Videos in 2022")
            published_2022_df = pd.DataFrame(analytics["published_in_2022"], columns=["channel_name"])
            st.table(published_2022_df)

            # Section 5: Top 10 Most Commented Videos
            st.header("Top 10 Most Commented Videos")
            most_commented_df = pd.DataFrame(analytics["T10_most_commented_videos"])
            st.table(most_commented_df)

            # Horizontal bar chart for "Top 10 Most Commented Videos"
            st.subheader("Bar Chart: Top 10 Most Commented Videos")
            most_commented_df = most_commented_df.sort_values("comment_count", ascending=True)  # For better visualization
            fig, ax = plt.subplots()
            ax.barh(most_commented_df["video_name"], most_commented_df["comment_count"], color="green")
            ax.set_title("Top 10 Most Commented Videos")
            ax.set_xlabel("Comment Count")
            ax.set_ylabel("Video Name")
            st.pyplot(fig)

       
    elif page == "About":
        st.markdown("### About this app")
        st.markdown(load_about())

if __name__ == "__main__":
    main()
