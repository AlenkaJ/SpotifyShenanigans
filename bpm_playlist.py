import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from pprint import pprint
from math import ceil
import sys
import json

default_params = {
    "name": "default_playlist",  # name of the new playlist
    "max_tracks": 50,  # max tracks in the playlist
    "playlist_duration": None,  # maximal duration of the playlist
    "playlists": None,  # where to take tracks - if None, take from saved tracks
    "batchsize": 50,  # Spotify api request batch size
    "sort_feature": None,  # sort playlist based on this feature
    "features_bounds": {  # parameters for track filtering, ref: (https://developer.spotify.com/documentation/web-api/reference/get-audio-features)
        "acousticness": [0, 1],
        "danceability": [0, 1],
        "energy": [0, 1],
        "instrumentalness": [0, 1],
        "liveness": [0, 1],
        "speechiness": [0, 1],
        "valence": [0, 1],
        "key": None,
        "mode": None,
        "tempo": None,
        "time_signature": None,
    },
}


class SavedTracksReader:
    """
    Iterator to retrieve the user's saved tracks from Spotify.

    Attributes:
    - spotify: The Spotify API client.
    - batchsize: Number of tracks to retrieve per batch.

    Methods:
    - __init__: Initializes a SavedTracksReader instance.
    - __iter__: Returns the iterator object.
    - __next__: Retrieves the next batch of track IDs.
    """

    def __init__(self, spotify, batchsize=50):
        """
        Initializes a SavedTracksReader instance.

        Args:
        - spotify: The Spotify API client.
        - batchsize (int): Number of tracks to retrieve per batch. Default is 50.
        """
        self.spotify = spotify
        self.batchsize = batchsize

    def __iter__(self):
        """
        Returns the iterator object.
        """
        self.batchnum = 0
        self.reading = True
        return self

    def __next__(self):
        """
        Retrieves the next batch of track IDs.
        """
        if self.reading is False:
            raise StopIteration
        results = sp.current_user_saved_tracks(
            limit=self.batchsize, offset=self.batchnum * self.batchsize
        )
        items = results["items"]
        tracks = [item["track"] for item in items]
        names = [track["name"] for track in tracks]
        ids = [track["id"] for track in tracks]
        print(names)
        self.batchnum += 1
        if results["next"] is None:
            self.reading = False
        return ids


class PlaylistTrackReader:
    """
    Iterator to retrieve tracks from specified playlists on Spotify.

    Attributes:
    - spotify: The Spotify API client.
    - playlist_list: List of playlist names to retrieve tracks from.
    - batchsize: Number of tracks to retrieve per batch.

    Methods:
    - __init__: Initializes a PlaylistTrackReader instance.
    - __iter__: Returns the iterator object.
    - __next__: Retrieves the next batch of track IDs.
    """

    def __init__(self, spotify, playlist_list=[], batchsize=50):
        """
        Initializes a PlaylistTrackReader instance.

        Args:
        - spotify: The Spotify API client.
        - playlist_list (list): List of playlist names to retrieve tracks from. Default is an empty list.
        - batchsize (int): Number of tracks to retrieve per batch. Default is 50.
        """
        self.spotify = spotify
        self.batchsize = batchsize
        playlists = self.spotify.current_user_playlists()["items"]
        self.playlist_ids = [
            playlist["id"]
            for playlist in playlists
            if playlist["name"] in playlist_list
        ]
        tracks_nums = [
            playlist["tracks"]["total"]
            for playlist in playlists
            if playlist["name"] in playlist_list
        ]
        self.playlist_batchnums = [
            ceil(tracks_num / batchsize) for tracks_num in tracks_nums
        ]

    def __iter__(self):
        """
        Returns the iterator object.
        """
        self.batchnum = 0
        self.playlist_iterator = iter(zip(self.playlist_ids, self.playlist_batchnums))
        self.current_playlist_id = None
        self.current_playlist_batchnum = None
        return self

    def __next__(self):
        """
        Retrieves the next batch of track IDs.
        """
        if (
            self.current_playlist_batchnum is None
            or self.batchnum >= self.current_playlist_batchnum
            or self.current_playlist_id is None
        ):
            self.current_playlist_id, self.current_playlist_batchnum = next(
                self.playlist_iterator
            )
            self.batchnum = 0
        results = self.spotify.playlist_items(
            self.current_playlist_id,
            limit=self.batchsize,
            offset=self.batchnum * self.batchsize,
        )
        items = results["items"]
        tracks = [item["track"] for item in items]
        names = [track["name"] for track in tracks]
        ids = [track["id"] for track in tracks]
        print(names)
        self.batchnum += 1
        return ids


