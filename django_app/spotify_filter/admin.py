from django.contrib import admin

from .models import Artist, Album


class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "spotify_id")
    list_filter = ["genres"]
    search_fields = ["name"]


class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "added_at", "release_date", "popularity")
    list_filter = ["release_date"]
    search_fields = ["title"]


admin.site.register(Artist, ArtistAdmin)
admin.site.register(Album, AlbumAdmin)
