import logging
import os
import re
from typing import NamedTuple

import yt_dlp
from mutagen.easyid3 import EasyID3

logger = logging.getLogger(__name__)

DOWNLOAD_OPTIONS = {
    "outtmpl": "%(id)s.%(ext)s",
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }
    ],
}


class File(NamedTuple):
    filename: str
    artist: str
    title: str
    url: str


async def get_metadata_local(result):
    artist = result.get("artist", None)
    if artist:
        artists = artist.split(", ")
        artist = ", ".join(sorted(set(artists), key=lambda x: artists.index(x)))
    title = result.get("title") or result.get("alt_title")
    try:
        if artist is None and " - " in title:
            artist = title.split(" - ")[0]
            title = title.split(" - ")[-1]
    except IndexError:
        artist = None
        title = result.get("title") or result.get("alt_title")
    return artist, title


async def get_metadata(url):
    logger.info(f"Downloading metadata for {url}")
    with yt_dlp.YoutubeDL({"noplaylist": True}) as ydl:
        result = ydl.extract_info(url, download=False)
    return await get_metadata_local(result)


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
    with yt_dlp.YoutubeDL(DOWNLOAD_OPTIONS) as ydl:
        result = ydl.extract_info(url, download=True)
        if 'entries' in result:
            info = result['entries'][0]
        else:
            info = result
        artist, title = await get_metadata_local(info)
        filename = f"{info['id']}.mp3"
        if os.path.exists(filename):
            return File(filename, artist, title, url), 0
        raise FileNotFoundError(f"{filename} not found")


async def download_playlist(url, send_message=None):
    """Download each video in the playlist and return the information as a list of tuples"""
    with yt_dlp.YoutubeDL({"extract_flat": True}) as ydl:
        info = ydl.extract_info(url)
        playlist_title = info.get("title")
        if playlist_title and send_message:
            await send_message(f"Downloading playlist: {playlist_title} ({info.get('playlist_count')} tracks)")
        for entry in info['entries']:
            yield await download_single_url(entry["url"])


async def parse_message_for_urls(message):
    urls = re.findall(r"https://\S+", message)
    for url in urls:
        yield url


async def download_url_list(message, send_message=None):
    async for url in parse_message_for_urls(message):
        if "playlist" in url:
            async for file, exit_code in download_playlist(url, send_message):
                if not exit_code:
                    yield file
                yield url
        else:
            file, exit_code = await download_single_url(url)
            if not exit_code:
                yield file
            yield url


if __name__ == "__main__":
    import asyncio
    import sys

    asyncio.run(download_single_url(sys.argv[1]))
