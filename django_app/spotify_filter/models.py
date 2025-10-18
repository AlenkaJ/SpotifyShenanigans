from django.db import models
from django.utils import timezone


class Album(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    artists = models.ManyToManyField("Artist", related_name="albums")
    total_tracks = models.IntegerField(default=0)
    release_date = models.DateField(default=timezone.now)
    added_at = models.DateTimeField(default=timezone.now)
    popularity = models.IntegerField(default=0)
    album_cover = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def spotify_link(self):
        return f"https://open.spotify.com/album/{self.spotify_id}"


class Track(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    albums = models.ManyToManyField(Album, related_name="tracks")
    track_number = models.IntegerField()
    duration_ms = models.IntegerField()

    def __str__(self):
        return self.title

    @property
    def spotify_link(self):
        return f"https://open.spotify.com/track/{self.spotify_id}"


class Artist(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    genres = models.ManyToManyField("Genre")

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
