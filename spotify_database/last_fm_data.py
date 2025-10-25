import os

import duckdb
import pandas as pd
import pylast
import requests
from alive_progress import alive_bar
from dotenv import load_dotenv


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


if __name__ == "__main__":
    load_dotenv()
    lastfm_api_key = os.getenv("LASTFM_API_KEY")
    lastfm_api_secret = os.getenv("LASTFM_API_SECRET")
    network = pylast.LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret)
    con = duckdb.connect("database.db", read_only=True)

    mbid_database_header = {
        "name": [],
        "spotify_id": [],
        "mbid": [],
    }
    mbid_df = pd.DataFrame(mbid_database_header)

    database_artist = con.sql("SELECT name, spotify_id FROM artists").df()
    with alive_bar(
        len(database_artist["name"]), bar="notes", spinner="waves2"
    ) as load_bar:
        for artist, sp_id in zip(
            database_artist["name"], database_artist["spotify_id"]
        ):
            mbid = get_artist_mbid_from_lastfm(artist, network)
            if mbid is None:
                mbid = get_artist_mbid_from_musicbrainz(artist)
            if mbid is not None:
                df_row = {
                    "name": artist,
                    "spotify_id": sp_id,
                    "mbid": mbid,
                }
                mbid_df = mbid_df._append(df_row, ignore_index=True)
            load_bar()
    con.close()

    # set data types
    mbid_df["spotify_id"] = mbid_df["spotify_id"].astype("string")
    mbid_df["mbid"] = mbid_df["mbid"].astype("string")
    mbid_df["name"] = mbid_df["name"].astype("string")

    mbid_df.to_csv("csvs/mbid.csv")

    # duckdb magic - add mbid table
    con.close()
    con = duckdb.connect("database.db")
    con.execute("DROP TABLE IF EXISTS artist_mbid")
    con.execute("CREATE TABLE artist_mbid AS SELECT * FROM mbid_df")
