from dateutil import parser

from spotify_filter.models import Album, Artist, Track, Genre, AlbumTrack
from .api import SpotifyImporter


def import_from_spotify():
    importer = SpotifyImporter()
    albums = importer.retrieve_albums()
    for album_entry in albums:
        album_data = album_entry["album"]
        if Album.objects.filter(spotify_id=album_data["id"]).exists():
            # if it doesn't exist, create it
            album_obj = Album.objects.get(spotify_id=album_data["id"])
            album_obj.title = album_data["name"]
            album_obj.total_tracks = int(album_data["total_tracks"])
            album_obj.release_date = parser.parse(album_data["release_date"])
            album_obj.added_at = parser.parse(album_entry["added_at"])
            album_obj.popularity = int(album_data["popularity"])
            # takes the first image url, seems to be the one with the highest resolution
            album_obj.album_cover = (
                album_data["images"][0]["url"] if album_data["images"] else None
            )
        else:
            # if it exists, update it
            album_obj = Album(
                spotify_id=album_data["id"],
                title=album_data["name"],
                total_tracks=int(album_data["total_tracks"]),
                release_date=parser.parse(album_data["release_date"]),
                added_at=parser.parse(album_entry["added_at"]),
                popularity=int(album_data["popularity"]),
                # takes the first image url, seems to be the one with the highest resolution
                album_cover=(
                    album_data["images"][0]["url"] if album_data["images"] else None
                ),
            )
        album_obj.save()

        # create each artist if they don't exist and link to album
        for artist_data in album_data["artists"]:
            artist_obj, artist_created = Artist.objects.get_or_create(
                spotify_id=artist_data["id"], name=artist_data["name"]
            )
            album_obj.artists.add(artist_obj)
        album_obj.save()

        for track_data in album_data["tracks"]["items"]:
            track_obj, track_created = Track.objects.get_or_create(
                spotify_id=track_data["id"],
                defaults={
                    "title": track_data["name"],
                    "duration_ms": int(track_data["duration_ms"]),
                },
            )
            # create link between album and track with track and disc number
            AlbumTrack.objects.get_or_create(
                album=album_obj,
                track=track_obj,
                defaults={
                    "track_number": int(track_data["track_number"]),
                    "disc_number": int(track_data["disc_number"]),
                },
            )

    # retrieve genres for all artists
    artist_ids = list(Artist.objects.values_list("spotify_id", flat=True))
    for id, artist_data in zip(artist_ids, importer.retrieve_artists_by_id(artist_ids)):
        artist_obj = Artist.objects.get(spotify_id=id)
        for genre_name in artist_data["genres"]:
            genre_obj, created = Genre.objects.get_or_create(name=genre_name)
            artist_obj.genres.add(genre_obj)
