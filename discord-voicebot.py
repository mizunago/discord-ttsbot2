import discord
import os
from datetime import datetime,timedelta,timezone
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')
UTC = timezone(timedelta(hours=0), "UTC")
cmd = '.'

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

fourm_channels = {
    '船員募集': '📄船員募集メイン',
    '質問用フォーラム': '❓過去ログ-質問-ネタバレok',
    '何でもフォーラム': '💬雑談-ネタバレok',
    '実験フォーラム': '実験室',
}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for server in client.guilds:
        if not 'Sea of Thieves' in server.name:
            continue

        # send_ch = discord.utils.get(server.channels, name=f'❓過去ログ-質問-ネタバレok')
        # await send_ch.send(f'過去の質問:')

        # for channel in server.channels:
        #     if channel.type == discord.ChannelType.forum:
        #         async for thread in channel.archived_threads():
        #             #print(f'{channel.name}: {channel.id}')
        #             if not thread is None:
        #                 #print(f'{channel.name} - {thread.name}: {thread.id} {channel.id}')
        #                 if '質問用フォーラム' in channel.name:
        #                     await send_ch.send(f'<#{thread.id}>')

        for channel in server.channels:
            if channel.type == discord.ChannelType.forum:
                print(f'{channel.name}: {channel.id}')

    print('boot finished')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    server = message.guild

    if not 'Sea of Thieves' in server.name:
        return

    print(server.name)
    print(message.channel.name)
    #print(message.channel.type)
    #print(message.channel.created_at)

    # パブリックスレッドじゃなかったら抜ける
    if not message.channel.type == discord.ChannelType.public_thread:
        return

    # フォーラムのスレッドじゃなかったら抜ける
    if not message.channel.parent.type == discord.ChannelType.forum:
        return

    now = datetime.now(UTC)
    # スレッドが作られたばかりじゃない場合は抜ける
    if now - message.channel.created_at < timedelta(seconds=10):
        print(message.channel.created_at)
        print(now)
        print('新規スレッド')
    else:
        #print(message.channel.created_at)
        #print(now)
        #print(now - message.channel.created_at)
        #print('新規スレッドじゃない')
        return

    for k in fourm_channels:
        # print(f'{fourm_channels[k]} に告知します。もし {k} == {message.channel.parent.name} ならね')
        if k in message.channel.parent.name:
            send_ch = discord.utils.get(message.guild.text_channels, name=fourm_channels[k])
            await send_ch.send(f'{message.author.mention} が <#{message.channel.id}> だってよ！気になるヤツはいるかい？')

client.run(TOKEN)


