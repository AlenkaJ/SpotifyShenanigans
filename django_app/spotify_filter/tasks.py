from celery import shared_task
from . import spotify_import


@shared_task
def import_spotify_data_task():
    spotify_import.import_from_spotify()
