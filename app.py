import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load CSV Files
url3 = 'https://raw.githubusercontent.com/Marc-Bouche/spotify-song-recommendation/refs/heads/main/csv_files/df_combined.csv'
url4 = 'https://raw.githubusercontent.com/Marc-Bouche/spotify-song-recommendation/refs/heads/main/csv_files/ww_de.csv'

try:
    df_combined = pd.read_csv(url3)
    ww_de = pd.read_csv(url4)
except Exception as e:
    st.error("Failed to load the CSV files. Please check the URLs or your connection.")
    st.stop()

# Spotify API Credentials
client_id = "4bc7ba599c3e4007b1f63b6d4b805108"
client_secret = "2c0d1010a68c4f28a2f791f163aac7e8"

# Initialize Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Placeholder Functions
def get_audio_features(track_id):
    try:
        return sp.audio_features([track_id])[0]
    except Exception:
        return None

def prepare_user_features(user_audio_features, feature_columns):
    # Simulate feature scaling for necessary columns
    return [user_audio_features.get(col, 0) for col in feature_columns]

def recommend_from_cluster(df_combined, user_cluster):
    return df_combined[df_combined["cluster"] == user_cluster]

def play_song(song_title, track_id):
    spotify_url = f"https://open.spotify.com/track/{track_id}"
    st.write(f"Playing **{song_title}**...")
    st.markdown(f"[Click here to listen on Spotify]({spotify_url})")

# Full Workflow Function
def full_workflow(user_input):
    search_results = sp.search(q=user_input, type='track,artist', limit=1)
    
    if not search_results['tracks']['items'] and not search_results['artists']['items']:
        st.error(f"No results found for '{user_input}'.")
        return

    if search_results['tracks']['items']:
        track = search_results['tracks']['items'][0]
        song_name = track.get('name', 'Unknown Song')
        artist_name = track['artists'][0].get('name', 'Unknown Artist')
        st.write(f"### Found Song: {song_name} by {artist_name}")
        
        if song_name in ww_de.get('song_title', []):
            st.success(f"The song '{song_name}' is found in your `ww_de` DataFrame.")
            random_recommendation = ww_de.sample(n=1)
            st.write("#### Recommended Song from ww_de:")
            st.table(random_recommendation[['song_title', 'artist']])
            random_track_id = random_recommendation['id'].iloc[0]  # Updated to 'id'
            play_song(random_recommendation['song_title'].iloc[0], random_track_id)
        else:
            user_audio_features = get_audio_features(track['id'])
            if user_audio_features:
                feature_columns = ['danceability', 'energy', 'tempo']  # Example features
                user_features_scaled = prepare_user_features(user_audio_features, feature_columns)
                user_cluster = 0  # Placeholder: replace with your actual clustering logic
                st.info(f"Song '{song_name}' belongs to cluster {user_cluster}.")
                recommendations = recommend_from_cluster(df_combined, user_cluster)
                if not recommendations.empty:
                    recommended_song = recommendations.iloc[0]
                    st.write("#### Recommended Song based on musical similarity:")
                    st.write(f"- **{recommended_song['song_title']}** by {recommended_song['artist']}")
                    play_song(recommended_song['song_title'], recommended_song['id'])  # Updated to 'id'
                else:
                    st.error("No recommendations found based on cluster.")
            else:
                st.error(f"Unable to retrieve audio features for '{song_name}'.")
    
    elif search_results['artists']['items']:
        artist = search_results['artists']['items'][0]
        artist_name = artist.get('name', 'Unknown Artist')
        st.write(f"### Found Artist: {artist_name}")
        artist_tracks = sp.artist_top_tracks(artist['id'])['tracks']
        if artist_tracks:
            st.write(f"#### Top song by {artist_name}:")
            top_song = artist_tracks[0]
            st.write(f"- **{top_song['name']}** ([Listen on Spotify](https://open.spotify.com/track/{top_song['id']}))")
        else:
            st.warning(f"No top tracks found for artist '{artist_name}'.")

# Streamlit Interface
st.title("Spotify Song/Artist Search and Recommendations")

user_input = st.text_input("Enter a song or artist name:")

if st.button("Search"):
    if user_input:
        full_workflow(user_input)
    else:
        st.warning("Please enter a valid song or artist name.")
