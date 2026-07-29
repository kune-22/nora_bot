import discord
from discord.ext import commands


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or not message.guild:
            return

        if message.content.startswith("test"):
            await message.channel.send("正常に動作しています")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
