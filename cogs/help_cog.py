import discord
from discord.ext import commands
from discord import app_commands, Interaction


def build_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="のらねこbot Help",
        description="のらねこbotのコマンド一覧です。\n"
        "お問い合わせ等サポートサーバーにて対応できます。プロフィールよりご参加下さい。",
        color=discord.Colour.blue()
    )
    embed.add_field(name="/form", value="お問い合わせフォームを作成します。", inline=False)
    embed.add_field(name="/create_voice_channel", value="ボイスチャンネル・聞き専を作成します。", inline=False)
    embed.add_field(name="/reaction_roles", value="開発中のため使用できません。", inline=False)
    embed.add_field(name="その他", value="機能追加時サポートサーバーにてお知らせ致します。", inline=False)
    embed.set_footer(text="現在開発中のため機能が少ないです。")
    return embed


class StrayCatHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = build_help_embed()
        channel = self.get_destination()
        await channel.send(embed=embed)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cogがロードされたタイミングで help_command を差し替える
        bot.help_command = StrayCatHelp()

    @app_commands.command(name="help", description="のらねこbotのコマンド一覧を表示します")
    async def slash_help(self, interaction: Interaction):
        embed = build_help_embed()
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))