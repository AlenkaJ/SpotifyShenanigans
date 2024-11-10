import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from pprint import pprint
from math import inf, ceil
from itertools import count
from alive_progress import alive_bar
import json
import pandas as pd
import duckdb

# IDEAS FOR LATER:
# top_artists = sp.current_user_top_artists()
# top_tracks = sp.current_user_top_tracks()


def retrieve_albums(max=inf, offset=0, limit=50):
    assert limit > 0
    assert max > 0
    assert offset >= 0
    albums = []
    counter = count(start=0, step=1)
    reading = True
    print("Reading albums ... ")
    while reading:
        batch_num = next(counter)
        print(batch_num)
        batch_offset = offset + limit * batch_num
        batch_limit = min(limit, max + offset - batch_offset)
        queue_response = sp.current_user_saved_albums(
            limit=batch_limit, offset=batch_offset
        )
        albums += queue_response["items"]
        if queue_response["next"] is None or len(albums) >= max:
            reading = False
    return albums


def retrieve_artists_by_id(ids, limit=50):
    artists = []
    nbatches = ceil(len(ids) / limit)
    print("Reading artists ... ")
    with alive_bar(nbatches, bar="notes", spinner="waves2") as bar:
        for i in range(nbatches):
            queue_response = sp.artists(ids[i * limit : (i + 1) * limit])
            artists += queue_response["artists"]
            bar()
    return artists


if __name__ == "__main__":
    load_dotenv()

    # setup spotify client
    scopes = ["user-library-read", "playlist-modify-private"]
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

    albums = retrieve_albums()

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
    # initialize dataframes
    albums_pandas_df = pd.DataFrame(albums_database_header_dict)
    artists_pandas_df = pd.DataFrame(artists_database_header_dict)
    album_artist_pandas_df = pd.DataFrame(album_artist_database_header_dict)
    artist_genre_pandas_df = pd.DataFrame(artist_genre_database_header_dict)

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

    # add genres to the artists dataframe
    artist_ids = artists_pandas_df["spotify_id"]
    for id, artist in zip(artist_ids, retrieve_artists_by_id(artist_ids)):
        for genre in artist["genres"]:
            artist_genre_new_row = {
                "artist_id": id,
                "genre": genre,
            }
            artist_genre_pandas_df = artist_genre_pandas_df._append(
                artist_genre_new_row, ignore_index=True
            )

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
    artists_pandas_df["name"] = artists_pandas_df["name"].astype("string")

    # set datatypes of the albums artist link
    album_artist_pandas_df["album_id"] = album_artist_pandas_df["album_id"].astype(
        "string"
    )
    album_artist_pandas_df["artist_id"] = album_artist_pandas_df["artist_id"].astype(
        "string"
    )

    # set datatypes if the artist genres link
    artist_genre_pandas_df["artist_id"] = artist_genre_pandas_df["artist_id"].astype(
        "string"
    )
    artist_genre_pandas_df["genre"] = artist_genre_pandas_df["genre"].astype("string")

    albums_pandas_df.to_csv("albums.csv")
    artists_pandas_df.to_csv("artists.csv")
    album_artist_pandas_df.to_csv("album_artist.csv")
    artist_genre_pandas_df.to_csv("artist_genre.csv")

    # duckdb magic - initialize database
    con = duckdb.connect("database.db")
    con.execute("CREATE TABLE albums AS SELECT * FROM albums_pandas_df")
    con.execute("CREATE TABLE artists AS SELECT * FROM artists_pandas_df")
    con.execute("CREATE TABLE album_artist AS SELECT * FROM album_artist_pandas_df")
    con.execute("CREATE TABLE artist_genre AS SELECT * FROM artist_genre_pandas_df")
    con.close()
