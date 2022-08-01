import sys
from typing import List, Tuple

import spotipy
import yt_dlp
from requests_html import HTMLSession
from spotipy import SpotifyOAuth


def main():
    playlist_url = input('Playlist URL: ')
    save_path = input('Full path to save songs to: ')
    tracks = get_playlist_tracks(playlist_url)

    track_urls: List[str] = []
    # In the case of an error, the download is retried later.
    # In the case of a second error for the same track, it is skipped.
    retried_tracks: List[str] = []
    tracks_not_downloaded: List[str] = []
    for index, track in enumerate(tracks):
        percent_done = int(index / len(tracks) * 100)
        sys.stdout.write(f'\rGetting track URLs... {percent_done}%')
        sys.stdout.flush()
        youtube_search_url = get_youtube_search_url(artist_name=track[0],
                                                    track_name=track[1])
        track_url = get_first_result_url(youtube_search_url)
        if track_url:
            track_urls.append(track_url)
        else:
            track_str = ' - '.join(list(track))
            if track_str in retried_tracks:
                tracks_not_downloaded.append(track_str)
            else:
                tracks.append(track)
                retried_tracks.append(track_str)

    sys.stdout.write('\rGetting track URLs... 100%')
    sys.stdout.flush()
    # Adding a new line because of the stdout.flush
    print()

    download_tracks(track_urls, save_path)

    if tracks_not_downloaded:
        print('\nCould not download following tracks:')
        for track in tracks_not_downloaded:
            print(track)


def get_playlist_tracks(playlist_id: str) -> List[Tuple[str, str]]:
    """ Returns the tracks of a playlist as (<artist_name>, <track_name>) """

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope='playlist-modify-private playlist-modify-public'),
        requests_timeout=10,
        retries=10)

    result = sp.playlist_items(
        playlist_id,
        fields='items.track.album.artists, items.track.name',
        additional_types=['track'])

    tracks = [
        (track['track']['album']['artists'][0]['name'], track['track']['name'])
        for track in result['items']]

    return tracks


def get_youtube_search_url(artist_name: str, track_name: str) -> str:
    """
    Returns the URL to a YouTube search for
    the given song by the given artist
    """
    query = f'{artist_name} {track_name}'.replace(' ', '+')
    return f'https://www.youtube.com/results?search_query={query}'


def get_first_result_url(search_url: str) -> str or None:
    """ Returns the URL of the first result of the search """
    session = HTMLSession()
    response = session.get(search_url)
    response.html.render()
    suffix = response.html.xpath(
        '//a[@class="yt-simple-endpoint inline-block style-scope ytd-thumbnail"]/@href',
        first=True)
    if not suffix:
        return None
    url = str(('https://www.youtube.com' + suffix))
    return url


def download_tracks(urls: List[str], save_path: str):
    print('Downloading tracks...\n')

    ydl_opts = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

    print('\nDone!')


if __name__ == '__main__':
    main()
