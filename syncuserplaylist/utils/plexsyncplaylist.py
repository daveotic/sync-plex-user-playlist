
#todo make a list from this list that is a list of the playlist ID and it instead syncs that list so if you rename a playlist it updates.
#todo sync playlist cover photo
#todo add documentation for def

import logging
from time import sleep
from plexapi.exceptions import NotFound
from plexapi.server import PlexServer
from datetime import datetime
import re

# other scripts import
from .cacheplaylist import check_for_playlist_cache
from .cacheplaylist import make_playlist_cache
from .cacheplaylist import compare_tracks_to_cache
from .cacheplaylist import delete_old_cache


def update_playlist_summary(
    updated_playlist,
    target_playlist,
    username,
    is_test
):
    """Takes a playlist from plex and updates the summary to the inputed updated playlist.

    Args:
        updated_playlist obj: playlist object from plexapi
        target_playlist obj: playlist object from plexapi
        username obj: username or account object from plexapi
        is_test bool: bool indicating whether to run as test

    Returns:
        obj: returns target playlist object from plexapi
    """
    if updated_playlist.summary:
        try:
            if not is_test:
                target_playlist.editSummary(updated_playlist.summary)
            if not target_playlist.summary.strip():
                print(
                    f"Adding summary '{updated_playlist.summary}' to '{target_playlist.title}'"
                )
            else:
                print(
                    f"Updated summary from '{target_playlist.summary}' to '{updated_playlist.summary}'"
                )
        except:
            print(
                f"Failed to update description for '{username.username or username.title}' '{target_playlist.title}' playlist."
            )
    return target_playlist

def create_playlist(
    username,
    user_plex,
    playlist,
    is_test
):
    """Create a new playlist for a user in plex who does not have a specific playlist.

    Args:
        username obj: plex user object
        user_plex obj: plexserver object under specific username
        playlist obj: playlist object from plexapi
        is_test bool: bool indicating whether to run as test

    Returns:
        obj: returns plex playlist object
    """
    if not is_test:
        user_plex.createPlaylist(playlist.title, items=playlist.items())
        new_playlist = user_plex.playlist(playlist.title)
        update_playlist_summary(
            updated_playlist=playlist,
            target_playlist=new_playlist,
            username=username,
            is_test=is_test,
        )
        make_playlist_cache(
            playlist=playlist,
            is_test=is_test
        )
    print(f"Created '{playlist.title}' for '{username.username or username.title}'.")
    if is_test:
        print(
            f"'{playlist.title}' summary '{playlist.summary}' would have been copied to new playlist for '{username.username or username.title}'."
        )
    return playlist