def features_filter(ids: list, features_bounds_dict: dict, spotify):
    """
    Filters track IDs based on specified audio feature bounds.

    Args:
    - ids (list): List of track IDs.
    - features_bounds_dict (dict): Dictionary containing audio feature bounds.
    - spotify: The Spotify API client.

    Returns:
    - filtered_ids (list): Filtered list of track IDs.
    - total_duration (int): Total duration of filtered tracks in milliseconds.
    """
    tracks_feature_list = spotify.audio_features(tracks=ids)
    # filter tracks that Spotify doesn't provide features for
    filtered_zip = [
        (id, features)
        for id, features in zip(ids, tracks_feature_list)
        if features is not None
    ]
    for feature_name in features_bounds_dict.keys():
        feature_bounds = features_bounds_dict[feature_name]
        if type(feature_bounds) == list:
            lower, upper = feature_bounds
            if lower is not None:
                filtered_zip = [
                    (id, features)
                    for id, features in filtered_zip
                    if features[feature_name] >= lower
                ]
            if upper is not None:
                filtered_zip = [
                    (id, features)
                    for id, features in filtered_zip
                    if features[feature_name] <= upper
                ]

        elif feature_bounds is not None:
            filtered_zip = [
                (id, features)
                for id, features in filtered_zip
                if features[feature_name] == feature_bounds
            ]
    return filtered_zip


def make_local_playlist(name, track_ids_list, spotify, description=""):
    """
    Creates a local playlist on the user's Spotify account.

    Args:
    - name (str): Name of the playlist.
    - track_ids_list (list): List of track IDs to add to the playlist.
    - spotify: The Spotify API client.
    - description (str): Description of the playlist. Default is an empty string.
    """
    if len(track_ids_list) > 0:
        user = spotify.current_user()
        playlist = spotify.user_playlist_create(
            user["id"], name, public=False, collaborative=False, description=description
        )
        spotify.playlist_add_items(playlist["id"], track_ids_list)
    else:
        raise Exception("track_ids_list is empty!")


if __name__ == "__main__":
    load_dotenv()

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as file:
            params = json.load(file)
    else:
        params = default_params

    pprint(params)

    # setup spotify client
    scopes = ["user-library-read", "playlist-modify-private"]
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

    # setup track reader
    if params["playlists"] is None:
        iterator = iter(SavedTracksReader(sp, batchsize=params["batchsize"]))
    else:
        iterator = iter(
            PlaylistTrackReader(sp, params["playlists"], batchsize=params["batchsize"])
        )

    filtered_zip = []
    duration_ms = 0
    # while we don't have enough tracks and there are still some left, read more tracks and filter them by features
    while (
        params["max_tracks"] is None or len(filtered_zip) < params["max_tracks"]
    ) and (
        params["playlist_duration"] is None or duration_ms < params["playlist_duration"]
    ):
        ids_list = next(iterator, None)
        if ids_list is None:
            break
        batch_filtered_zip = features_filter(
            ids_list,
            features_bounds_dict=params["features_bounds"],
            spotify=sp,
        )
        filtered_zip += batch_filtered_zip
        duration_ms += sum(
            [features["duration_ms"] for (id, features) in batch_filtered_zip]
        )

    # sort by a given feature value from smallest to largest
    if params["sort_feature"] is not None:
        filtered_zip = sorted(
            filtered_zip, key=lambda pair: pair[1][params["sort_feature"]]
        )
        print([features[params["sort_feature"]] for (id, features) in filtered_zip])

    # get only the ids
    filtered_ids = [id for (id, features) in filtered_zip]
    # remove duplicates without losing the ordering
    filtered_ids = list(dict.fromkeys(filtered_ids))
    make_local_playlist(params["name"], filtered_ids, spotify=sp)
