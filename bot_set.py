import discord
import logging
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv('TOKEN')

def bot_run():
    bot.run(TOKEN) 

class StaryCat(commands.Bot):
    def __init__(self):
        #初期化
        intents = discord.Intents.all()
        #botがメッセージを読み取れる様にTrue
        intents.members = True
        intents.message_content = True
        
        #@mention か　stray? でコマンドを実行可にする
        super().__init__(
            command_prefix=commands.when_mentioned_or('stray?'),
            intents=intents,
            case_insensitive=True,
            )
        activity=discord.Game("stray?help or /help")
        self.activity = activity

    async def setup_hook(self):
        # Cogの読み込みは on_ready より前、setup_hook で行うのが推奨されている
        for cog in [
            "cogs.events_cog",
            "cogs.help_cog",
            "cogs.form_cog",
            "cogs.voice_cog",
            "cogs.reaction_roles_cog",
            "cogs.reload_cog",
        ]:
            await self.load_extension(cog)
        
    async def on_ready(self):
    # スラッシュコマンドの同期
        guild = discord.Object(id=1139501724499988540)
        bot.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"同期されたコマンド: {[cmd.name for cmd in synced]}")
        await self.change_presence(activity=self.activity)
        print(f'{self.user}が起動しました')


# ログ設定
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# botにStrayCatクラスを代入
bot = StaryCat()