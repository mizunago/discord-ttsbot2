from discord import Intents, Client, Interaction, Message, Member, FFmpegPCMAudio, ChannelType, app_commands, utils
from discord.app_commands import CommandTree
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from polly import Polly
import regex
import functools
import typing
import asyncio

load_dotenv()

TOKEN = os.environ.get('TOKEN')
POLLY_VOICE_ID = os.environ.get('POLLY_VOICE_ID')
UTC = timezone(timedelta(hours=0), "UTC")
BOT_NAME = os.environ.get('BOT_NAME')

# 管理者ID
OWNER_ID = 311482797053444106

FOURM_CHANNELS = {
    '船員募集': '📄船員募集メイン',
    '質問用フォーラム': '❓過去ログ-質問-ネタバレok',
    '何でもフォーラム': '💬雑談-ネタバレok',
    '実験フォーラム': '実験室',
}

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

# TODO: self で呼んでるので直す
@app_commands.command(name='sync', description='Owner only')
async def sync(interaction: Interaction):
    if interaction.user.id == OWNER_ID:
        await self.tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

@app_commands.command(name="connect", description='ボイスチャットに読み上げBOTを呼びます')
async def connect(ctx: Interaction):
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

    await ctx.response.defer()

    # 呼び出した人のいるボイスチャットに接続する
    await ctx.user.voice.channel.connect()
    await ctx.followup.send(f"ボイスチャンネル: {ctx.user.voice.channel.name} に接続しました")

@app_commands.command(name="disconnect", description='ボイスチャットから読み上げBOTを切断します')
async def disconnect(ctx: Interaction):
    await ctx.response.defer()
    for voice in client.voice_clients:
        if ctx.user.voice.channel.name == voice.channel.name:
            await voice.disconnect()
            await ctx.followup.send(f"ボイスチャンネル: {ctx.user.voice.channel.name} から切断しました")

class MyClient(Client):
    def __init__(self, intents: Intents) -> None:
        super().__init__(intents=intents)
        self.last_user = None
        self.polly = Polly()
        self.tree = CommandTree(self)
        self.tree.add_command(connect)
        self.tree.add_command(disconnect)

    async def setup_hook(self) -> None:
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} command(s)")

    async def on_ready(self):
        print(f'We have logged in as {client.user}')

        #for server in client.guilds:
        #    synced = await self.tree.sync(guild=server)
        #    print(f"Synced {len(synced)} command(s)")
        #    cmds = self.tree.get_commands(guild=server)
        #    print(len(cmds))
        #    print(cmds)

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
                if channel.type == ChannelType.forum:
                    print(f'{channel.name}: {channel.id}')

        print('boot finished')

    @to_thread
    def create_voice(self, text, id):
        return self.polly.create_voice(text, POLLY_VOICE_ID)

    async def talk(self, message):
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
            if self.last_user == user_name:
                text = f"{body}"
            else:
                text = f"{user_name} さんの発言、{body}"

            # 最後に読み上げた人を記録
            self.last_user = user_name
            # 音声を生成
            file_path = await self.create_voice(text, POLLY_VOICE_ID)
            # 再生
            message.guild.voice_client.play(FFmpegPCMAudio(file_path))

    # TODO: on_thread_create を使って書き直してね☆
    # https://discordpy.readthedocs.io/ja/latest/api.html?highlight=on_message#discord.on_thread_create
    async def on_message(self, message: Message):

        await self.talk(message)

        if BOT_NAME != 'jack':
            return

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
        if not message.channel.type == ChannelType.public_thread:
            return

        # フォーラムのスレッドじゃなかったら抜ける
        if not message.channel.parent.type == ChannelType.forum:
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

        for k in FOURM_CHANNELS:
            # print(f'{fourm_channels[k]} に告知します。もし {k} == {message.channel.parent.name} ならね')
            if k in message.channel.parent.name:
                send_ch = utils.get(message.guild.text_channels, name=FOURM_CHANNELS[k])
                await send_ch.send(f'{message.author.mention} が <#{message.channel.id}> だってよ！気になるヤツはいるかい？')

    async def on_voice_state_update(self, member, before, after):
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

    async def on_member_update(self, before: Member, after: Member):
        if POLLY_VOICE_ID != 'Takumi':
            return

        server = after.guild

        send_ch = utils.get(server.channels, name=f'ニックネーム変更履歴')
        if send_ch and before.display_name != after.display_name:
            await send_ch.send(f'{after.name} (<@!{after.id}>) さんがニックネームを変更しました. {before.display_name} => {after.display_name}')

    async def on_member_join(self, member: Member):
        if POLLY_VOICE_ID != 'Takumi':
            return

        server = member.guild

        send_ch = utils.get(server.channels, name=f'サーバー入退室ログ')
        if send_ch:
            await send_ch.send(f'{server.name} にニックネーム: {member.display_name} ユーザー名: {member.name} <@!{member.id}> さんがサーバーに来ました')

    async def on_member_remove(self, member: Member):
        if BOT_NAME != 'jack':
            return
        server = member.guild

        send_ch = utils.get(server.channels, name=f'サーバー入退室ログ')
        if send_ch:
            await send_ch.send(f'{server.name} から ニックネーム: {member.display_name} ユーザー名: {member.name} <@!{member.id}> さんがサーバーから出ていきました')

intents = Intents.all()
intents.members = True
intents.messages = True
intents.message_content = True
client = MyClient(intents=intents)
# tree = CommandTree(client)
# bot = commands.Bot(command_prefix=f"!{BOT_NAME}", intents=intents)

client.run(TOKEN)
