import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import sys
import contextlib
import subprocess

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

def print_progress_bar(index, total):
    total_emoji_count = 10
    progress_percentage = int((index / total) * 100)
    crescent_emojis = ['🌑', '🌒', '🌓', '🌔', '🌕']
    full_emoji_count = progress_percentage // 10
    fractional_percentage = progress_percentage % 10
    fractional_emoji_index = int(fractional_percentage / 2.5)
    if progress_percentage == 100:
        bar = crescent_emojis[4] * total_emoji_count
    else:
        bar = (crescent_emojis[0] * (total_emoji_count - full_emoji_count - 1) +
               crescent_emojis[fractional_emoji_index] +
               crescent_emojis[4] * full_emoji_count)
    print(f'\r{index}/{total} songs downloaded {bar} {progress_percentage}%', end='')

def print_download_status(song_name, artist, total_tracks, index):
    clear_terminal()
    print(f"Downloading '{song_name}' by {artist}...")
    print_progress_bar(index + 1, total_tracks)

def download_song_from_youtube(song_name, artist, folder_path=None, quality='320'):
    query = f"{song_name} {artist} lyrics"
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
    folder_was_created = False
    if "track" in link:
        track_info = get_track_details(link)
        total_tracks = 1
        print_download_status(track_info['name'], track_info['artist'], total_tracks, 0)
        download_song_from_youtube(track_info['name'], track_info['artist'], folder_path, quality)
        print("\nDownload completed!")
    elif "album" in link:
        album_name, tracks = get_album_tracks(link)
        album_folder = folder_path or album_name.replace('/', '_').replace('\\', '_')
        if not os.path.exists(album_folder):
            os.makedirs(album_folder)
            folder_was_created = True
        total_tracks = len(tracks)
        clear_terminal()
        for index, track in enumerate(tracks):
            print_download_status(track['name'], track['artist'], total_tracks, index)
            download_song_from_youtube(track['name'], track['artist'], album_folder, quality)
        print("\nDownload completed!")
        convert_files_to_mp3(album_folder)
    elif "playlist" in link:
        playlist_name, tracks = get_playlist_tracks(link)
        playlist_folder = folder_path or playlist_name.replace('/', '_').replace('\\', '_')
        if not os.path.exists(playlist_folder):
            os.makedirs(playlist_folder)
            folder_was_created = True
        total_tracks = len(tracks)
        clear_terminal()
        for index, track in enumerate(tracks):
            print_download_status(track['name'], track['artist'], total_tracks, index)
            download_song_from_youtube(track['name'], track['artist'], playlist_folder, quality)
        print("\nDownload completed!")
        convert_files_to_mp3(playlist_folder)
    elif "artist" in link:
        tracks = get_artist_tracks(link)
        artist_name = tracks[0]['artist'] if tracks else 'Unknown_Artist'
        artist_folder = folder_path or artist_name.replace('/', '_').replace('\\', '_')
        if not os.path.exists(artist_folder):
            os.makedirs(artist_folder)
            folder_was_created = True
        total_tracks = len(tracks)
        clear_terminal()
        for index, track in enumerate(tracks):
            print_download_status(track['name'], track['artist'], total_tracks, index)
            download_song_from_youtube(track['name'], track['artist'], artist_folder, quality)
        print("\nDownload completed!")
        convert_files_to_mp3(artist_folder)
    else:
        print("Unsupported Spotify link.")
    if folder_was_created or folder_path:
        open_folder(album_folder if "album" in link else playlist_folder if "playlist" in link else artist_folder)

def main():
    link = input("Please enter a Spotify link (track, album, playlist, or artist): ").strip()
    folder_path = input("Enter the download folder path (or press Enter to use the default): ").strip()
    if not folder_path:
        folder_path = None
    quality = input("Enter audio quality (128, 192, 320) or press Enter for default (320): ").strip()
    if not quality:
        quality = '320'
    download_from_spotify_link(link, folder_path, quality)

if __name__ == "__main__":
    main()

