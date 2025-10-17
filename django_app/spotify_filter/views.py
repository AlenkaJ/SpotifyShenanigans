from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from . import spotify_import
from .models import Artist


def index(request):
    return render(request, "spotify_filter/index.html")


def importing(request):
    spotify_import.import_from_spotify()
    messages.success(request, "Spotify data imported successfully.")
    return HttpResponseRedirect(reverse("spotify_filter:dashboard"))


class DashboardView(generic.ListView):
    template_name = "spotify_filter/dashboard.html"

    def get_queryset(self):
        return Artist.objects.all()
