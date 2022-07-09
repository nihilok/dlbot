import yt_dlp

YT_OPTS = {
    'format': 'bestaudio',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
    "noplaylist": True,
    "addmetadata": True,
}


async def get_filename(url):
    with yt_dlp.YoutubeDL({"noplaylist": True}) as ydl:
        result = ydl.extract_info(url, download=False)
    artist = result.get('artist')
    title = result.get('title') or result.get('alt_title')
    return f'{artist + " - " if artist else ""}{title if title else "download"}.mp3'


async def download_single_url(url):
    filename = await get_filename(url)
    opts = YT_OPTS
    opts['outtmpl'] = filename
    with yt_dlp.YoutubeDL(opts) as ydl:
        exit_code = ydl.download([url])
    return filename, exit_code


if __name__ == "__main__":
    print(help(yt_dlp.YoutubeDL))
