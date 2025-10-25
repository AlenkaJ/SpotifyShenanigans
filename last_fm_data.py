"""Definition of functions for retrieving data from LastFM and MusicBrainz"""

import pylast
import requests


def get_artist_mbid_from_musicbrainz(artist_name):
    """Send request to MusicBrainz to obtain the mbid for a given artist_name"""
    url = "https://musicbrainz.org/ws/2/artist/"
    params = {"query": f'artist:"{artist_name}"', "fmt": "json", "limit": 1}
    headers = {
        "User-Agent": "BPMplaylists/1.0",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "artists" in data and len(data["artists"]) > 0:
            return data["artists"][0].get("id")
        print(f"MusicBrainz did not find mbid for artist {artist_name}")
        return None
    except Exception as e:
        print(f"MusicBrainz request failed for '{artist_name}': {e}")
        return None


def get_artist_mbid_from_lastfm(artist_name, lastfm_network):
    """Attempt to obtain the mbid for a given_artist name from LastFM"""
    try:
        fm_artist = lastfm_network.get_artist(artist_name)
        fm_mbid = fm_artist.get_mbid()
        return fm_mbid
    except pylast.WSError as e:
        print(f"Error retrieving MBID for artist {artist_name}: {e}")
        return None
