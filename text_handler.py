import io
import logging
import os
from aiogram import types
from aiogram.types import ParseMode
from pytube import YouTube
import uuid

logger = logging.getLogger(__name__)


class TextHandler:

    async def handle(self, message: types.Message):
        text = message.text
        if text and ('youtu.be' in text or 'youtube.com' in text):
            await self.__handleYoutubeDownload(message)
        elif text == 'ping':
            await message.reply('pong', reply=False)

    async def __handleYoutubeDownload(self, message: types.Message):
        try:
            yt = YouTube(message.text)
            stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('bitrate').desc().first()
            output_filename = stream.download("downloads", str(uuid.uuid1()) + ".m4a")
            file = open(output_filename, "rb")
            telegram_audio_limit = 52428800
            file_size = os.path.getsize(output_filename)
            if file_size < telegram_audio_limit:
                await message.reply_audio(io.BytesIO(file.read()),
                                          performer="unknown",
                                          title=stream.title)
            else:
                await message.reply("The linked video has been successfully downloaded, however, its "
                                    "audio file has the size of " + str(file_size) + " bytes. " +
                                    "Bots can currently send files of any type of only up to 50 MB " +
                                    "in size (52428800 bytes)")
            file.close()
            os.remove(output_filename)
        except Exception as e:
            await message.reply("I've tried downloading this video but caught the "
                                "following error: " + str(e) + ".\n\n<b>Please report it to @konnov</b>",
                                parse_mode=ParseMode.HTML)
