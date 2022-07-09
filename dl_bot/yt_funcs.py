import yt_dlp
from mutagen.easyid3 import EasyID3
import logging

logger = logging.getLogger(__name__)

YT_OPTS = {
    'format': 'bestaudio',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
    "noplaylist": True,
}


async def get_metadata(url):
    with yt_dlp.YoutubeDL({"noplaylist": True}) as ydl:
        result = ydl.extract_info(url, download=False)
    artist = result.get('artist')
    title = result.get('title') or result.get('alt_title')
    return artist, title


async def set_tags(filepath, title, artist=None):
    try:
        metatag = EasyID3(filepath)
        metatag['title'] = title
        if artist is not None:
            metatag['artist'] = artist
        metatag.save()
    except Exception as e:
        logger.error(f"Error settings tags: {e}")


async def download_single_url(url):
    artist, title = await get_metadata(url)
    filename = f'{artist + " - " if artist else ""}{title}.mp3'
    opts = YT_OPTS.copy()
    opts['outtmpl'] = filename
    with yt_dlp.YoutubeDL(opts) as ydl:
        exit_code = ydl.download([url])
    await set_tags(filename, title, artist)
    return filename, exit_code


if __name__ == "__main__":
    print(help(yt_dlp.YoutubeDL))
