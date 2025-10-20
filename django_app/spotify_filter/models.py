from django.db import models
from django.utils import timezone


class Artist(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, verbose_name="Artist Name")
    genres = models.ManyToManyField(
        "Genre", related_name="artists", verbose_name="Genres"
    )

    def __str__(self):
        return self.name

    @property
    def spotify_link(self):
        return f"https://open.spotify.com/artist/{self.spotify_id}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    artists = models.ManyToManyField(
        "Artist",
        related_name="albums",
        verbose_name="Album Artists",
    )
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
    albums = models.ManyToManyField(Album, through="AlbumTrack", related_name="tracks")
    duration_ms = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    @property
    def spotify_link(self):
        return f"https://open.spotify.com/track/{self.spotify_id}"


class AlbumTrack(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    track_number = models.IntegerField()
    disc_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ("album", "track")
        ordering = ["disc_number", "track_number"]
