import asyncio

# discord.py をインポート
import discord
#logを保存するためにインポート
import logging

# bot commandを使用するためにインポート
from discord.ext import commands
from discord import app_commands

# modelsから必要なモデルをインポート(botはサーバーを起動するために必要な変数)
import models
from models import bot
import view_ui


# メッセージが送信された時の処理
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # 通常のメッセージコマンド処理
    
    if message.content.startswith('test'):
        await message.channel.send("正常に動作しています")
    
    # スラッシュコマンドを処理するために、明示的にbot.process_commandsを呼び出す
    await bot.process_commands(message)
    

@bot.tree.command(name="form", description='お問い合わせフォームを作成します')
async def form(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        view_1 = view_ui.Form_Create()
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


@bot.tree.command(name="create_voice_channel", description="ボイスチャンネル・聞き専を作成します")
async def create_voice_channel(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        view = view_ui.Vc_listen_create()
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


@bot.tree.command(name="reaction_roles" , description="リアクションロールボードを作成できます。")
async def create_role_bords(interaction: discord.Interaction):
    pass

# Botを実行

models.bot_run()