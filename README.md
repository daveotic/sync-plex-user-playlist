# Sync Plex User Playlists:

This project aims to sync playlists between users in Plex to allow for collaberation on editing playlists similar to other music platforms. It allows both the owner of the playlist and the shared users to add tracks, remove tracks, and edit the playlist summary. There is also an option to allow users to make playlist and add them to the main admin account. This code only syncs playlists between user in your plex server instance and **does not** sync to playlist outside of Plex.

## Requirments:
1. Plex server address
2. Plex token
    - [How to get Plex token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/ "Link to plex support page")

## Instillation:

To run the code you will need docker or dock-compose. The docker images are a available [here](https://hub.docker.com/repository/docker/daveotic/syncuserplaylist/general "Link to docker hub").

### Docker Run:

Include `http://` in PLEX_URL and remove all comments before running command.

~~~ bash
docker run -d \
--name==syncuserplaylist \
-e PLEX_URL=<plex url> \
-e PLEX_TOKEN=<plex token> \
-e PLAYLIST_LIST=<list of playlist to sync> # format playlist1,playlist2 if blank will do all. \
-e USER_LIST=<list of users to sync to> # format user1,user2 if blank will do all. Admin is not needed. \
-e SYNC_USER_CREATED_PLAYLIST=<0 or 1> # 1 to sync a playlist from a user to the admin playlist. 1 is default \
-e RUN_AS_TEST=<0 or 1> # 1 to run as test 0 is default \
-e TIME_BETWEEN_RUNS=<any number of seconds between runs> # default is 1 second between runs. \
--restart unless-stopped \
daveotic/syncuserplaylist:latest
~~~

### Docker-Compose:

Docker-compose should follow this configuration below. You can refrence the [example-docker-compose.yml](example-docker-compose.yml) to set the docker up.

~~~ yml
version: '3.3'
services:
  syncuserplaylist:
    image: daveotic/syncuserplaylist:latest
    container_name: syncuserplaylist
    environment:
      - PLEX_URL=<plex url>
      - PLEX_TOKEN=<plex token>
      - PLAYLIST_LIST=<list of playlist to sync> # format playlist1,playlist2 if blank will do all.
      - USER_LIST=<list of users to sync to> # format user1,user2 if blank will do all. Admin is not needed.
      - SYNC_USER_CREATED_PLAYLIST=<0 or 1> # 1 to sync a playlist from a user to the admin playlist. 1 is default
      - RUN_AS_TEST=<0 or 1> # 1 to run as test 0 is default
      - TIME_BETWEEN_RUNS=<any number of seconds between runs> # default is 1 second between runs.
    restart: unless-stopped
~~~

Once the docker-compose file is created run it with
~~~ bash
docker-compose up
~~~

## Folder Structure:

~~~ bash
SYNC-PLEX-USER-PLAYLIST
├── syncuserplaylist # Folder containing all python scripts
│   ├── utils
│   │   ├── .cache # Folder generated to store all cache files
│   │   ├── cacheplaylist.py
│   │   └── plexsyncplaylist.py
│   │
│   └── run.py
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── dockerfile
├── example-docker-compose.yml
├── LICENSE
├── README.md
└── requirements.txt
~~~

## Suggestions/Issues:

If you are having issues or have suggestions on improvements leave an issue with as much info as you can. Thanks! :)

## Future Changes:

I wasn't able to figure out to do these initially, but going to keep looking into possible solutions.

1. Able to sync playlist uploaded cover art across all users.
2. Able to sync playlist names across all users.