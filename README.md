# Spotload
Download Spotify songs/albums/playlist/artists
# Basic Installation
1. Download Spotload.zip at [releases](https://github.com/MilkyBoiVR/Spotload/releases) and unzip the file
2. Create your own [Spotify Developer](https://developer.spotify.com/dashboard) app and enter the credentials
```
SPOTIPY_CLIENT_ID=your spotify client ID here
SPOTIPY_CLIENT_SECRET=your spotify client secret here
```
# Development Installation
1. Download all necessary files like `Spotload.py` and `credentials.txt`
2. Install Python and run following command to install requirements
```
pip install spotipy yt-dlp
```
3. Create your own [Spotify Developer](https://developer.spotify.com/dashboard) app and enter the credentials
```
SPOTIPY_CLIENT_ID=your spotify client ID here
SPOTIPY_CLIENT_SECRET=your spotify client secret here
```
4. Upload any updates to the page to be reviewed and accepted
# Upcoming Features
## CLI Usage
### `spotload {song/album/playlist/artist}`
Download any Spotify song/album/playlist/artist
## Additional Arguments
Allow the following arguments for the command `spotload {song/album/playlist/artist}`
### `--path {your path}`
Path to download the music file/folder
### `list`
Path to a file that has a list of Spotify song/album/playlist/artist links
### `--quality`
Allows you to set the audio quality in kbps
### `--search`
Search for a specific song with keywords and download it
### `help`
Allows users to use `spotload help` which returns a list of available arguments and options
