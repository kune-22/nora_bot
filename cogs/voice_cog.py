import discord
from discord.ext import commands
from discord import app_commands


class VcNameModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="作成するボイスチャンネル名を入力")
        self.voice_channel_name = discord.ui.TextInput(
            label="ボイスチャンネル名",
            placeholder="例：VC1",
            required=True,
        )
        self.add_item(self.voice_channel_name)

    async def on_submit(self, interaction: discord.Interaction):
        vc_name = self.voice_channel_name.value
        category = interaction.channel.category
        voice_channel = await interaction.guild.create_voice_channel(vc_name, category=category)
        await interaction.response.send_message(
            f"ボイスチャネル{voice_channel}が作成されました。\n聞き専は、ボイスチャンネルに入室すると表示されます。\nこのメッセージは5秒後に削除されます。",
            ephemeral=True,
        )


class VcListenCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        self.created_channel = None
        self.created_voice_channel = None

    @discord.ui.button(label="ボイスチャンネルを作成", style=discord.ButtonStyle.blurple)
    async def vc_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VcNameModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="聞き専を作成", style=discord.ButtonStyle.green)
    async def listen_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        category = interaction.channel.category
        lt_ch = await interaction.guild.create_text_channel("聞き専", category=category)
        await interaction.response.send_message(f"{lt_ch.mention}が作成されました。", ephemeral=True)


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create_voice_channel", description="ボイスチャンネル・聞き専を作成します")
    async def create_voice_channel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have administrator privileges.....", ephemeral=True)
            return

        view = VcListenCreateView()
        embed = discord.Embed(
            title="ボイスチャンネルを作成",
            description="ボタンを押してボイスチャンネル名を入力し、送信してください。\n聞き専ボタンを押すと新たに「聞き専」が作成されます。",
            color=discord.Colour.blue(),
        )
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        if view.value is not None:
            view.value = None


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceCog(bot))
