from itertools import count
from math import ceil, inf

from alive_progress import alive_bar


def retrieve_albums(spotify, max_len=inf, offset=0, limit=50):
    """
    Get spotify info for the max_len of user's saved albums
    starting at offset using batches of size limit
    """
    assert limit > 0
    assert max_len > 0
    assert offset >= 0
    albums_list = []
    counter = count(start=0, step=1)
    reading = True
    print("Reading albums ... ")
    while reading:
        batch_num = next(counter)
        print(batch_num)
        batch_offset = offset + limit * batch_num
        batch_limit = min(limit, max_len + offset - batch_offset)
        queue_response = spotify.current_user_saved_albums(
            limit=batch_limit, offset=batch_offset
        )
        albums_list += queue_response["items"]
        if queue_response["next"] is None or len(albums_list) >= max_len:
            reading = False
    return albums_list


def retrieve_artists_by_id(spotify, ids, limit=50):
    """Get spotify info for a list of artists given by ids using batches of size limit"""
    artists = []
    nbatches = ceil(len(ids) / limit)
    print("Reading artists ... ")
    with alive_bar(nbatches, bar="notes", spinner="waves2") as load_bar:
        for i in range(nbatches):
            queue_response = spotify.artists(ids[i * limit : (i + 1) * limit])
            artists += queue_response["artists"]
            load_bar()
    return artists
