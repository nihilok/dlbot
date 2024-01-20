import logging
import os
import re
from typing import NamedTuple

import yt_dlp
from mutagen.easyid3 import EasyID3

from dl_bot.file_operations import sanitise_filename

logger = logging.getLogger(__name__)

YT_OPTS = {
    "format": "bestaudio",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }
    ],
    "extract_flat": True,
}


class File(NamedTuple):
    filename: str
    artist: str
    title: str


async def get_metadata(url):
    logger.info(f"Downloading metadata for {url}")
    with yt_dlp.YoutubeDL({"noplaylist": True}) as ydl:
        result = ydl.extract_info(url, download=False)
    artist = result.get("artist")
    title = result.get("title") or result.get("alt_title")
    try:
        if artist is None and " - " in title:
            artist = title.split(" - ")[0]
            title = title.split(" - ")[-1]
    except IndexError:
        artist = None
        title = result.get("title") or result.get("alt_title")
    logger.info(f"Returning: {artist}, {title}")
    return artist, title


async def get_playlist_metadata(url):
    logger.info(f"Downloading playlist metadata for {url}")
    with yt_dlp.YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
        playlist_title = result.get("title")
        videos_metadata = []
        for entry in result['entries']:
            video_url = entry['url']
            artist, title = await get_metadata(video_url)  # Use the existing get_metadata function
            videos_metadata.append({"artist": artist, "title": title})
    return playlist_title, videos_metadata


async def set_tags(filepath, title, artist=None):
    try:
        metatag = EasyID3(filepath)
        metatag["title"] = title
        if artist is not None:
            metatag["artist"] = artist
        metatag.save()
    except Exception as e:
        logger.error(f"Error settings tags: {e}")


async def download_single_url(url):
    logger.info(f"Downloading {url}")
    artist, title = await get_metadata(url)
    base_name = await sanitise_filename(f'{artist + " - " if artist else ""}{title}')
    outtmpl = f"{base_name}.%(ext)s"
    filename = f"{base_name}.mp3"
    if os.path.exists(filename):
        return filename, artist, title, 0
    opts = YT_OPTS.copy()
    opts["outtmpl"] = outtmpl
    with yt_dlp.YoutubeDL(opts) as ydl:
        exit_code = ydl.download([url])
    return filename, artist, title, exit_code


async def download_playlist(url):
    """Download each video in the playlist and return the information as a list of tuples"""
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        for entry in info['entries']:
            video_url = entry['original_url']
            filename, artist, title, exit_code = await download_single_url(video_url)  # Use the existing download_single_url function
            yield filename, artist, title, exit_code


async def parse_message_for_urls(message):
    urls = re.findall(r"https://\S+", message)
    for url in urls:
        yield url


async def download_url_list(message):
    async for url in parse_message_for_urls(message):
        if "playlist" in url:
            async for filename, artist, title, exit_code in download_playlist(url):
                if not exit_code:
                    yield filename, artist, title
        filename, artist, title, exit_code = await download_single_url(url)
        if not exit_code:
            yield filename, artist, title


if __name__ == "__main__":
    import asyncio
    import sys

    asyncio.run(download_single_url(sys.argv[1]))
