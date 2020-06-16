import logging
import os
from datetime import datetime, timedelta
import threading
from aiogram import types
from aiogram.types import ParseMode
from pytube import YouTube
import uuid

from timeloop import Timeloop

logger = logging.getLogger(__name__)


class PendingVideo:
    def __init__(self, id, time, message):
        self.id = id
        self.time = time
        self.message = message


class TextHandler:
    pendingVideos = []

    async def checkVideos(self):
        print("checking vids")
        if len(self.pendingVideos) > 0:
            firstVideo = self.pendingVideos[0]
            timeDifference = (firstVideo.time - datetime.now()).total_seconds()
            if timeDifference in range(-20, 20):
                await self.__downloadVideo(firstVideo)

    async def handle(self, message: types.Message):
        text = message.text
        if text and ('youtu.be' in text or 'youtube.com' in text):
            await self.__handleYoutubeDownload(message)
        elif text == 'ping':
            await message.reply('pong', reply=False)

    async def __handleYoutubeDownload(self, message: types.Message):
        if len(self.pendingVideos) == 0:
            self.pendingVideos.append(PendingVideo(str(uuid.uuid4()),
                                                   datetime.now(),
                                                   message))
        else:
            self.pendingVideos.append(
                PendingVideo(str(uuid.uuid4()),
                             self.pendingVideos[-1].time + timedelta(seconds=10),
                             message))

    async def __downloadVideo(self, pendingVideo):
        try:
            yt = YouTube(pendingVideo.message.text)
            author = yt.author
            length = yt.length
            title = yt.title
            stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('bitrate').desc().first()
            filesize = stream.filesize
            telegram_audio_limit = 52428800
            if (filesize < telegram_audio_limit and length < 600):
                output_filename = stream.download("downloads")
                with open(output_filename, "rb") as f:
                    await pendingVideo.message.reply_audio(f, duration=length, performer=author, title=title)
                os.remove(output_filename)
            else:
                await pendingVideo.message.reply(
                    "<code>No downloads for 10min+ audio or file size greater than 50M</code>",
                    parse_mode=ParseMode.HTML)
        except Exception as e:
            await pendingVideo.message.reply("I've tried downloading this video but caught the "
                                             "following error: " + str(e) + ".\n\n<b>Please report it to @konnov</b>",
                                             parse_mode=ParseMode.HTML)
        finally:
            for vid in self.pendingVideos:
                if vid.id == pendingVideo.id:
                    self.pendingVideos.remove(vid)
                    return
