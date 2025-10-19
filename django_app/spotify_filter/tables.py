from django.utils.html import format_html_join, format_html
from django.urls import reverse
import django_tables2 as tables

from .models import Artist


class ArtistTable(tables.Table):
    class Meta:
        model = Artist
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "name",
            "albums",
            "genres",
        )

    def render_name(self, value, record):
        name = value
        return format_html(
            '<a href="{}">{}</a>',
            reverse("spotify_filter:artist_detail", args=[record.id]),
            name,
        )

    def render_albums(self, value):
        albums = value.all()
        return format_html_join(
            "",
            '<p><a href="{}">{}</a></p>',
            (
                (reverse("spotify_filter:album_detail", args=[album.id]), album.title)
                for album in albums
            ),
        )

    def render_genres(self, value):
        genres = value.all()
        return ", ".join([genre.name for genre in genres])
