import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load CSV Files
url3 = 'https://raw.githubusercontent.com/Marc-Bouche/spotify-song-recommendation/refs/heads/main/csv_files/df_combined.csv'
url4 = 'https://raw.githubusercontent.com/Marc-Bouche/spotify-song-recommendation/refs/heads/main/csv_files/ww_de.csv'

try:
    df_combined = pd.read_csv(url3)
    ww_de = pd.read_csv(url4)
except Exception as e:
    st.error("Failed to load the CSV files. Please check the URLs or your connection.")
    st.stop()

# Step 1: Select Features for Clustering
features = df_combined[['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 
                        'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']]

# Step 2: Normalize Features
scaler = StandardScaler()
try:
    features_scaled = scaler.fit_transform(features)
except Exception as e:
    st.error(f"Error during feature scaling: {e}")
    st.stop()

# Check for NaN or inf in scaled features
if np.isnan(features_scaled).sum() > 0 or np.isinf(features_scaled).sum() > 0:
    st.error("Features contain NaN or inf values after scaling.")
    st.stop()

# Step 3: Apply K-Means Clustering
try:
    kmeans = KMeans(n_clusters=2000, random_state=42)  # Adjust 'n_clusters' as needed
    df_combined['cluster'] = kmeans.fit_predict(features_scaled)
except Exception as e:
    st.error(f"Error during K-Means clustering: {e}")
    st.stop()

# Spotify API Credentials
from spotify_config import client_id, client_secret

# Initialize Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Placeholder Functions
def get_audio_features(track_id):
    try:
        return sp.audio_features([track_id])[0]
    except Exception:
        return None

def prepare_user_features(user_audio_features, feature_columns):
    return [user_audio_features.get(col, 0) for col in feature_columns]

def recommend_from_cluster(df_combined, user_cluster):
    return df_combined[df_combined["cluster"] == user_cluster]

def play_song(song_title, track_id):
    spotify_url = f"https://open.spotify.com/track/{track_id}"
    st.write(f"Playing **{song_title}**...")
    st.markdown(f"[Click here to listen on Spotify]({spotify_url})")

def find_closest_cluster(user_features, df_combined):
    feature_columns = ['danceability', 'energy', 'tempo']  # Example features
    df_combined_features = df_combined[feature_columns].values
    similarity_scores = cosine_similarity([user_features], df_combined_features)
    closest_cluster_idx = similarity_scores.argmax()
    closest_cluster = df_combined.iloc[closest_cluster_idx]['cluster']
    return closest_cluster

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
            random_track_id = random_recommendation['id'].iloc[0]
            play_song(random_recommendation['song_title'].iloc[0], random_track_id)
        else:
            user_audio_features = get_audio_features(track['id'])
            if user_audio_features:
                user_features = prepare_user_features(user_audio_features, ['danceability', 'energy', 'tempo'])
                
                # Dynamically find the closest cluster
                user_cluster = find_closest_cluster(user_features, df_combined)
                st.info(f"Song '{song_name}' belongs to cluster {user_cluster}.")
                
                recommendations = recommend_from_cluster(df_combined, user_cluster)
                if not recommendations.empty:
                    recommended_song = recommendations.iloc[0]
                    st.write("#### Recommended Song based on musical similarity:")
                    st.write(f"- **{recommended_song['song_title']}** by {recommended_song['artist']}")
                    play_song(recommended_song['song_title'], recommended_song['id'])
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
