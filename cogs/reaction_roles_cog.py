import discord
from discord.ext import commands
from discord import app_commands


class ReactionRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reaction_roles", description="リアクションロールボードを作成できます。")
    async def reaction_roles(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have administrator privileges.....", ephemeral=True)
            return

        await interaction.response.send_message("この機能は開発中です。", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRolesCog(bot))
