import os
import base64
import requests
import json
from dotenv import load_dotenv
from scrape import get_song

load_dotenv()
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")

    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + auth_base64,
        'Content-type': 'application/x-www-form-urlencoded'
    }
    data = {"grant_type" : "client_credentials"}
    result = requests.post(url, headers = headers, data = data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_song_url(song):
    ACCESS_TOKEN = get_token()

    # get song artist
    artist = song[1]

    # get japanese artist if it exists
    japanese_artist = ""
    if "(" in artist and ")" in artist:
        japanese_artist = artist.split("(")[1].split(")")[0]
   
    # remove japanese words in parenthesis (if any)
    artist = artist.split("(")[0].strip()

    # get song name
    # remove "by" and everything after it
    song_name = song[0].split("by")[0].strip()
    song_name = song_name[1:]
    # remove quotes from the song name
    song_name = song_name.replace("\"", "")
    # replace single quotes with the correct unicode character
    # this is to avoid issues with the Spotify API
    song_name = song_name.replace("'", "’")

    # get japanese name if it exists
    # if the song name has a japanese name in parenthesis, we extract it
    japanese_name = ""
    if ("(" in song[0] and ")" in song[0]):
        japanese_name = song[0].split("(")[1].split(")")[0]

    # base URL for Spotify search
    search_url = "https://api.spotify.com/v1/search"

    # make the request to Spotify API
    response = requests.get(
        search_url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}", 
                 "Accept-Language": "en"}, # specify the language for the response
        params={"q": song_name, "type": "track", "limit": 10}
    )

    # check if the request was successful
    if response.status_code != 200:
        return "Error fetching song from Spotify"
    results = response.json()
    track_id = None

    # remove any extra information in parenthesis
    song_name = song_name.split(" (")[0].strip()

    # iterate through the results to find the track
    # check if the artist and song name match
    for item in results['tracks']['items']:
        # if japanese name exists, check for both song names (romaji and japanese characters)
        if japanese_name != "":
            # if japanese artist exists, check for both artists (romaji and japanese characters)
            if japanese_artist != "":
                if ((japanese_artist in item['artists'][0]['name'].strip() or artist in item['artists'][0]['name'].strip()) and 
                     ((song_name in item['name'].strip()) or (japanese_name in item['name'].strip()))):
                    track_id = item['id']
                    break
            # if no japanese artist, check only the romaji song name
            else:
                if artist in item['artists'][0]['name'].strip() and ((song_name in item['name'].strip()) or (japanese_name in item['name'].strip())):
                    track_id = item['id']
                    break
        # if no japanese name, check only the romaji song name
        else:
            # if japanese artist exists, check for both artists (romaji and japanese characters)
            if japanese_artist != "":
                if ((japanese_artist in item['artists'][0]['name'].strip() or artist in item['artists'][0]['name'].strip()) and 
                     song_name in item['name'].strip()):
                    track_id = item['id']
                    break
            # if no japanese artist, check only the romaji artist and song name
            else:
                if (artist in item['artists'][0]['name'].strip() and song_name in item['name'].strip()):
                    track_id = item['id']
                    break
    if track_id == None:
        track_url = "Song not found on Spotify"
    else:
        track_url = f"https://open.spotify.com/track/{track_id}"
        
    # return the track URL
    return track_url