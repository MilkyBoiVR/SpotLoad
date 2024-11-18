import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import sys
import subprocess
import argparse
import contextlib
from tqdm import tqdm

def load_credentials(file_path='credentials.txt'):
    credentials = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            credentials[key] = value
    return credentials

credentials = load_credentials()

SPOTIPY_CLIENT_ID = credentials['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = credentials['SPOTIPY_CLIENT_SECRET']

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "Downloads")

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def strip_quotes(s):
    return s.strip('"').strip("'")

def open_folder(folder_path):
    if os.name == 'nt':
        os.startfile(folder_path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', folder_path])
    else:
        subprocess.Popen(['xdg-open', folder_path])

def get_artist_tracks(artist_link):
    artist_URI = artist_link.split("/")[-1].split("?")[0]
    results = sp.artist_albums(artist_URI, album_type='album,single', limit=50)
    
    albums = results['items']
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    
    all_tracks = []
    for album in albums:
        album_id = album['id']
        album_name = album['name']
        tracks = sp.album_tracks(album_id)
        
        for track in tracks['items']:
            track_info = {
                'name': track['name'],
                'artist': album['artists'][0]['name'],
                'album': album_name,
                'duration_ms': track['duration_ms']
            }
            all_tracks.append(track_info)
    
    return all_tracks

def get_album_tracks(album_link):
    album_URI = album_link.split("/")[-1].split("?")[0]
    results = sp.album_tracks(album_URI)
    
    album_details = sp.album(album_URI)
    album_name = album_details['name']
    
    tracks = []
    for item in results['items']:
        track = item
        track_info = {
            'name': track['name'],
            'artist': album_details['artists'][0]['name'],
            'album': album_name,
            'duration_ms': track['duration_ms']
        }
        tracks.append(track_info)
    
    return album_name, tracks

def get_playlist_tracks(playlist_link):
    playlist_URI = playlist_link.split("/")[-1].split("?")[0]
    results = sp.playlist_tracks(playlist_URI)
    
    playlist_details = sp.playlist(playlist_URI)
    playlist_name = playlist_details['name']
    
    tracks = []
    for item in results['items']:
        track = item['track']
        track_info = {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration_ms': track['duration_ms']
        }
        tracks.append(track_info)
    
    return playlist_name, tracks

def get_track_details(track_link):
    track_URI = track_link.split("/")[-1].split("?")[0]
    
    if len(track_URI) != 22:
        raise ValueError("Invalid track ID")
    
    track = sp.track(track_URI)
    
    track_info = {
        'name': track['name'],
        'artist': track['artists'][0]['name'],
        'album': track['album']['name'],
        'duration_ms': track['duration_ms']
    }
    
    return track_info

@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def print_progress_bar(index, total, download_message):
    with tqdm(total=total, desc=download_message, ncols=100) as pbar:
        pbar.update(index)

def download_song_from_youtube(song_name, artist, folder_path=None, quality='320'):
    query = f"{song_name} {artist} audio"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'outtmpl': os.path.join(folder_path, f'{song_name} - {artist}.mp3') if folder_path else f'{song_name} - {artist}.mp3',
        'quiet': True,
        'no-warnings': True,
        'ignoreerrors': True
    }
    
    with suppress_output():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])

