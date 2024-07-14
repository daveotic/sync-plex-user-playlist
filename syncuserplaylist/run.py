import logging
import os
from time import sleep
from plexapi.server import PlexServer
from datetime import datetime

# other scripts import
from utils.plexsyncplaylist import sync_playlists

plex_url = os.getenv( "PLEX_URL" )
plex_token = os.getenv( "PLEX_TOKEN" )
playlist_list = [p.strip() for p in os.environ['PLAYLIST_LIST'].split(',')]
user_list = [u.strip() for u in os.environ['USER_LIST'].split(',')]
sync_user_created_playlist = os.getenv( "SYNC_USER_CREATED_PLAYLIST", default=1 ) == "1"
run_as_test = os.getenv( "RUN_AS_TEST", default=0 ) == "1"
try:
    time_between_runs = float(os.getenv( "TIME_BETWEEN_RUNS", default=1 ))
except ValueError:
    time_between_runs = 0

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    while True:
        try:
            logging.info("Starting playlist sync")
            if plex_url and plex_token:
                try:
                    plex = PlexServer(plex_url, plex_token)
                except:
                    logging.error("Plex authorization error")
                    exit()
            else:
                logging.error("Missing Plex Authorization Variables")
                exit()

            sync_playlists(
                plex,
                playlist_list,
                user_list,
                sync_user_created_playlist,
                run_as_test
            )
            if time_between_runs != 0:
                print(f"Done. Running again in {time_between_runs} seconds.")
            print("""
    ======== end of run ========
                """
            )
            sleep(time_between_runs)
        except KeyboardInterrupt:
            print("Script terminated by user.")
            logging.info("Script terminated by user.")
            exit()