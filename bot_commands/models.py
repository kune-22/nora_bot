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
        super().__init__(command_prefix=commands.when_mentioned_or('stray?'),intents=intents)
        activity=discord.Game("stray? | ")
        self.activity = activity
        
    async def on_ready(self):
    # スラッシュコマンドの同期
        await self.tree.sync()
        await self.change_presence(activity=self.activity)
        print(f'{self.user}が起動しました')

# ログ設定
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# botにStrayCatクラスを代入
bot = StaryCat()