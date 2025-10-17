from math import inf, ceil
from itertools import count
from dateutil import parser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

from .models import Album, Artist, Genre


def import_from_spotify():
    load_dotenv()
    scopes = ["user-library-read", "playlist-modify-private"]
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

    albums = retrieve_albums(sp)
    for album_entry in albums:
        album_data = album_entry["album"]
        if Album.objects.filter(spotify_id=album_data["id"]).exists():
            # if it doesn't exist, create it
            album = Album.objects.get(spotify_id=album_data["id"])
            album.title = album_data["name"]
            album.total_tracks = int(album_data["total_tracks"])
            album.release_date = parser.parse(album_data["release_date"])
            album.added_at = parser.parse(album_entry["added_at"])
            album.popularity = int(album_data["popularity"])
        else:
            # if it exists, update it
            album = Album(
                spotify_id=album_data["id"],
                title=album_data["name"],
                total_tracks=int(album_data["total_tracks"]),
                release_date=parser.parse(album_data["release_date"]),
                added_at=parser.parse(album_entry["added_at"]),
                popularity=int(album_data["popularity"]),
            )
        album.save()

        # create each artist if they don't exist and link to album
        for artist_data in album_data["artists"]:
            artist, artist_created = Artist.objects.get_or_create(
                spotify_id=artist_data["id"], name=artist_data["name"]
            )
            artist.albums.add(album)

    # retrieve genres for all artists
    artist_ids = list(Artist.objects.values_list("spotify_id", flat=True))
    for id, artist_data in zip(artist_ids, retrieve_artists_by_id(sp, artist_ids)):
        artist_obj = Artist.objects.get(spotify_id=id)
        for genre_name in artist_data["genres"]:
            genre_obj, created = Genre.objects.get_or_create(name=genre_name)
            artist_obj.genres.add(genre_obj)


def retrieve_albums(sp, max=inf, offset=0, limit=50):
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


def retrieve_artists_by_id(sp, ids, limit=50):
    artists = []
    nbatches = ceil(len(ids) / limit)
    print("Reading artists ... ")
    for i in range(nbatches):
        print(i)
        queue_response = sp.artists(ids[i * limit : (i + 1) * limit])
        artists += queue_response["artists"]
    return artists
