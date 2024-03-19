import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
from math import ceil

scopes = ["user-library-read", "playlist-modify-private"]
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

limit=50
total = sp.current_user_saved_tracks(limit=1)["total"]
batches = ceil(total/limit)
#batches = 30

lower_bound=120
upper_bound=125
dance_bound = 0.4


chosen_ids = []
energy_list = []
for i in range(batches):
    results = sp.current_user_saved_tracks(limit=limit, offset=i*limit)
    items = results["items"]
    tracks = [item["track"] for item in items]
    names = [track["name"] for track in tracks]
    ids = [track["id"] for track in tracks]
    #features = [sp.audio_features(id)[0] for id in ids]
    features = sp.audio_features(tracks=ids)
    #print(features[0].keys())

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

sorted_ids = [id for energy, id in sorted(zip(energy_list, chosen_ids), key=lambda pair: pair[0])]
user = sp.current_user()
playlist = sp.user_playlist_create(user["id"], "BPM120-125", public=False, collaborative=False, description="")
sp.playlist_add_items(playlist["id"], sorted_ids)
