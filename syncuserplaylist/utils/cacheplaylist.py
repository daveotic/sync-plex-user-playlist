import logging
import re
import pandas as pd
import pyarrow.feather as feather
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)


def sanitize_filename(filename):
    """converts a filename to a savable name.

    Args:
        filename str: a string of text.

    Returns:
        str: a string of text as a savable text.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def extract_playlist_info(playlist):
    """searlizes information about each playlist object passed into the function.

    Args:
        playlist obj: playlist object from plexapi

    Returns:
        dict: a dictionary containing information about each playlist and a list of item dictionaries for the tracks in the playlist.
    """
    logging.info("getting playlist info...")
    playlist_info = {
        "title": playlist.title,
        "summary": playlist.summary,
        "playlistType": playlist.playlistType,
        "updatedAt": playlist.updatedAt.isoformat(),
        "items": [],
    }
    for item in playlist.items():
        item_info = {
            "title": item.title,
            "ratingKey": item.ratingKey,
            "type": item.type,
            "librarySectionID": item.librarySectionID,
            "artist": item.artist().title if item.type == "track" else None,
        }
        playlist_info["items"].append(item_info)
    return playlist_info


def save_playlist_to_cache(
    playlist_info,
    playlist
):
    """takes playlist dictonaries and plex api playlist objects and saves the information as feather files for metadata and items/

    Args:
        playlist_info dict: dictionary containing information about a playlist and a list of item dictionaries for the tracks in the playlist
        playlist obj: playlist object from plexapi
    """
    playlist_name = playlist.title
    sanitized_playlist_name = sanitize_filename(playlist_name)
    playlist_cache_filename = os.path.join(
        cache_directory, f"{sanitized_playlist_name}_cache.feather"
    )

    playlist_cache_filename_items = f"{playlist_cache_filename}_items"
    playlist_cache_filename_metadata = f"{playlist_cache_filename}_metadata"
    old_playlist_cache_filename_items = f"{playlist_cache_filename}_items_old"
    old_playlist_cache_filename_metadata = f"{playlist_cache_filename}_metadata_old"

    logging.info(f"saving cache for {playlist_name}...")

    items_df = pd.DataFrame(playlist_info["items"])
    metadata = {
        "title": playlist_info["title"],
        "summary": playlist_info["summary"],
        "playlistType": playlist_info["playlistType"],
        "updatedAt": playlist_info["updatedAt"],
    }
    metadata_df = pd.DataFrame([metadata])

    try:
        if os.path.exists(old_playlist_cache_filename_items):
            logging.info("Removing old item cache file")
            os.remove(old_playlist_cache_filename_items)

        if os.path.exists(old_playlist_cache_filename_metadata):
            logging.info("Removing old metadate cache file")
            os.remove(old_playlist_cache_filename_metadata)

    except Exception as e:
        logging.error(f"The old playlist cache failed to be deleted! Error: {e}")

    try:
        if os.path.exists(playlist_cache_filename_items):
            logging.info("Copying old item cache file")
            os.rename(playlist_cache_filename_items, old_playlist_cache_filename_items)

        if os.path.exists(playlist_cache_filename_metadata):
            logging.info("Copying old metadata cache file")
            os.rename(
                playlist_cache_filename_metadata, old_playlist_cache_filename_metadata
            )

    except Exception as e:
        logging.error(f"The old playlist cache failed to be saved! Error: {e}")

    try:

        if not os.path.exists(old_playlist_cache_filename_items):
            feather.write_feather(items_df, playlist_cache_filename_items)
            os.rename(playlist_cache_filename_items, old_playlist_cache_filename_items)
            feather.write_feather(items_df, playlist_cache_filename_items)
        else:
            feather.write_feather(items_df, playlist_cache_filename_items)

        if not os.path.exists(old_playlist_cache_filename_metadata):
            feather.write_feather(metadata_df, playlist_cache_filename_metadata)
            os.rename(
                playlist_cache_filename_metadata, old_playlist_cache_filename_metadata
            )
            feather.write_feather(metadata_df, playlist_cache_filename_metadata)
        else:
            feather.write_feather(metadata_df, playlist_cache_filename_metadata)

    except Exception as e:
        logging.error(f"The playlist {playlist_name} failed to be saved! Error: {e}")


def load_playlist_from_cache(
    playlist,
    load_old,
    is_test
):
    """Takes seralized cached data from feather files and converts them into usable dictionaries

    Args:
        playlist obj: plex api playlist object
        load_old bool: option to load the old playlists or not
        is_test bool: bool indicating whether to run as test

    Returns:
        dict: combined dictionary of playlist information and playlist tracks
    """
    playlist_name = playlist.title
    sanitized_playlist_name = sanitize_filename(playlist_name)

    if not is_test:
        try:
            playlist_cache_filename = os.path.join(
                cache_directory, f"{sanitized_playlist_name}_cache.feather"
            )
            if load_old:
                items_df = feather.read_feather(playlist_cache_filename + "_items_old")
                metadata_df = feather.read_feather(
                    playlist_cache_filename + "_metadata_old"
                )
            else:
                items_df = feather.read_feather(playlist_cache_filename + "_items")
                metadata_df = feather.read_feather(
                    playlist_cache_filename + "_metadata"
                )

            playlist_info = {
                "title": metadata_df.loc[0, "title"],
                "summary": metadata_df.loc[0, "summary"],
                "playlistType": metadata_df.loc[0, "playlistType"],
                "updatedAt": datetime.fromisoformat(metadata_df.loc[0, "updatedAt"]),
                "items": items_df.to_dict(orient="records"),
            }
            return playlist_info
        except FileNotFoundError:
            logging.error(f"The playlist {playlist_name} failed to be loaded!")
        except Exception as e:
            logging.error(
                f"An error occurred while loading the playlist {playlist_name} from cache! Error: {e}"
            )

def update_playlist_summary(
    playlist_cache,
    target_playlist,
    username,
    is_test
):
    """Takes playlsit dictonary cache and updates the summary in the target playlist based off of it.

    Args:
        playlist_cache dict: dictonary of playlist data
        target_playlist obj: plex api playlist object
        username obj: plex api username object
        is_test bool: bool indicating whether to run as test

    Returns:
        obj: updated playlsit object with newe summary.
    """
    if playlist_cache["summary"]:
        try:
            if not is_test:
                target_playlist.editSummary(playlist_cache["summary"])
            if not target_playlist.summary.strip():
                print(
                    f"Adding summary '{playlist_cache['summary']}' to '{target_playlist.title}'"
                )
            else:
                print(
                    f"Updated summary from '{target_playlist.summary}' to '{playlist_cache['summary']}'"
                )
        except:
            print(
                f"Failed to update description for '{username.username or username.title}' '{target_playlist.title}' playlist."
            )
    return target_playlist


def update_plex_from_cache(
    plex,
    playlist_cache,
    target_playlist,
    username,
    is_test
):
    """Updates plex playlist object from the cache by searching for the track by ID.

    Args:
        plex obj: plexserver endpoint
        playlist_cache dict: playlists cache dictionary
        target_playlist obj: plex api playlist object
        username obj: plex api username object
        is_test bool: bool indicating whether to run as test

    Returns:
        obj: updated plex playlist object with new tracks and with tracks that are no longer in updated playlist
    """
    cache_tracklist = []

    if not is_test:
        for cachedtrack in playlist_cache["items"]:
            plex_track_obj = plex.library.sectionByID(
                cachedtrack["librarySectionID"]
            ).searchTracks(id=cachedtrack["ratingKey"])
            for track in plex_track_obj:
                cache_tracklist.append(track)
                if track not in target_playlist.items():
                    try:
                        target_playlist.addItems(track)
                        print(
                            f"Adding '{track.title}' by '{track.artist().title}' to '{username.username or username.title}' '{target_playlist.title}' playlist."
                        )
                    except:
                        print(
                            f"Failed to add '{track.title}' by '{track.artist().title}'"
                        )
        for plextrack in target_playlist.items():
            if plextrack not in cache_tracklist:
                try:
                    target_playlist.removeItems(plextrack)
                    print(
                        f"Removing '{plextrack.title}' by '{plextrack.artist().title}' from '{username.username or username.title}' '{target_playlist.title}' playlist."
                    )
                except:
                    print(
                        f"Failed to remove {plextrack.title}' by '{plextrack.artist().title}' from '{username.username or username.title}' '{target_playlist.title}' playlist."
                    )

        if target_playlist.summary != playlist_cache["summary"]:
            update_playlist_summary(playlist_cache, target_playlist, username, is_test)
    else:
        logging.info("If not in test mode would update plex playlist from cache file")
    return target_playlist

# Key def to call

def check_for_playlist_cache(playlist):
    """ Checks if the playlist feather cache files exsit already for both metadata and items cache

    Args:
        playlist obj: plex api playlist object

    Returns:
       bool: returns True or False depending if all cahce files exist for the playlist
    """
    playlist_name = playlist.title
    sanitized_playlist_name = sanitize_filename(playlist_name)
    playlist_cache_filename = os.path.join(
        cache_directory, f"{sanitized_playlist_name}_cache.feather"
    )

    playlist_cache_filename_items = f"{playlist_cache_filename}_items"
    playlist_cache_filename_metadata = f"{playlist_cache_filename}_metadata"
    old_playlist_cache_filename_items = f"{playlist_cache_filename}_items_old"
    old_playlist_cache_filename_metadata = f"{playlist_cache_filename}_metadata_old"
    cache_files_list, check_list = [
        playlist_cache_filename_items,
        playlist_cache_filename_metadata,
        old_playlist_cache_filename_items,
        old_playlist_cache_filename_metadata,
    ], []

    try:
        for cache_file_path in cache_files_list:
            check = os.path.exists(cache_file_path)
            check_list.append(check)

        check_results = all(check_list)

        return check_results

    except Exception as e:
        logging.error(
            f"An error occurred while loading the playlist {playlist_name} from cache! Error: {e}"
        )

def make_playlist_cache(
    playlist,
    is_test
):
    """Runs the extract_playlist_info function and save_playlist_to_cache funtion on the playlist obj passed through.

    Args:
        playlist obj: Plex api playlist object
        is_test bool: bool indicating whether to run as test
    """
    if not is_test:
        playlist_info = extract_playlist_info(playlist=playlist)
        save_playlist_to_cache(playlist_info=playlist_info, playlist=playlist)
    print(f"Created cache for {playlist.title}")


def delete_old_cache(
    playlist_list,
    is_test
):
    """Takes playlist list and compares to all cached feather files. If a cached playlist is no longer in the list it deletes the feather files.

    Args:
        playlist_list list: list of playlists titles
        is_test bool: bool indicating whether to run as test
    """
    cache_list = []
    if not is_test:
        try:
            for playlist_name in playlist_list:
                file_name = f"{sanitize_filename(playlist_name)}_cache.feather"
                cache_list.append(file_name + "_items")
                cache_list.append(file_name + "_items_old")
                cache_list.append(file_name + "_metadata")
                cache_list.append(file_name + "_metadata_old")

            for cache_file in os.listdir(cache_directory):
                cache_file_path = os.path.join(cache_directory, cache_file)
                if cache_file not in cache_list:
                    try:
                        if os.path.isfile(cache_file_path):
                            print(f"Removing {cache_file} from cache storage")
                            os.remove(cache_file_path)
                    except Exception as e:
                        logging.error(
                            f"An error occurred while removing old playlist! Error: {e}"
                        )
                else:
                    print(
                        f"Playlist for {cache_file} cache still in playlsit sync list, skipping..."
                    )

        except Exception as e:
            logging.error(f"An error occurred while removing old playlist! Error: {e}")
    else:
        logging.info("In test mode no cache needs to be removed.")


def compare_tracks_to_cache(
    plexserver,
    playlist,
    username,
    is_test
):
    """Logic test to compare tracks in cache playlist file to the tracks in the playlist by track ID.
    If the plex playlist needs new tracks or tracks removed it runs update_plex_from_cache.
    If the playlist cache needs to be updated then it runs make_playlist_cache.


    Args:
        plexserver obj: plexserver endpoint
        playlist obj: plex api playlist object
        username obj: plex api username object
        is_test bool: bool indicating whether to run as test
    """
    if not is_test:
        playlist_name = playlist.title
        logging.info(f"Reading {playlist_name} cache...")
        cached_playlist = load_playlist_from_cache(
            playlist=playlist, load_old=False, is_test=is_test
        )
        logging.info(f"Reading {playlist_name} old cache...")
        old_cached_playlist = load_playlist_from_cache(
            playlist=playlist, load_old=True, is_test=is_test
        )

        cached_track_list, old_cached_track_list = [], []

        for cachedtrack in cached_playlist["items"]:
            plex_track_obj = plexserver.library.sectionByID(
                cachedtrack["librarySectionID"]
            ).searchTracks(id=cachedtrack["ratingKey"])
            for track in plex_track_obj:
                cached_track_list.append(track)

        for cachedtrack in old_cached_playlist["items"]:
            plex_track_obj = plexserver.library.sectionByID(
                cachedtrack["librarySectionID"]
            ).searchTracks(id=cachedtrack["ratingKey"])
            for track in plex_track_obj:
                old_cached_track_list.append(track)

        cache_length = len(cached_track_list)
        old_cache_length = len(old_cached_track_list)
        summary_changed = playlist.summary != cached_playlist["summary"]
        old_summary_changed = playlist.summary == old_cached_playlist["summary"]
        current_track_list = playlist.items()

        if (
            not set(cached_track_list).issubset(set(current_track_list))
            and set(old_cached_track_list).issubset(set(current_track_list))
            or (
                cache_length != len(current_track_list)
                and old_cache_length == len(current_track_list)
            )
            or (summary_changed and old_summary_changed)
        ):
            print("updating plex from cache")
            update_plex_from_cache(
                plex=plexserver,
                playlist_cache=cached_playlist,
                target_playlist=playlist,
                username=username,
                is_test=is_test,
            )
        elif (
            not set(current_track_list).issubset(set(cached_track_list))
            and not set(old_cached_track_list).issubset(set(current_track_list))
            or (
                cache_length != len(current_track_list)
                or old_cache_length != len(current_track_list)
            )
            or (summary_changed and not old_summary_changed)
        ):
            print("the cached playlist needs to be updated")
            make_playlist_cache(
                playlist=playlist,
                is_test=is_test
            )
        else:
            print(f"no changes needed for '{username.username or username.title}'")
    else:
        logging.info(
            "If not in test mode would compare both plex playlist from user/account to cache playlist. Based on set conditions it would update the other playlist accordingly."
        )

# ensures cache directories are in place for script to run properly

cache_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
if not os.path.exists(cache_directory):
    os.makedirs(cache_directory)
