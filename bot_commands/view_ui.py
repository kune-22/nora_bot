import discord
import logging
from discord.ext import commands
from discord import app_commands


form_ch_count = 0

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

# 問い合わせチャンネル削除
class Form_Delete(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label='delete', style=discord.ButtonStyle.red)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        global form_ch_count
        form_ch_count -= 1
        await self.channel.delete()


# voiceチャンネル作成
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

# 聞き専を作成
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