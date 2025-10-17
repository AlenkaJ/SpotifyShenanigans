from django.urls import path

from . import views

app_name = "spotify_filter"
urlpatterns = [
    path("", views.index, name="index"),
    path("importing/", views.importing, name="importing"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("artist/<str:pk>/", views.ArtistDetailView.as_view(), name="artist_detail"),
    path("album/<str:pk>/", views.AlbumDetailView.as_view(), name="album_detail"),
]
