"""Script for creating a duckdb database for playing with Spotify and LastFM data"""

import os

import duckdb
import pandas as pd
import pylast
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from last_fm_data import get_artist_mbid_from_lastfm, get_artist_mbid_from_musicbrainz
from spotify_data import retrieve_albums, retrieve_artists_by_id


if __name__ == "__main__":
    load_dotenv()

    # setup spotify client
    scopes = ["user-library-read", "playlist-modify-private"]
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

    # setup last fm network
    lastfm_api_key = os.getenv("LASTFM_API_KEY")
    lastfm_api_secret = os.getenv("LASTFM_API_SECRET")
    network = pylast.LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret)

    albums = retrieve_albums(sp)

    # creating databases in pandas first
    # database for albums, artists and genres
    albums_database_header_dict = {
        "spotify_id": [],
        "name": [],
        "total_tracks": [],
        "release_date": [],
        "added_at": [],
        "popularity": [],
    }
    artists_database_header_dict = {
        "spotify_id": [],
        "name": [],
    }
    # database linking the databases together
    album_artist_database_header_dict = {
        "album_id": [],
        "artist_id": [],
    }
    artist_genre_database_header_dict = {
        "artist_id": [],
        "genre": [],
    }
    artist_tag_database_header_dict = {
        "mbid": [],
        "tag": [],
        "weight": [],
    }
    # initialize dataframes
    albums_pandas_df = pd.DataFrame(albums_database_header_dict)
    artists_pandas_df = pd.DataFrame(artists_database_header_dict)
    album_artist_pandas_df = pd.DataFrame(album_artist_database_header_dict)
    artist_genre_pandas_df = pd.DataFrame(artist_genre_database_header_dict)
    artist_tag_pandas_df = pd.DataFrame(artist_tag_database_header_dict)

    for album_entry in albums:
        album = album_entry["album"]
        # add new row to the dataframe representing the album
        albums_new_row = {
            "spotify_id": album["id"],
            "name": album["name"],
            "total_tracks": album["total_tracks"],
            "release_date": album["release_date"],
            "added_at": album_entry["added_at"],
            "popularity": album["popularity"],
        }
        albums_pandas_df = albums_pandas_df._append(albums_new_row, ignore_index=True)

        # loop over the artists and add them to the artists dataframe
        for artist in album["artists"]:
            # add artist to the artists dataframe
            artists_new_row = {
                "spotify_id": artist["id"],
                "name": artist["name"],
            }
            artists_pandas_df = artists_pandas_df._append(
                artists_new_row, ignore_index=True
            )
            # drop duplicates in case it is already there
            artists_pandas_df.drop_duplicates(inplace=True, ignore_index=True)

            # add album - artist link to the linking database
            album_artist_new_row = {
                "album_id": album["id"],
                "artist_id": artist["id"],
            }
            album_artist_pandas_df = album_artist_pandas_df._append(
                album_artist_new_row, ignore_index=True
            )

    # go through artists to add more info
    artist_ids = artists_pandas_df["spotify_id"]
    mbids = []
    for sp_id, artist in zip(artist_ids, retrieve_artists_by_id(sp, artist_ids)):
        # add genres to the artists dataframe
        for genre in artist["genres"]:
            artist_genre_new_row = {
                "artist_id": sp_id,
                "genre": genre,
            }
            artist_genre_pandas_df = artist_genre_pandas_df._append(
                artist_genre_new_row, ignore_index=True
            )

        # obtain mbid for each artist and related tags
        mbid = get_artist_mbid_from_lastfm(artist["name"], network)
        if mbid is None:
            mbid = get_artist_mbid_from_musicbrainz(artist["name"])
        mbids.append(mbid)
    artists_pandas_df.insert(1, "mbid", mbids)

    for mbid in artists_pandas_df["mbid"]:
        if mbid is not None:
            try:
                fm_artist = network.get_artist_by_mbid(mbid)
                tags = fm_artist.get_top_tags()
                for tag in tags:
                    artist_tag_new_row = {
                        "mbid": mbid,
                        "tag": str(tag.item),
                        "weight": int(tag.weight),
                    }
                    artist_tag_pandas_df = artist_tag_pandas_df._append(
                        artist_tag_new_row, ignore_index=True
                    )
            except pylast.WSError as e:
                print(f"Last FM did not find artist with mbid {mbid}: {e}")

    # set datatypes in the albums
    albums_pandas_df["spotify_id"] = albums_pandas_df["spotify_id"].astype("string")
    albums_pandas_df["name"] = albums_pandas_df["name"].astype("string")
    albums_pandas_df["total_tracks"] = albums_pandas_df["total_tracks"].astype("int32")
    albums_pandas_df["popularity"] = albums_pandas_df["popularity"].astype("int32")
    albums_pandas_df["release_date"] = pd.to_datetime(
        albums_pandas_df["release_date"], format="mixed"
    )
    albums_pandas_df["added_at"] = pd.to_datetime(
        albums_pandas_df["added_at"], format="mixed"
    )

    # set datatypes in the artists
    artists_pandas_df["spotify_id"] = artists_pandas_df["spotify_id"].astype("string")
    artists_pandas_df["mbid"] = artists_pandas_df["mbid"].astype("string")
    artists_pandas_df["name"] = artists_pandas_df["name"].astype("string")

    # set datatypes of the albums artist link
    album_artist_pandas_df["album_id"] = album_artist_pandas_df["album_id"].astype(
        "string"
    )
    album_artist_pandas_df["artist_id"] = album_artist_pandas_df["artist_id"].astype(
        "string"
    )

    # set datatypes in the artist genres link
    artist_genre_pandas_df["artist_id"] = artist_genre_pandas_df["artist_id"].astype(
        "string"
    )
    artist_genre_pandas_df["genre"] = artist_genre_pandas_df["genre"].astype("string")

    # set datatypes in the artist tags link
    artist_tag_pandas_df["mbid"] = artist_tag_pandas_df["mbid"].astype("string")
    artist_tag_pandas_df["tag"] = artist_tag_pandas_df["tag"].astype("string")
    artist_tag_pandas_df["weight"] = artist_tag_pandas_df["weight"].astype("int")

    albums_pandas_df.to_csv("csvs/albums.csv")
    artists_pandas_df.to_csv("csvs/artists.csv")
    album_artist_pandas_df.to_csv("csvs/album_artist.csv")
    artist_genre_pandas_df.to_csv("csvs/artist_genre.csv")
    artist_tag_pandas_df.to_csv("csvs/artist_tag.csv")

    # duckdb magic - initialize database
    con = duckdb.connect("database.db")
    con.execute("DROP TABLE IF EXISTS albums")
    con.execute("DROP TABLE IF EXISTS artists")
    con.execute("DROP TABLE IF EXISTS album_artist")
    con.execute("DROP TABLE IF EXISTS artist_genre")
    con.execute("DROP TABLE IF EXISTS artist_tag")
    con.execute("CREATE TABLE albums AS SELECT * FROM albums_pandas_df")
    con.execute("CREATE TABLE artists AS SELECT * FROM artists_pandas_df")
    con.execute("CREATE TABLE album_artist AS SELECT * FROM album_artist_pandas_df")
    con.execute("CREATE TABLE artist_genre AS SELECT * FROM artist_genre_pandas_df")
    con.execute("CREATE TABLE artist_tag AS SELECT * FROM artist_tag_pandas_df")
    con.close()
