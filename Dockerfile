FROM python:3.8
RUN apt-get update && apt-get install -y \
    locales \
    locales-all \
    libopus-dev \
    libopus0 \
    libsodium-dev \
    software-properties-common \
    libffi-dev libnacl-dev python3-dev
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV LANG ja_JP.UTF-8

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN python -m pip install discord.py python-dotenv

COPY discord-voicebot.py /app/
COPY secret.json /app/
COPY vision.json /app/
COPY twitch_secret.yml /app/
COPY youtube_secret.yml /app/
COPY twitter_secret.yml /app/
CMD ["python", "discord-voicebot.py"]