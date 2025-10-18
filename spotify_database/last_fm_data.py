from alive_progress import alive_bar
from dotenv import load_dotenv
import pandas as pd
import requests
import pylast
import duckdb
import os


def get_artist_mbid_from_musicbrainz(artist_name):
    url = "https://musicbrainz.org/ws/2/artist/"
    params = {"query": f'artist:"{artist_name}"', "fmt": "json", "limit": 1}
    headers = {
        "User-Agent": "BPMplaylists/1.0 (contact@example.com)",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "artists" in data and len(data["artists"]) > 0:
            return data["artists"][0].get("id")
    except Exception as e:
        print(f"MusicBrainz request failed for '{artist_name}': {e}")
        return None


def get_artist_mbid_from_lastfm(artist_name, network):
    try:
        artist = network.get_artist(artist_name)
        mbid = artist.get_mbid()
        return mbid
    except Exception as e:
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
    with alive_bar(len(database_artist["name"]), bar="notes", spinner="waves2") as bar:
        for artist, id in zip(database_artist["name"], database_artist["spotify_id"]):
            mbid = get_artist_mbid_from_lastfm(artist, network)
            if mbid is None:
                mbid = get_artist_mbid_from_musicbrainz(artist)
            if mbid is not None:
                try:
                    last_artist = network.get_artist_by_mbid(mbid)
                    df_row = {
                        "name": artist,
                        "spotify_id": id,
                        "mbid": mbid,
                    }
                    mbid_df = mbid_df._append(df_row, ignore_index=True)
                except Exception as e:
                    print(f"Error retrieving artist {artist} with MBID {mbid}: {e}")
            bar()
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
