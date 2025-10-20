from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
import json

from spotify_filter.tasks import import_spotify_data_task
from spotify_filter.models import Album, Artist, Genre, Track, AlbumTrack
from spotify_filter.spotify_import.import_logic import import_from_spotify


class AlbumModelTests(TestCase):
    def test_album_creation(self):
        """Test that an Album instance can be created successfully."""
        album = Album.objects.create(
            spotify_id="12345",
            title="Test Album",
            total_tracks=10,
            release_date="2023-01-01",
            popularity=50,
            album_cover="http://example.com/cover.jpg",
        )
        self.assertEqual(album.spotify_id, "12345")
        self.assertEqual(album.title, "Test Album")
        self.assertEqual(album.total_tracks, 10)
        self.assertEqual(album.release_date, "2023-01-01")
        self.assertEqual(album.popularity, 50)
        self.assertEqual(album.album_cover, "http://example.com/cover.jpg")

    def test_spotify_link_property(self):
        """Test the spotify_link property of the Album model."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        self.assertEqual(album.spotify_link, "https://open.spotify.com/album/12345")

    def test_album_str_method(self):
        """Test the __str__ method of the Album model."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        self.assertEqual(str(album), "Test Album")

    def test_artists_verbose_name(self):
        """Test the verbose_name of the artists field in Album model."""
        album = Album()
        self.assertEqual(album._meta.get_field("artists").verbose_name, "Album Artists")

    def test_album_with_artists(self):
        """Test that artists can be associated with an Album."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        artist1 = Artist.objects.create(spotify_id="a1", name="Artist One")
        artist2 = Artist.objects.create(spotify_id="a2", name="Artist Two")
        album.artists.add(artist1, artist2)
        self.assertEqual(album.artists.count(), 2)
        self.assertIn(artist1, album.artists.all())
        self.assertIn(artist2, album.artists.all())


class ArtistModelTests(TestCase):
    def test_artist_creation(self):
        """Test that an Artist instance can be created successfully."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        self.assertEqual(artist.spotify_id, "a1")
        self.assertEqual(artist.name, "Artist One")

    def test_spotify_link_property(self):
        """Test the spotify_link property of the Artist model."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        self.assertEqual(artist.spotify_link, "https://open.spotify.com/artist/a1")

    def test_artist_str_method(self):
        """Test the __str__ method of the Artist model."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        self.assertEqual(str(artist), "Artist One")

    def test_name_verbose_name(self):
        """Test the verbose_name of the name field in Artist model."""
        artist = Artist()
        self.assertEqual(artist._meta.get_field("name").verbose_name, "Artist Name")

    def test_genres_verbose_name(self):
        """Test the verbose_name of the genres field in Artist model."""
        artist = Artist()
        self.assertEqual(artist._meta.get_field("genres").verbose_name, "Genres")

    def test_artist_with_genres(self):
        """Test that genres can be associated with an Artist."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        genre1 = Genre.objects.create(name="Rock")
        genre2 = Genre.objects.create(name="Pop")
        artist.genres.add(genre1, genre2)
        self.assertEqual(artist.genres.count(), 2)
        self.assertIn(genre1, artist.genres.all())
        self.assertIn(genre2, artist.genres.all())


class GenreModelTests(TestCase):
    def test_genre_creation(self):
        """Test that a Genre instance can be created successfully."""
        genre = Genre.objects.create(name="Rock")
        self.assertEqual(genre.name, "Rock")

    def test_genre_str_method(self):
        """Test the __str__ method of the Genre model."""
        genre = Genre.objects.create(name="Rock")
        self.assertEqual(str(genre), "Rock")


class TrackModelTests(TestCase):
    def test_track_creation(self):
        """Test that a Track instance can be created successfully."""
        track = Track.objects.create(
            spotify_id="t1",
            title="Test Track",
            duration_ms=300000,
        )
        self.assertEqual(track.spotify_id, "t1")
        self.assertEqual(track.title, "Test Track")
        self.assertEqual(track.duration_ms, 300000)

    def test_spotify_link_property(self):
        """Test the spotify_link property of the Track model."""
        track = Track.objects.create(spotify_id="t1", title="Test Track")
        self.assertEqual(track.spotify_link, "https://open.spotify.com/track/t1")

    def test_track_str_method(self):
        """Test the __str__ method of the Track model."""
        track = Track.objects.create(spotify_id="t1", title="Test Track")
        self.assertEqual(str(track), "Test Track")

    def test_track_with_albums(self):
        """Test that albums can be associated with a Track."""
        track = Track.objects.create(spotify_id="t1", title="Test Track")
        album1 = Album.objects.create(spotify_id="12345", title="Album One")
        album2 = Album.objects.create(spotify_id="67890", title="Album Two")
        AlbumTrack.objects.create(album=album1, track=track, track_number=1)
        AlbumTrack.objects.create(album=album2, track=track, track_number=2)
        self.assertEqual(track.albums.count(), 2)
        self.assertIn(album1, track.albums.all())
        self.assertIn(album2, track.albums.all())


class AlbumTrackModelTests(TestCase):
    def test_album_track_creation(self):
        """Test that an AlbumTrack instance can be created successfully."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        track = Track.objects.create(spotify_id="t1", title="Test Track")
        album_track = AlbumTrack.objects.create(
            album=album, track=track, track_number=1, disc_number=1
        )
        self.assertEqual(album_track.album, album)
        self.assertEqual(album_track.track, track)
        self.assertEqual(album_track.track_number, 1)
        self.assertEqual(album_track.disc_number, 1)

    def test_album_track_unique_together(self):
        """Test that the unique_together constraint on AlbumTrack works."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        track = Track.objects.create(spotify_id="t1", title="Test Track")
        AlbumTrack.objects.create(
            album=album, track=track, track_number=1, disc_number=1
        )
        with self.assertRaises(Exception):
            AlbumTrack.objects.create(
                album=album, track=track, track_number=2, disc_number=1
            )

    def test_album_track_ordering(self):
        """Test the ordering of AlbumTrack instances."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        track1 = Track.objects.create(spotify_id="t1", title="Track One")
        track2 = Track.objects.create(spotify_id="t2", title="Track Two")
        track3 = Track.objects.create(spotify_id="t3", title="Track Three")

        at1 = AlbumTrack.objects.create(
            album=album, track=track1, track_number=2, disc_number=1
        )
        at2 = AlbumTrack.objects.create(
            album=album, track=track2, track_number=1, disc_number=1
        )
        at3 = AlbumTrack.objects.create(
            album=album, track=track3, track_number=1, disc_number=2
        )

        album_tracks = AlbumTrack.objects.filter(album=album)
        self.assertEqual(
            list(album_tracks), [at2, at1, at3]
        )  # Ordered by disc_number then track_number


