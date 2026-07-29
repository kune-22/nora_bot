import discord
from discord.ext import commands


class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload_addfunc")
    async def reload_cog(self, ctx: commands.Context, cog_name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("権限がありません")
            return
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"`{cog_name}` を再読み込みしました")
        except Exception as e:
            await ctx.send(f"エラー: {e}")


async def setup(bot):
    await bot.add_cog(ReloadCog(bot))