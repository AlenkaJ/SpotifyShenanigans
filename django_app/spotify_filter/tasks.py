from celery import shared_task
from .spotify_import.import_logic import import_from_spotify


@shared_task
def import_spotify_data_task():
    import_from_spotify()
