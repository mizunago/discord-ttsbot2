import discord
import os
from datetime import datetime,timedelta,timezone
from discord import app_commands
from dotenv import load_dotenv
from polly import Polly
import regex
import asyncio

load_dotenv()

TOKEN = os.environ.get('TOKEN')
POLLY_VOICE_ID = os.environ.get('POLLY_VOICE_ID')
UTC = timezone(timedelta(hours=0), "UTC")

intents = discord.Intents.all()
intents.members = True
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
command = app_commands.CommandTree(client)
# 管理者ID
OWNER_ID = 311482797053444106
polly = Polly()
last_user = None

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

# TODO: on_thread_create を使って書き直してね☆
# https://discordpy.readthedocs.io/ja/latest/api.html?highlight=on_message#discord.on_thread_create
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


    await command.tree.sync()

@command.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        await command.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

@command.command(name='connect', description='ボイスチャットに読み上げBOTを呼びます')
async def connect(ctx: discord.Interaction):
    # BOT からの呼び出しには無視
    if ctx.user.bot:
        return

    # ボイスチャットをつないでいない人からの呼び出しにはエラーを返す
    if ctx.user.voice is None:
        await ctx.response.send_message(f"ボイスチャットチャンネルに接続してからコマンドを実行してください")
        return

    # 人数無制限以外は入らない
    if ctx.user.voice.channel.user_limit != 0:
        await ctx.response.send_message(f"人数無制限のVCで呼び出してください")
        return

    # 呼び出した人のいるボイスチャットに接続する
    await ctx.user.voice.channel.connect()
    await ctx.response.send_message(f"ボイスチャンネル: {ctx.user.voice.channel.name} に接続しました")

@command.command(name='disconnect', description='ボイスチャットから読み上げBOTを切断します')
async def disconnect(ctx: discord.Interaction):
    for voice in client.voice_clients:
        if ctx.user.voice.channel.name == voice.channel.name:
            await voice.disconnect()
            await ctx.response.send_message(f"ボイスチャンネル: {ctx.user.voice.channel.name} から切断しました")

@client.event
async def on_message(message: discord.Message):
    global last_user
    # メッセージの送信者がbotだった場合は無視する
    if message.author.bot:
        return

    # テキストチャンネルとボイスチャンネルの名前が一致しない場合は何もしない
    for voice in client.voice_clients:
        if message.channel.name != voice.channel.name:
            return

        # 発言者の名前を取得
        user_name = message.author.display_name
        name_regex = regex.compile(r'(?:\p{Hiragana}|\p{Katakana}|[ー－])+')
        matched = name_regex.match(user_name)

        if matched:
            user_name = matched.group()

        body = message.content
        # URL が含まれる場合は処理する
        if 'http' in body:
            body = 'URL 省略'

        # 最近読み上げた人だったら名前を省略
        if last_user == user_name:
           text = f"{body}"
        else:
            text = f"{user_name} さんの発言、{body}"

        # 最後に読み上げた人を記録
        last_user = user_name
        # 音声を生成して再生
        message.guild.voice_client.play(discord.FFmpegPCMAudio(polly.create_voice(text, POLLY_VOICE_ID)))

@client.event
async def on_voice_state_update(member, before, after):
    # BOTがボイスチャットチャンネルに入っているか確認する
    if len(client.voice_clients) == 0:
        return

    await asyncio.sleep(5)  # 退出前に5秒待機する（任意の秒数で設定可能）
    # 自分の入っているボイスチャットが変更になったか調べる
    for voice in client.voice_clients:
        # ボイスチャンネルにBOT以外のメンバーが残っているか確認する
        if len(voice.channel.members) == 1 and voice.channel.members[0] == client.user:
            # BOT以外のメンバーがいなくなった場合、BOTをボイスチャンネルから退出させる
            await voice.disconnect()
            await voice.channel.send(f'{voice.channel.name} から切断しました')

@client.event
async def on_member_join(member: discord.Member):
    for server in client.guilds:
        if not 'Sea of Thieves' in server.name:
            continue

        send_ch = discord.utils.get(server.channels, name=f'サーバー入退室ログ')
        await send_ch.send(f'{member.display_name} <@!{member.id}> さんがサーバーに来ました')

@client.event
async def on_member_remove(member: discord.Member):
    for server in client.guilds:
        if not 'Sea of Thieves' in server.name:
            continue

        send_ch = discord.utils.get(server.channels, name=f'サーバー入退室ログ')
        await send_ch.send(f'{member.display_name} <@!{member.id}> さんがサーバーから出ていきました')

client.run(TOKEN)
