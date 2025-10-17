from django.db import models
from django.utils import timezone


class Artist(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    albums = models.ManyToManyField("Album")
    genres = models.ManyToManyField("Genre")

    def __str__(self):
        return self.name


class Album(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    total_tracks = models.IntegerField(default=0)
    release_date = models.DateField(default=timezone.now)
    added_at = models.DateTimeField(default=timezone.now)
    popularity = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
