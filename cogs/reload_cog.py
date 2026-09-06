import discord
from discord.ext import commands


class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="raf")
    async def reload_cog(self, ctx: commands.Context, cog_name: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"`{cog_name}` を再読み込みしました")
        except Exception as e:
            await ctx.send(f"エラー: {e}")

    @commands.is_owner()
    @commands.command(name="allraf")
    async def reload_all_cogs(self, ctx: commands.Context):
        for cog in self.bot.cogs:
            try:
                await self.bot.reload_extension(f"cogs.{cog.lower()}")
            except Exception as e:
                await ctx.send(f"エラー: {e}")
        await ctx.send("すべてのCogを再読み込みしました")

async def setup(bot):
    await bot.add_cog(ReloadCog(bot))