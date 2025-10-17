from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from . import spotify_import
from .models import Artist, Album


def index(request):
    return render(request, "spotify_filter/index.html")


def importing(request):
    spotify_import.import_from_spotify()
    messages.success(request, "Spotify data imported successfully.")
    return HttpResponseRedirect(reverse("spotify_filter:dashboard"))


class DashboardView(generic.ListView):
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
