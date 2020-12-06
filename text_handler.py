import logging
import os
from aiogram import types
from aiogram.types import ParseMode
from youtube_dl import YoutubeDL
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen
from PIL import Image
import config

logger = logging.getLogger(__name__)


# TODO move youtube logic into a separate class
class TextHandler:

    async def handle(self, message: types.Message):
        text = message.text
        if text and (' ' not in text and '\n' not in text) \
                and ('youtu.be' in text
                     or 'youtube.com' in text
                     or 'soundcloud.com' in text):
            await self.__handleYoutubeDownload(message)
        elif text == 'ping':
            await message.reply('pong', reply=False)

    async def __handleYoutubeDownload(self, message: types.Message):
        if not str(message.chat.id) in config.WHITELIST_CHAT_ID:
            return
        try:
            ydl_opts = {
                    'writethumbnail': True,
                    'outtmpl': 'downloads/%(extractor)s_%(id)s.%(ext)s',
                    'format': 'bestaudio',
            }
            ydl = YoutubeDL(ydl_opts)
            info = ydl.extract_info(message.text, download=False)
            audio_url = format(info['url'])
            telegram_audio_limit = 52428800
            request_head = Request(audio_url, method='HEAD')
            audio_filesize = urlopen(request_head).headers['Content-Length']

            if int(audio_filesize) < telegram_audio_limit:
                ydl.download([message.text])
                duration = format(info['duration'])
                extractor = format(info['extractor'])
                title = format(info['title'])
                audio_ext = format(info['ext'])
                webpage_id = format(info['id'])
                webpage_url = format(info['webpage_url'])
                uploader = format(info['uploader'])
                thumbnail_url = format(info['thumbnail'])
                thumbnail_urlpath = urlparse(thumbnail_url).path
                thumbnail_filename = os.path.basename(thumbnail_urlpath)
                thumbnail_ext = thumbnail_filename.split(".")[-1]
                base_filename = "downloads/" + extractor + '_' + \
                    webpage_id + '.'
                output_audiofile = base_filename + audio_ext
                original_thumbnail = base_filename + thumbnail_ext
                output_thumbnail = "downloads/square_thumbnail_" + \
                    webpage_id + ".jpg"
                self.__make_squarethumb(original_thumbnail, output_thumbnail)
                with open(output_audiofile, "rb") as audio, \
                     open(output_thumbnail, "rb") as thumb:
                    await message.reply_audio(audio,
                                              caption="<b><a href=\"" +
                                              webpage_url + "\">" +
                                              title + "</a></b>",
                                              parse_mode=ParseMode.HTML,
                                              duration=int(float(duration)),
                                              performer=uploader,
                                              title=title,
                                              thumb=thumb)
                os.remove(output_audiofile)
                os.remove(original_thumbnail)
                os.remove(output_thumbnail)
            else:
                await message.reply("The audio file has the size of " +
                                    str(audio_filesize) + " bytes. " +
                                    "Bots can currently send files of " +
                                    "any type of only up to 50 MB " +
                                    "in size (52428800 bytes)")
        except Exception as e:
            await message.reply("text handler error: `" + str(e) + "`\\.\n\n" +
                                "*Please report it to @konnov*",
                                parse_mode=ParseMode.MARKDOWN_V2)

    # https://stackoverflow.com/a/52177551
    def __make_squarethumb(self, thumbnail, output):
        original_thumb = Image.open(thumbnail)
        squarethumb = self.__crop_to_square(original_thumb)
        squarethumb.thumbnail((320, 320), Image.ANTIALIAS)
        squarethumb.save(output)

    def __crop_to_square(self, img):
        width, height = img.size
        length = min(width, height)
        left = (width - length)/2
        top = (height - length)/2
        right = (width + length)/2
        bottom = (height + length)/2
        return img.crop((left, top, right, bottom))
