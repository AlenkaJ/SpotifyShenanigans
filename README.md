# Spotify Music Library Analysis
   
   Analysis of my personal Spotify library using [DuckDB](https://duckdb.org/) and SQL.

   TODO: add screenshot here
   
   ## Key Questions Explored
   - Which artists dominate my collection?
   - Genre distribution and trends
   - Album release patterns over time
   
   ## Technical Highlights
   - Complex SQL queries with window functions
   - Multi-table joins across artists/albums/tracks
   - DuckDB for efficient local analytics
   
   ## Setup
   If you want to try this notebook for yourself on your Spotify library, follow these steps:
   1. Clone the repository
```bash
      git clone https://github.com/AlenkaJ/SpotifyShenanigans.git
      cd SpotifyShenanigans
```
   2. Create the virtual environment and install requirements
```bash
      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      pip install -r requirements.txt
```
   3. Set up Spotify API credentials
      - Create an app at https://developer.spotify.com/dashboard
      - Create `.env` file with your credentials:
```
        SPOTIPY_CLIENT_ID=your_client_id
        SPOTIPY_CLIENT_SECRET=your_client_secret
        SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```
   5. Initialize the database
```
        python initialize_spotify_database.py
```
   7. Have fun with the notebooks :)
```bash
        jupyter notebook
```

   ## Key findings
   - My library contains a lot of stuff

   ## Tech Stack
   - Python 3.x
   - DuckDB
   - Spotipy (Spotify API)
   - Jupyter Notebook
   - Pandas

   This analysis led to building a full Django web app: [SpotifyDjangoApp](https://github.com/AlenkaJ/SpotifyDjangoApp).
