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

    # list_of_genres = sp.recommendation_genre_seeds()[
    #    "genres"
    # ]  # options usable for sp.recommendations
    albums = retrieve_albums()

    # DUMP SOME DATA TO JSON TO AVOID PROMPTING SPOTIFY TOO MUCH WHEN FIGURING THINGS OUT
    # with open("albums_list.json", "w") as jsonfle:
    #    json.dump(albums, jsonfle, indent=6)

    # with open("albums_list.json", "r") as jsonfle:
    #     albums = json.load(jsonfle)

    # creating albums and artists databases in pandas first
    albums_database_header_dict = {
        "spotify_id": [],
        "name": [],
        "artists": [],
        "total_tracks": [],
        "release_date": [],
        "added_at": [],
        "popularity": [],
    }
    artists_database_header_dict = {
        "spotify_id": [],
        "name": [],
    }
    albums_pandas_df = pd.DataFrame(albums_database_header_dict)
    artists_pandas_df = pd.DataFrame(artists_database_header_dict)

    for album_entry in albums:
        album = album_entry["album"]
        # add new row to the dataframe representing the album
        albums_new_row = {
            "spotify_id": album["id"],
            "name": album["name"],
            "artists": [artist["name"] for artist in album["artists"]],
            "total_tracks": album["total_tracks"],
            "release_date": album["release_date"],
            "added_at": album_entry["added_at"],
            "popularity": album["popularity"],
        }
        albums_pandas_df = albums_pandas_df._append(albums_new_row, ignore_index=True)

        # loop over the artists and add them to the artists dataframe
        for artist in album["artists"]:
            artists_new_row = {
                "spotify_id": artist["id"],
                "name": artist["name"],
            }
            artists_pandas_df = artists_pandas_df._append(
                artists_new_row, ignore_index=True
            )
            artists_pandas_df.drop_duplicates(inplace=True, ignore_index=True)

    # add genres to the artists dataframe
    artists_list = retrieve_artists_by_id(artists_pandas_df["spotify_id"])
    genres = [artist["genres"] for artist in artists_list]
    artists_pandas_df.insert(2, "genres", genres, False)

    # print(albums_pandas_df)
    # print(artists_pandas_df)
    albums_pandas_df.to_csv("albums.csv")
    artists_pandas_df.to_csv("artists.csv")

    # duckdb magic - initialize database
    con = duckdb.connect("albums_database.db")
    con.execute("CREATE TABLE albums AS SELECT * FROM albums_pandas_df")
    con.close()