class IndexViewTests(TestCase):
    def test_index_view_status_code(self):
        """Test that the index view returns a 200 status code."""
        response = self.client.get(reverse("spotify_filter:index"))
        self.assertEqual(response.status_code, 200)

    def test_index_view_template(self):
        """Test that the index view uses the correct template."""
        response = self.client.get(reverse("spotify_filter:index"))
        self.assertTemplateUsed(response, "spotify_filter/index.html")


class ImportingViewTests(TestCase):
    def test_importing_view_status_code(self):
        """Test that the importing view returns a 200 status code."""
        response = self.client.get(reverse("spotify_filter:importing"))
        self.assertEqual(response.status_code, 200)

    def test_importing_view_template(self):
        """Test that the importing view uses the correct template."""
        response = self.client.get(reverse("spotify_filter:importing"))
        self.assertTemplateUsed(response, "spotify_filter/importing.html")


class ArtistDetailViewTests(TestCase):
    def test_artist_detail_view_status_code(self):
        """Test that the ArtistDetailView returns a 200 status code."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        response = self.client.get(
            reverse("spotify_filter:artist_detail", args=(artist.id,))
        )
        self.assertEqual(response.status_code, 200)

    def test_artist_detail_view_template(self):
        """Test that the ArtistDetailView uses the correct template."""
        artist = Artist.objects.create(spotify_id="a1", name="Artist One")
        response = self.client.get(
            reverse("spotify_filter:artist_detail", args=(artist.id,))
        )
        self.assertTemplateUsed(response, "spotify_filter/artist_detail.html")


class AlbumDetailViewTests(TestCase):
    def test_album_detail_view_status_code(self):
        """Test that the AlbumDetailView returns a 200 status code."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        response = self.client.get(
            reverse("spotify_filter:album_detail", args=(album.id,))
        )
        self.assertEqual(response.status_code, 200)

    def test_album_detail_view_template(self):
        """Test that the AlbumDetailView uses the correct template."""
        album = Album.objects.create(spotify_id="12345", title="Test Album")
        response = self.client.get(
            reverse("spotify_filter:album_detail", args=(album.id,))
        )
        self.assertTemplateUsed(response, "spotify_filter/album_detail.html")


class DashboardViewTests(TestCase):
    def test_dashboard_view_status_code(self):
        """Test that the DashboardView returns a 200 status code."""
        response = self.client.get(reverse("spotify_filter:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_template(self):
        """Test that the DashboardView uses the correct template."""
        response = self.client.get(reverse("spotify_filter:dashboard"))
        self.assertTemplateUsed(response, "spotify_filter/dashboard.html")

    def test_dashboard_view_context(self):
        """Test that the DashboardView provides the correct context data."""
        artist1 = Artist.objects.create(spotify_id="a1", name="Artist One")
        artist2 = Artist.objects.create(spotify_id="a2", name="Artist Two")
        response = self.client.get(reverse("spotify_filter:dashboard"))
        self.assertIn(artist1, response.context["artist_list"])
        self.assertIn(artist2, response.context["artist_list"])


class ImportSpotifyTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open("spotify_filter/tests/data/albums2.json") as f:
            cls.two_albums = json.load(f)
        with open("spotify_filter/tests/data/artists2.json") as f:
            cls.two_artists = json.load(f)

    @patch("spotify_filter.spotify_import.api.SpotifyImporter.retrieve_artists_by_id")
    @patch("spotify_filter.spotify_import.api.SpotifyImporter.retrieve_albums")
    def test_import_from_spotify_success(
        self,
        mock_retrieve_albums,
        mock_retrieve_artists_by_id,
    ):
        """Test that the import_from_spotify correctly imports data."""
        mock_retrieve_albums.return_value = self.two_albums
        mock_retrieve_artists_by_id.return_value = self.two_artists

        import_from_spotify()

        assert Album.objects.count() == 2
        assert Artist.objects.count() == 2
        assert Track.objects.count() == 25
        assert AlbumTrack.objects.count() == 25


@patch("spotify_filter.tasks.import_from_spotify")
def test_celery_task_runs(mock_import):
    """Test that the import_spotify_data_task calls the import function."""
    import_spotify_data_task()
    mock_import.assert_called_once()
