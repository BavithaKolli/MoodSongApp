import streamlit as st
import google.generativeai as genai
import requests
from typing import List

# === CONFIG ===
GOOGLE_API_KEY = "AIzaSyBq2gHsfCJICo_KodUqWaal7929OeRzuQI"  # Replace with your actual Gemini API key
SPOTIFY_CLIENT_ID = "eba7cff4235949e5bef32ce7548dbfc3"  # Replace with your Spotify Client ID
SPOTIFY_CLIENT_SECRET = "17e8dc8308be4908b26f3a50fdd39d7a"  # Replace with your Spotify Secret

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

languages = ["English", "Hindi", "Telugu", "Tamil"]

# === STYLING ===
st.set_page_config(page_title="🎵 AI Mood-Based Playlist Recommender", layout="wide")
st.markdown("""
    <style>
        .playlist-card {
            border-radius: 15px;
            background-color: #f9f9f9;
            padding: 1.5em;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1em;
        }
        .title {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 0.3em;
        }
    </style>
""", unsafe_allow_html=True)

# === FUNCTIONS ===
def detect_mood(feeling: str) -> str:
    prompt = f"The user says they feel: '{feeling}'. Detect the mood in one word (happy, sad, energetic, calm)."
    response = model.generate_content(prompt)
    mood = response.text.strip().lower()
    for key in ["happy", "sad", "energetic", "calm"]:
        if key in mood:
            return key
    return "happy"

def get_spotify_token() -> str:
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    if auth_response.status_code == 200:
        return auth_response.json().get("access_token", "")
    else:
        st.error(f"Spotify Auth Error: {auth_response.status_code} - {auth_response.text}")
        return ""

def search_spotify_playlists(mood: str, language: str, token: str) -> List[dict]:
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    query = f"{language} {mood} mood playlist"
    url = f"https://api.spotify.com/v1/search?q={query}&type=playlist&limit=5"
    response = requests.get(url, headers=headers)

    playlists = []
    if response.status_code == 200:
        data = response.json()
        items = data.get("playlists", {}).get("items", [])
        for item in items:
            if item:  # Make sure it's not None
                playlists.append({
                    "title": item.get('name', 'Unknown'),
                    "url": item.get('external_urls', {}).get('spotify', '#'),
                    "image": item.get('images', [{}])[0].get('url', '')
                })
    else:
        st.error(f"Spotify API Error: {response.status_code} - {response.text}")

    return playlists

def embed_spotify_player(playlist_url: str):
    uri_part = playlist_url.split("/")[-1].split("?")[0]
    st.components.v1.html(
        f"""
        <iframe style="border-radius:12px" 
                src="https://open.spotify.com/embed/playlist/{uri_part}" 
                width="100%" height="152" frameBorder="0" 
                allowtransparency="true" allow="encrypted-media"></iframe>
        """, height=180
    )

# === UI ===
st.title("🎵 AI Mood-Based Playlist Recommender")
st.markdown("Tell us how you're feeling, and we'll match you with the perfect Spotify music!")

language = st.selectbox("🌍 Choose Your Preferred Language:", languages)
feeling = st.text_input("💬 How are you feeling today?")

if st.button("🔍 Get Playlist") and feeling:
    with st.spinner("Detecting your mood and fetching Spotify playlists..."):
        mood = detect_mood(feeling)
        st.success(f"Detected mood: **{mood.title()}**")

        token = get_spotify_token()
        playlist_data = search_spotify_playlists(mood, language, token)

        if playlist_data:
            st.subheader(f"🎧 Top {language} Playlists for a {mood} Mood")
            for playlist in playlist_data:
                with st.container():
                    st.markdown(f"<div class='playlist-card'><div class='title'>{playlist['title']}</div>", unsafe_allow_html=True)
                    if playlist['image']:
                        st.image(playlist['image'], width=300)
                    embed_spotify_player(playlist['url'])
                    st.markdown(f"[🎵 Open in Spotify]({playlist['url']})")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No playlists found. Try again later.")
else:
    st.info("Enter your feeling above and click 'Get Playlist' to begin.")