def convert_files_to_mp3(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.webm') or filename.endswith('.m4a') or filename.endswith('.wav'):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.splitext(input_path)[0] + '.mp3'
            subprocess.run(['ffmpeg', '-i', input_path, '-q:a', '0', '-map', 'a', output_path], check=True)
            os.remove(input_path)

def download_from_spotify_link(link, folder_path=None, quality='320'):
    folder_path = folder_path or DEFAULT_DOWNLOAD_FOLDER
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    if "track" in link:
        track_info = get_track_details(link)
        print(f"Downloading: {track_info['name']} by {track_info['artist']}")
        download_song_from_youtube(track_info['name'], track_info['artist'], folder_path, quality)
        print(f"Download Complete: {track_info['name']} by {track_info['artist']}")

    elif "album" in link:
        album_name, tracks = get_album_tracks(link)
        album_folder = os.path.join(folder_path, album_name)
        if not os.path.exists(album_folder):
            os.makedirs(album_folder)
        print(f"Downloading album: {album_name}")
        for track in tracks:
            print(f"Downloading: {track['name']} by {track['artist']}")
            download_song_from_youtube(track['name'], track['artist'], album_folder, quality)
            print(f"Download Complete: {track['name']} by {track['artist']}")

    elif "playlist" in link:
        playlist_name, tracks = get_playlist_tracks(link)
        playlist_folder = os.path.join(folder_path, playlist_name)
        if not os.path.exists(playlist_folder):
            os.makedirs(playlist_folder)
        print(f"Downloading playlist: {playlist_name}")
        for track in tracks:
            print(f"Downloading: {track['name']} by {track['artist']}")
            download_song_from_youtube(track['name'], track['artist'], playlist_folder, quality)
            print(f"Download Complete: {track['name']} by {track['artist']}")

    elif "artist" in link:
        tracks = get_artist_tracks(link)
        artist_folder = os.path.join(folder_path, tracks[0]['artist'])
        if not os.path.exists(artist_folder):
            os.makedirs(artist_folder)
        print(f"Downloading artist: {tracks[0]['artist']}")
        for track in tracks:
            print(f"Downloading: {track['name']} by {track['artist']}")
            download_song_from_youtube(track['name'], track['artist'], artist_folder, quality)
            print(f"Download Complete: {track['name']} by {track['artist']}")

def download_from_list(file_path, folder_path=None, quality='320'):
    with open(file_path, 'r') as file:
        links = file.readlines()
        total = len(links)
        for index, link in enumerate(links):
            link = link.strip()
            print(f"Downloading from list: {link}")
            download_from_spotify_link(link, folder_path, quality)
            print_progress_bar(index + 1, total, f"Downloading from list")
            print(f"Download Complete: {link}")

def search_spotify(query, folder_path=None, quality='320'):
    results = sp.search(query, limit=5, type='track')
    if not results['tracks']['items']:
        print("No results found.")
        return
    
    first_track = results['tracks']['items'][0]
    track_name = first_track['name']
    artist_name = first_track['artists'][0]['name']
    track_link = first_track['external_urls']['spotify']
    
    print(f"Found: {track_name} by {artist_name}")
    download_from_spotify_link(track_link, folder_path, quality)

def print_help():
    help_text = """
SPOTLOAD

Commands
spotload {link} [OPTIONS]
spotload list {file path}
spotload search {query}
spotload help

[OPTIONS]
Quality - Enter any kbps (320)
path - Specify a folder for the download

Examples
spotload https://open.spotify.com/track/77hjM9bMmgfTGJXv14UFmi
spotload search Play That Song by Train
spotload list C:/songs.txt
    """
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description="SpotLoad - Download music from Spotify")
    parser.add_argument('command', nargs='?', type=str, help='Command to run (search, list, or a Spotify link)')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments for the command (e.g., query, file path)')

    args = parser.parse_args()

    command = args.command
    extra_args = args.args
    quality = '320'
    folder_path = None

    if len(extra_args) > 0:
        if extra_args[-1].isdigit():
            quality = extra_args.pop() 
        if len(extra_args) > 0 and os.path.isdir(extra_args[-1]):
            folder_path = extra_args.pop()

    clear_terminal()

    if command:
        if command.lower() == 'help':
            print_help()
        elif command.lower() == 'search':
            query = " ".join(extra_args)
            search_spotify(query, folder_path, quality)
        elif command.lower() == 'list':
            file_path = extra_args[0]
            download_from_list(file_path, folder_path, quality)
        elif "spotify.com" in command:
            download_from_spotify_link(command, folder_path, quality)
        else:
            print_help()
    else:
        print_help()

if __name__ == "__main__":
    main()