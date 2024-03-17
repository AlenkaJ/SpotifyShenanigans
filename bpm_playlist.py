import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
from math import ceil

scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


limit=50
total = sp.current_user_saved_tracks(limit=1)["total"]
batches = ceil(total/limit)

lower_bound=120
upper_bound=125

chosen_ids = []
for i in range(batches):
    results = sp.current_user_saved_tracks(limit=limit, offset=i*limit)
    items = results["items"]
    tracks = [item["track"] for item in items]
    names = [track["name"] for track in tracks]
    ids = [track["id"] for track in tracks]
    #features = [sp.audio_features(id)[0] for id in ids]
    features = sp.audio_features(tracks=ids)
    #durations = [feature["duration_ms"] for feature in features]

    for id, feature, name in zip(ids, features, names):
        if feature is not None:
            bpm = feature["tempo"]
            if lower_bound < bpm < upper_bound:
                #print(name)
                chosen_ids.append(id)
