import discord
from discord.ext import commands
from discord import app_commands


class FormCreateView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.value = None
        self.created_channel = None
        self.cog = cog

    @discord.ui.button(label="create ticket🎫", style=discord.ButtonStyle.red)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.form_ch_count += 1
        no_look_member = interaction.guild.default_role
        ch_id = await interaction.channel.guild.create_text_channel(f"お問い合わせフォーム-{self.cog.form_ch_count}")
        self.created_channel = ch_id
        await interaction.response.send_message(
            f"{ch_id.mention}が作成がされました。\n作成されたフォームにてお問い合わせ内容を送信ください。",
            ephemeral=True,
        )

        if no_look_member:
            await ch_id.set_permissions(no_look_member, read_messages=False)
        await ch_id.set_permissions(interaction.user, read_messages=True, send_messages=True)

        embed = discord.Embed(
            title="チャンネルを削除",
            description="問題が解決しましたか？\n下にあるボタンを押し、フォームを削除してください。",
            color=discord.Colour.red(),
        )
        pinning = await ch_id.send(embed=embed, view=FormDeleteView(ch_id))
        await pinning.pin()
        self.value = True


class FormDeleteView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="delete", style=discord.ButtonStyle.red)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.channel.delete()


class FormCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.form_ch_count = 0

    @app_commands.command(name="form", description="お問い合わせフォームを作成します")
    async def form_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have administrator privileges.....", ephemeral=True)
            return

        view = FormCreateView(self)
        embed = discord.Embed(
            title="お問い合わせ",
            description="下のボタンよりお問い合わせフォームを作成してください",
            color=discord.Colour.red(),
        )
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        if view.value is not None:
            view.value = None


async def setup(bot: commands.Bot):
    await bot.add_cog(FormCog(bot))