def sync_playlists(
    plex,
    playlist_list,
    user_list,
    sync_user_created_playlist,
    run_as_test
):
    """Compares the playlist given in the list to those listed in the for each user in the user list provided. Playlists are then cached and compared against the cache as a way to know when to update to a new change.

    Args:
        plex obj: plex server object
        playlist_list list: list of string names that correspond to playlist names.
        user_list list: list of string names that correspond to user names.
        sync_user_created_playlist bool: bool indicating whether to sync playlist made by users that are not on admin account.
        run_as_test bool: bool indicating whether to run as test
    """
    try:
        delete_old_cache(
            playlist_list=playlist_list,
            is_test=run_as_test
        )
    except Exception as e:
        print(f"Failed to delete old cache: {e}")

    account = plex.myPlexAccount()
    if run_as_test:
        print("Running sync in test mode, no changes will be actually be applied.")

    if not user_list:
        print("No users were specified, so all users will be used.")
        users = account.users()
    else:
        valid_usernames, not_usernames = [], []

        for listed_username in user_list:
            if listed_username in [u.username or u.title for u in account.users()]:
                valid_usernames.append(listed_username)
                users = [account.user(username) for username in valid_usernames]
            else:
                not_usernames.append(listed_username)
        if not_usernames:
            print("These usernames are not valid", *not_usernames, sep=", ")

    if not playlist_list:
        print("No playlist were provided, so all playlist will be synced")
        playlists = plex.playlists()
    else:
        playlist_to_sync, invalid_playlist, new_playlist_from_user = [], [], []
        playlist_names = [p.title for p in plex.playlists()]
        for sync_playlist_title in playlist_list:
            if sync_playlist_title in playlist_names:
                playlist_to_sync.append(sync_playlist_title)
            elif sync_playlist_title not in [
                p.title for p in playlist_to_sync
            ]:
                invalid_playlist.append(sync_playlist_title)
        playlists = [plex.playlist(playlist) for playlist in playlist_to_sync]
        if invalid_playlist:
            print("These playlist names are not valid", *invalid_playlist, sep=", ")

    for user in users:
        user_plex = plex.switchUser(user.username or user.title)

        if playlist_list is None and sync_user_created_playlist:
            user_playlists = user_plex.playlists()
        else:
            try:
                user_playlist_names = [p.title for p in user_plex.playlists()]
                for sync_playlist_title in playlist_list:
                    if (
                        sync_playlist_title in user_playlist_names
                        and sync_user_created_playlist
                        and not sync_playlist_title in playlist_names
                    ):
                        new_playlist_from_user.append(sync_playlist_title)
                user_playlists = [
                    user_plex.playlist(playlist) for playlist in new_playlist_from_user
                ]
            except Exception:
                print(f"Playlist not found in {user.username or user.title} account continuing...")

    try:
        for playlist in playlists:
            if playlist.smart:
                print(f"'{playlist.title}' is a smart playlist skipping...")
            elif not playlist.isAudio:
                print(f"'{playlist.title}' is a not an audio playlist skipping...")
            else:
                try:
                    print(
                        f"'{playlist.title}' found in '{account.username or account.title}' playlist, checking for most updated playlist"
                    )
                    if not check_for_playlist_cache(
                        playlist=playlist
                    ):
                        logging.info("Playlist cache does not exist. Creating...")
                        make_playlist_cache(
                            playlist=playlist,
                            is_test=run_as_test
                        )
                    logging.info(f"Comparing {account.username or account.title}' playlist {playlist.title} to cache")
                    compare_tracks_to_cache(
                        plexserver=plex,
                        playlist=playlist,
                        username=account,
                        is_test=run_as_test
                    )
                    for user in users:
                        user_plex = plex.switchUser(user.username or user.title)

                        try:
                            try:
                                print(
                                    f"'{playlist.title}' found in '{user.username or user.title}' playlist, checking for most updated playlist"
                                )
                                if not check_for_playlist_cache(
                                    playlist=playlist
                                ):
                                    logging.info("Playlist cache does not exist. Creating...")
                                    make_playlist_cache(
                                        playlist=playlist,
                                        is_test=run_as_test
                                    )
                                logging.info(f"Comparing {user.username or user.title}' playlist {playlist.title} to cache")
                                compare_tracks_to_cache(
                                    plexserver=plex,
                                    playlist=user_plex.playlist(playlist.title),
                                    username=user,
                                    is_test=run_as_test
                                )
                            except NotFound:
                                print(
                                    f"Playlist '{playlist.title}' not found for '{user.username or user.title}' adding playlist to users account"
                                )
                                create_playlist(
                                    username=user,
                                    user_plex=user_plex,
                                    playlist=playlist,
                                    is_test=run_as_test,
                                )
                        except:
                            print("No playlist to sync, continuing...")
                except:
                    pass

        if not set(new_playlist_from_user).issubset(set(playlist_names)):
            print( user_playlists )
            try:
                for playlist in user_playlists:
                    if playlist.smart:
                        print(f"'{playlist.title}' is a smart playlist skipping...")
                    elif not playlist.isAudio:
                        print(
                            f"'{playlist.title}' is a not an audio playlist skipping..."
                        )
                    else:
                        print(
                            f"checking for new playlist made by {user.username or user.title}"
                        )
                        print(f"New playlist found '{playlist.title}'!")
                        print(
                            f"Adding playlist '{playlist.title}' to '{account.username or account.title}'..."
                        )
                        create_playlist(
                            username=account,
                            user_plex=plex,
                            playlist=playlist,
                            is_test=run_as_test,
                        )
                        if not check_for_playlist_cache(
                            playlist=playlist
                        ):
                            logging.info("Playlist cache does not exist. Creating...")
                            make_playlist_cache(
                            playlist=playlist,
                            is_test=run_as_test
                    )
            except:
                print(
                    f"Error getting new playlist from '{user.username or user.title}'"
                )
        else:
            print(f"No new sync playlist from '{user.username or user.title}'")
    except:
        print("No playlist to sync, continuing...")

logging.basicConfig(level=logging.INFO)