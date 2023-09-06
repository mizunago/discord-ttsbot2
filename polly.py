# -*- coding: utf-8 -*-
import os
from tempfile import gettempdir
from contextlib import closing
import boto3

class Polly:
    def __init__(self):
        # MEMO: 環境変数からAWSアクセス情報を読み出すので、環境変数がないときはエラーになることに注意
        self.client = boto3.client('polly')

    def create_voice(self, text, actor = "Mizuki"):
        response = self.client.synthesize_speech(Text = text, OutputFormat = "mp3", VoiceId = actor)
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                file_path = os.path.join(gettempdir(), "speech.mp3")
                with open(file_path, "wb") as file:
                    file.write(stream.read())
            return file_path
