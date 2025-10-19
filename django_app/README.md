a server needs to be running for the site to work:
(browsing existing dashboard etc works)
```
python manage.py runserver
```

Celery needs to be running in the background for the spotify loading to work properly - it runs background task:
```
celery -A analytics_site worker -l info --pool=solo
```

(run each of those in separate cmd)