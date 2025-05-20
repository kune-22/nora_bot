import asyncio

# discord.py をインポート
import discord
#logを保存するためにインポート
import logging

# bot commandを使用するためにインポート
from discord.ext import commands
from discord import app_commands
# modelsから必要なモデルをインポート(botはサーバーを起動するために必要な変数)
from models import bot, Confirm, User, Channel
import models as models
import youtube_dl

form_ch_count = 0

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
#お問い合わせ作成の処理        
class Form_Create(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        self.created_channel = None

    @discord.ui.button(label="create ticket🎫", style=discord.ButtonStyle.red)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        global form_ch_count
        form_ch_count += 1
        no_look_member = interaction.guild.default_role
        ch_id = await interaction.channel.guild.create_text_channel(f'お問い合わせフォーム-{form_ch_count}')
        self.created_channel = ch_id
        await interaction.response.send_message(f'{ch_id.mention}が作成がされました。\n作成されたフォームにてお問い合わせ内容を送信ください。', ephemeral=True)

        #everyoneに対してチャンネルを非表示
        if no_look_member:
            await ch_id.set_permissions(no_look_member, read_messages=False)
        #ボタンを押した人に閲覧権限を付与
        await ch_id.set_permissions(interaction.user, read_messages=True, send_messages=True)

        embed = discord.Embed(
            title="チャンネルを削除",
            description="問題が解決しましたか？\n下にあるボタンを押し、フォームを削除してください。",
            color=discord.Colour.red()
        )
        pinning = await ch_id.send(embed=embed,view=Form_Delete(ch_id))
        await pinning.pin()
        self.value = True

class Form_Delete(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label='delete', style=discord.ButtonStyle.red)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        global form_ch_count
        form_ch_count -= 1
        await self.channel.delete()
    

@bot.tree.command(name="form", description='お問い合わせフォームを作成します')
async def form(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        view_1 = Form_Create()
        embed = discord.Embed(
            title="お問い合わせ",
            description="下のボタンよりお問い合わせフォームを作成してください",
            color=discord.Colour.red(),
        )
        await interaction.response.send_message(embed=embed,view=view_1)
        await view_1.wait()
        if view_1.value or view_1.value == False:
            view_1.value = None
    else:
        await interaction.response.send_message("You do not have administrator privileges.....")


#ボイスチャンネル+聞き専を作成

class VcName(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="作成するボイスチャンネル名を入力")
        self.voice_channel_name = discord.ui.TextInput(label="ボイスチャンネル名",placeholder="例：VC1",required=True)
        self.add_item(self.voice_channel_name)
        

    async def on_submit(self, interaction: discord.Interaction):
        vc_name = self.voice_channel_name.value

        category = interaction.channel.category
        voice_channel = await interaction.guild.create_voice_channel(vc_name, category=category)
        await interaction.response.send_message(f"ボイスチャネル{voice_channel}が作成されました。\n聞き専は、ボイスチャンネルに入室すると表示されます。\nこのメッセージは5秒後に削除されます。", ephemeral=True)

class Vc_listen_create(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        self.created_channel = None
        self.created_voice_channel  = None

    @discord.ui.button(label="ボイスチャンネルを作成",style=discord.ButtonStyle.blurple)
    async def vc_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VcName()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="聞き専を作成", style=discord.ButtonStyle.green)
    async def listen_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        category = interaction.channel.category
        lt_ch = await interaction.guild.create_text_channel("聞き専",category=category)
        await interaction.response.send_message(f"{lt_ch.mention}が作成されました。", ephemeral=True)

@bot.tree.command(name="create_voice_channel", description="ボイスチャンネル・聞き専を作成します")
async def create_voice_channel(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        view = Vc_listen_create()
        embed = discord.Embed(
            title="ボイスチャンネルを作成",
            description="ボタンを押してボイスチャンネル名を入力し、送信してください。\n聞き専ボタンを押すと新たに「聞き専」が作成されます。",
            color=discord.Colour.blue()
        )
        await interaction.response.send_message(embed=embed,view=view)
        await view.wait()
        if view.value or view.value == False:
            view.value = None
    else:
        await interaction.response.send_message("You do not have administrator privileges.....")
# Botを実行

models.bot_run()