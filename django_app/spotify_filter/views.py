from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django_tables2 import SingleTableView

from .models import Artist, Album
from .tables import ArtistTable
from .tasks import import_spotify_data_task


def index(request):
    return render(request, "spotify_filter/index.html")


def importing(request):
    import_spotify_data_task.delay()
    messages.info(
        request, "Spotify data import has been started. This may take a while."
    )
    return render(request, "spotify_filter/importing.html")


class DashboardView(SingleTableView):
    model = Artist
    table_class = ArtistTable
    template_name = "spotify_filter/dashboard.html"
    context_object_name = "artist_list"

    def get_queryset(self):
        return Artist.objects.all()


class ArtistDetailView(generic.DetailView):
    model = Artist
    template_name = "spotify_filter/artist_detail.html"

    def get_queryset(self):
        return Artist.objects.all()


class AlbumDetailView(generic.DetailView):
    model = Album
    template_name = "spotify_filter/album_detail.html"

    def get_queryset(self):
        return Album.objects.all()
