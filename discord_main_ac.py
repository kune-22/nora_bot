# discord.py をインポート
import discord
#logを保存するためにインポート
import logging

# bot commandを使用するためにインポート
from discord.ext import commands
from discord import app_commands
# modelsから必要なモデルをインポート(botはサーバーを起動するために必要な変数)
from models import bot, Confirm, User, Channel
import models

ch_count = 0

# メッセージが送信された時の処理
@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return
    file_path = "img/ZenlessZoneZero 2024_12_19 23_18_51.png"
    # 通常のメッセージコマンド処理
    
    if message.content.startswith('gyazo'):
            await message.channel.send(file=discord.File(file_path))
    
    # スラッシュコマンドを処理するために、明示的にbot.process_commandsを呼び出す
    await bot.process_commands(message)



# スラッシュコマンドの定義
@bot.tree.command(name="hey", description="Say hello to the bot!")
async def hey(interaction: discord.Interaction):
    await interaction.response.send_message('Hello, World!', ephemeral=True)

#ui.viewでbuttonを作成
        
class Form_Create(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        self.created_channel = None

    @discord.ui.button(label="test", style=discord.ButtonStyle.red)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        global ch_count
        ch_count += 1
        no_look_member = interaction.guild.default_role
        ch_id = await interaction.channel.guild.create_text_channel(f'test{ch_count}')
        self.created_channel = ch_id
        await interaction.response.send_message(f'created "{ch_id.mention}" channel!!', ephemeral=True)
        
        if no_look_member:
            await ch_id.set_permissions(no_look_member, read_messages=False)
        await ch_id.set_permissions(interaction.user, read_messages=True, send_messages=True)

        await ch_id.send(f'消してくれ',view=Form_Delete(ch_id))
        self.value = True

class Form_Delete(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label='test', style=discord.ButtonStyle.red)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        global ch_count
        ch_count -= 1
        await self.channel.delete()
    

@bot.tree.command(name="test", description='test for button is create channel')
async def test(interaction: discord.Interaction):
    view_1 = Form_Create()
    await interaction.response.send_message("test creat channel",view=view_1)
    await view_1.wait()
    if view_1.value or view_1.value == False:
        view_1.value = None
    else:
        print("?")

# Botを実行

models.bot_run()