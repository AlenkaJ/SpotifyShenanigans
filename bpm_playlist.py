import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
from math import ceil


class SavedTracksReader:
    def __init__(self, spotify, batchsize=50):
        self.spotify = spotify
        self.batchsize = batchsize

    def __iter__(self):
        self.batchnum = 0
        return self

    def __next__(self):
        results = sp.current_user_saved_tracks(
            limit=self.batchsize, offset=self.batchnum * self.batchsize
        )
        items = results["items"]
        tracks = [item["track"] for item in items]
        names = [track["name"] for track in tracks]
        ids = [track["id"] for track in tracks]
        print(names)
        self.batchnum += 1
        return ids


class PlaylistTrackReader:
    def __init__(self, spotify, playlist_list=[], batchsize=50):
        self.spotify = spotify
        self.batchsize = batchsize
        playlists = self.spotify.current_user_playlists()["items"]  # batches!
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
        self.batchnum = 0
        self.playlist_iterator = iter(zip(self.playlist_ids, self.playlist_batchnums))
        self.current_playlist_id = None
        self.current_playlist_batchnum = None
        return self

    def __next__(self):
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


def features_filter(ids: list, features_bounds):
    """implement extraction of track ids based on given feature bounds"""
    features = sp.audio_features(tracks=ids)
    # TODO


def make_local_playlist(name, track_ids_list, spotify, description=""):
    user = spotify.current_user()
    playlist = spotify.user_playlist_create(
        user["id"], name, public=False, collaborative=False, description=description
    )
    spotify.playlist_add_items(playlist["id"], track_ids_list)


"""TODO:
rewrite using iterators:
ptr = PlaylistTrackReader([....])
iter_ptr = iter(ptr)
batch_ids = next(iter_ptr)
...
"""

if __name__ == "__main__":
    scopes = ["user-library-read", "playlist-modify-private"]
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

    limit = 50
    total = sp.current_user_saved_tracks(limit=1)["total"]
    batches = ceil(total / limit)
    batches = 30

    lower_bound = 120
    upper_bound = 125
    dance_bound = 0.4

    chosen_ids = []
    energy_list = []
    for i in range(batches):
        results = sp.current_user_saved_tracks(limit=limit, offset=i * limit)
        items = results["items"]
        tracks = [item["track"] for item in items]
        names = [track["name"] for track in tracks]
        ids = [track["id"] for track in tracks]
        features = sp.audio_features(tracks=ids)
        # print(features[0].keys())

        for id, feature, name in zip(ids, features, names):
            if feature is not None:
                bpm = feature["tempo"]
                dance = feature["danceability"]
                energy = feature["energy"]
                positivity = feature["valence"]
                duration = feature["duration_ms"]
                if lower_bound < bpm < upper_bound and dance > dance_bound:
                    print(name, energy, positivity)
                    chosen_ids.append(id)
                    energy_list.append(energy)

    sorted_ids = [
        id
        for energy, id in sorted(zip(energy_list, chosen_ids), key=lambda pair: pair[0])
    ]

    make_local_playlist(f"BPM{lower_bound}-{upper_bound}", sorted_ids)
