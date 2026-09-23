import discord
from discord.ext import commands
from discord import app_commands,Interaction
import asyncio
from sqlalchemy.exc import IntegrityError
from db.crud import (
    add_custom_role_to_user, create_custom_role, create_custom_role_channel, delete_custom_role, delete_custom_role_channel, get_channels_by_custom_role, get_custom_roles,
    get_roles_by_user, get_users_by_role, remove_custom_role_from_user
)
from services.channel_permission import (
    grant_custom_role_channel_access,
    revoke_custom_role_channel_access,
)
from views.role_select import PaginatedRoleSelectView



def make_role_select_embed_factory(title: str, description: str):
    """Selectの現在ページに表示されている候補だけをEmbedへ載せる。"""
    def factory(role_names, page: int, page_count: int):
        page_text = "\n".join(f"- {role_name}" for role_name in role_names)
        if page_count > 1:
            page_text = f"{page_text}\n\nページ: {page + 1}/{page_count}"
        return discord.Embed(
            title=title,
            description=f"{description}\n\n{page_text}",
            color=discord.Colour.blue(),
        ).set_footer(text="表示されているロールから選択してください")

    return factory

# ロール作成
class CreateCustomRoleModal(discord.ui.Modal):
    def __init__(self, guild_id: int):
        super().__init__(title="Create Custom Role")
        self.guild_id = guild_id
        self.role_name = discord.ui.TextInput(
            label = "Role Name",
            placeholder = "cat",
            required = True,
        )
        self.add_item(self.role_name)

    async def on_submit(self, interaction: discord.Interaction):
        role_name = self.role_name.value.strip()
        if not role_name:
            await interaction.response.send_message(
                "カスタムロール名を入力してください。",
                ephemeral=True,
            )
            return

        # 先に確認して、DBの一意制約違反をユーザー向けの案内に変える。
        existing_roles = get_custom_roles(self.guild_id)
        if any(role.role_name.casefold() == role_name.casefold() for role in existing_roles):
            await interaction.response.send_message(
                f"「{role_name}」という名前のカスタムロールは既に存在します。別の名前を入力してください。",
                ephemeral=True,
            )
            return

        try:
            create_custom_role(self.guild_id, role_name)
        except IntegrityError:
            # 同時操作などで事前確認後に重複した場合も同じ案内を返す。
            await interaction.response.send_message(
                f"「{role_name}」という名前のカスタムロールは既に存在します。別の名前を入力してください。",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(f"Creating custom_role:@{role_name}, create user by {interaction.user.mention}\n messages will be deleted in 5 seconds.")
        await asyncio.sleep(5)
        await interaction.delete_original_response()
#付与
class AddUserToCustomRoleView(PaginatedRoleSelectView):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        roles = get_custom_roles(guild_id)
        self.embed_factory = make_role_select_embed_factory(
            "カスタムロールを追加",
            "以下のロールから、ユーザーに付与するロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.role_select,
            placeholder="Select a role",
            embed_factory=self.embed_factory,
        )

    async def role_select(self, interaction: discord.Interaction, role_name: str):
        try:
            add_custom_role_to_user(self.guild_id, role_name, interaction.user.id, interaction.user.name)
            if interaction.guild is None:
                await interaction.response.send_message("サーバー情報を取得できませんでした。", ephemeral=True)
                return

            message = f"Adding custom role:@{role_name}"
            channel_records = get_channels_by_custom_role(self.guild_id, role_name)
            if channel_records:
                updated_count, failed_count = await grant_custom_role_channel_access(
                    interaction.guild,
                    self.guild_id,
                    role_name,
                    interaction.user,
                    channel_records=channel_records,
                )
                if failed_count:
                    message += f"\nチャンネル権限の更新に失敗: {failed_count}件"
                elif updated_count:
                    message += f"\nチャンネル閲覧権限を更新: {updated_count}件"
            await interaction.response.send_message(message, ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
#剝奪
class RemoveUserFromCustomRoleView(PaginatedRoleSelectView):
    def __init__(self, guild_id: int, user_id: int):
        self.guild_id = guild_id
        self.user_id = user_id
        roles = get_roles_by_user(guild_id, user_id)
        self.embed_factory = make_role_select_embed_factory(
            "カスタムロールを削除",
            "以下のロールから、あなたが所持しているロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.role_select,
            placeholder="Select a role",
            author_id=user_id,
            embed_factory=self.embed_factory,
        )

    async def role_select(self, interaction: discord.Interaction, role_name: str):
        try:
            remove_custom_role_from_user(self.guild_id, role_name, self.user_id)
            if interaction.guild is None:
                await interaction.response.send_message("サーバー情報を取得できませんでした。", ephemeral=True)
                return

            message = f"Removing custom role:@{role_name}"
            channel_records = get_channels_by_custom_role(self.guild_id, role_name)
            if channel_records:
                updated_count, failed_count = await revoke_custom_role_channel_access(
                    interaction.guild,
                    self.guild_id,
                    role_name,
                    interaction.user,
                    channel_records=channel_records,
                )
                if failed_count:
                    message += f"\nチャンネル権限の更新に失敗: {failed_count}件"
                elif updated_count:
                    message += f"\nチャンネル閲覧権限を更新: {updated_count}件"
            await interaction.response.send_message(message, ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

#削除
class DeleteCustomRoleView(PaginatedRoleSelectView):
    def __init__(self, guild_id: int, author_id: int):
        self.guild_id = guild_id
        roles = get_custom_roles(guild_id)
        self.embed_factory = make_role_select_embed_factory(
            "カスタムロールを削除",
            "以下のロールから、サーバーから削除するロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.role_select,
            placeholder="Select a role",
            author_id=author_id,
            embed_factory=self.embed_factory,
        )

    async def role_select(self, interaction: discord.Interaction, role_name: str):
        try:
            delete_custom_role(self.guild_id, role_name)
            await interaction.response.send_message(f"Deleting custom role:@{role_name} and removing it from all users\n messages will be deleted in 15 seconds.")
            await asyncio.sleep(15)
            await interaction.delete_original_response()
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

#一覧と対象Uの表示
class ListView(PaginatedRoleSelectView):
    def __init__(self, cog, guild_id: int, author_id: int):
        self.cog = cog
        self.guild_id = guild_id
        roles = get_custom_roles(guild_id)
        self.embed_factory = make_role_select_embed_factory(
            "Custom Roles List",
            "以下のロールから、所持ユーザーを表示するロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.role_select,
            placeholder="Select a role to view users",
            author_id=author_id,
            embed_factory=self.embed_factory,
        )

    async def role_select(self, interaction: discord.Interaction, role_name: str):
        try:
            users = get_users_by_role(self.guild_id, role_name)
            if not users:
                embed = discord.Embed(
                    title=f"Custom Role: @{role_name}",
                    description="No users have this custom role",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                embed = discord.Embed(
                    title=f"Custom Role: @{role_name}",
                    description=f"Total Users: {len(users)}",
                    color=discord.Color.blue()
                )
                
                current_field = ""
                field_count = 0
                
                for user in users:
                    user_line = f"- {user.user_name} (ID: {user.discord_user_id})\n"
                    if len(current_field) + len(user_line) > 1024:
                        embed.add_field(
                            name=f"Users ({field_count + 1})" if field_count > 0 else "Users",
                            value=current_field.strip(),
                            inline=False
                        )
                        current_field = user_line
                        field_count += 1
                    else:
                        current_field += user_line
                
                if current_field:
                    embed.add_field(
                        name=f"Users ({field_count + 1})" if field_count > 0 else "Users",
                        value=current_field.strip(),
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

# role所持者のみのチャンネル作成等のViewを必要に応じてここに追加
# Modal (channel name) second
class CreateChannelModal(discord.ui.Modal):
    def __init__(self, guild_id: int, category_id: int, role_name: str):
        super().__init__(title="Please enter the channel name")
        self.guild_id = guild_id
        self.role_name = role_name
        self.category_id = category_id
        self.channel_name = discord.ui.TextInput(
            label="Channel Name",
            placeholder="meow",
            required=True
        )
        self.add_item(self.channel_name)

    async def on_submit(self, modal_interaction: discord.Interaction):
        guild = modal_interaction.guild
        if guild is None:
            await modal_interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        category = guild.get_channel(self.category_id)
        if not isinstance(category, discord.CategoryChannel):
            await modal_interaction.response.send_message(
                "選択したカテゴリが見つかりません。もう一度やり直してください。",
                ephemeral=True,
            )
            return

        channel_name = self.channel_name.value
        ct_role_members = get_users_by_role(self.guild_id, self.role_name)
        members = [
            guild.get_member(user.discord_user_id)
            for user in ct_role_members
        ]

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                **{
                    member: discord.PermissionOverwrite(view_channel=True)
                    for member in members
                    if member is not None
                }
            }
        )
        create_custom_role_channel(self.guild_id, self.role_name, channel.id)
        await modal_interaction.response.send_message(f"<#{channel.id}> channel created for custom role **@{self.role_name}** only views", ephemeral=True)


class CreateChannelCategorySelectView(discord.ui.View):
    """カテゴリを25件ずつ表示して、チャンネル作成先を選ぶView。"""

    PAGE_SIZE = 25

    def __init__(
        self,
        guild_id: int,
        role_name: str,
        categories: list[discord.CategoryChannel],
        author_id: int,
    ):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.role_name = role_name
        self.categories = categories
        self.author_id = author_id
        self.page = 0
        self._build_components()

    @property
    def page_count(self) -> int:
        return (len(self.categories) + self.PAGE_SIZE - 1) // self.PAGE_SIZE

    def _build_components(self) -> None:
        self.clear_items()
        start = self.page * self.PAGE_SIZE
        page_categories = self.categories[start : start + self.PAGE_SIZE]

        select = discord.ui.Select(
            placeholder="カテゴリを選択してください",
            options=[
                discord.SelectOption(label=category.name, value=str(category.id))
                for category in page_categories
            ],
            row=0,
        )
        select.callback = self.select_category
        self.add_item(select)

        if self.page_count > 1:
            previous = discord.ui.Button(
                label="前へ",
                style=discord.ButtonStyle.secondary,
                disabled=self.page == 0,
                row=1,
            )
            previous.callback = self.previous_page
            self.add_item(previous)

            next_button = discord.ui.Button(
                label="次へ",
                style=discord.ButtonStyle.secondary,
                disabled=self.page >= self.page_count - 1,
                row=1,
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "このメニューは操作を開始した人だけが使用できます。",
                ephemeral=True,
            )
            return False
        return True

    async def select_category(self, interaction: discord.Interaction) -> None:
        category_id = int(interaction.data["values"][0])
        await interaction.response.send_modal(
            CreateChannelModal(self.guild_id, category_id, self.role_name)
        )
        self.stop()

    async def previous_page(self, interaction: discord.Interaction) -> None:
        self.page -= 1
        self._build_components()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction) -> None:
        self.page += 1
        self._build_components()
        await interaction.response.edit_message(view=self)

# view(role and category) select  first
class CreateChannelThisCustomRole(PaginatedRoleSelectView):
    def __init__(self, cog, guild_id: int, author_id: int):
        self.cog = cog
        self.guild_id = guild_id
        roles = get_roles_by_user(guild_id, author_id)
        self.embed_factory = make_role_select_embed_factory(
            "チャンネル作成に使用するロール",
            "以下のロールから、チャンネルを閲覧できるロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.select_role,
            placeholder="ロールを選択",
            author_id=author_id,
            timeout=120,
            embed_factory=self.embed_factory,
        )

    async def select_role(self, interaction: discord.Interaction, role_name: str):
        guild = self.cog.bot.get_guild(self.guild_id)
        if guild is None:
            await interaction.response.send_message("サーバー情報を取得できませんでした。", ephemeral=True)
            return

        if not guild.categories:
            await interaction.response.edit_message(
                content="作成先として選べるカテゴリがありません。",
                view=None,
            )
            self.stop()
            return

        category_view = CreateChannelCategorySelectView(
            guild_id=self.guild_id,
            role_name=role_name,
            categories=guild.categories,
            author_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            content="チャンネルを作成するカテゴリを選択してください:",
            view=category_view,
        )
        self.stop()
   

# mention部分一致時のドロップダウン
class MentionRoleSelectView(PaginatedRoleSelectView):
    def __init__(self, cog, guild_id: int, author_id: int, roles, message: str | None):
        self.cog = cog
        self.guild_id = guild_id
        self.mention_message = message
        self.embed_factory = make_role_select_embed_factory(
            "メンションするロールを選択",
            "検索結果のうち、メンションするロールを選択できます。",
        )
        super().__init__(
            [role.role_name for role in roles],
            self.select_role,
            placeholder="メンションするロールを選択",
            author_id=author_id,
            timeout=120,
            embed_factory=self.embed_factory,
        )

    async def select_role(self, interaction: discord.Interaction, role_name: str):
        if interaction.channel is None:
            await interaction.response.send_message("チャンネルを取得できませんでした。", ephemeral=True)
            return

        # コンポーネント操作を受理してから、候補メニューを消す。
        await interaction.response.defer()
        await interaction.message.delete()

        await self.cog.send_role_mention(
            interaction.channel,
            self.guild_id,
            role_name,
            self.mention_message,
        )

        self.stop()
        

class CustomRoleControlView(discord.ui.View):
    def __init__(self, cog, guild_id: int | None = None):
        super().__init__(timeout=None)
        self.value = None
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(
        label="Create Custom Role",
        style=discord.ButtonStyle.blurple,
        custom_id="custom_role_control:create",
    )
    async def create_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id or interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        modal = CreateCustomRoleModal(guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Add Custom Role",
        style=discord.ButtonStyle.green,
        custom_id="custom_role_control:add",
    )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id or interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        if not get_custom_roles(guild_id):
            await interaction.response.send_message("追加できるカスタムロールはありません。", ephemeral=True)
            return
        view = AddUserToCustomRoleView(guild_id)
        await interaction.response.send_message(
            embed=view.current_page_embed(),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Remove Custom Role",
        style=discord.ButtonStyle.red,
        custom_id="custom_role_control:remove",
    )
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id or interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        if not get_roles_by_user(guild_id, interaction.user.id):
            await interaction.response.send_message("削除できるカスタムロールはありません。", ephemeral=True)
            return
        view = RemoveUserFromCustomRoleView(guild_id, interaction.user.id)
        await interaction.response.send_message(
            embed=view.current_page_embed(),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Delete Custom Role",
        style=discord.ButtonStyle.danger,
        custom_id="custom_role_control:delete",
    )
    async def delete_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id or interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        if not get_custom_roles(guild_id):
            await interaction.response.send_message("削除できるカスタムロールはありません。", ephemeral=True)
            return
        view = DeleteCustomRoleView(guild_id, interaction.user.id)
        await interaction.response.send_message(
            embed=view.current_page_embed(),
            view=view,
            ephemeral=True,
        )

class CustomRoleActionView(discord.ui.View):
    def __init__(self, cog, guild_id: int | None = None):
        super().__init__(timeout=None)
        self.value = None
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(
        label="チャンネル作成",
        style=discord.ButtonStyle.primary,
        custom_id="custom_role_action:create_channel",
    )
    async def open_create_channel_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id or interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        if not get_roles_by_user(guild_id, interaction.user.id):
            await interaction.response.send_message(
                "あなたが所持しているカスタムロールがありません。",
                ephemeral=True,
            )
            return

        view = CreateChannelThisCustomRole(self.cog, guild_id, interaction.user.id)
        await interaction.response.send_message(
            embed=view.current_page_embed(),
            view=view,
            ephemeral=True,
        )

class CustomRoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # コントロールパネル
    @app_commands.command(name="custom_role_control", description="カスタムロールのコントロールパネルを生成します")
    async def custom_role_control(self, interaction: discord.Interaction):
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このパネルは管理者のみ配置できます。", ephemeral=True)
            return

        view = CustomRoleControlView(self, interaction.guild_id)
        embed = discord.Embed(
            title="Custom Role Control Panel",
            description="ボタンを押してカスタムロールを作成してください。",
            color=discord.Colour.blue(),
        )
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        if view.value is not None:
            view.value = None

    # 操作パネル
    @app_commands.command(name="custom_role_action", description="カスタムロールを使用してチャンネル等を作成できるパネルを生成します。")
    async def custom_role_action(self, interaction: discord.Interaction):
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このパネルは管理者のみ配置できます。", ephemeral=True)
            return

        view = CustomRoleActionView(self, interaction.guild_id)
        embed = discord.Embed(
                title="Custom Role Action Panel",
                description="カスタムロールを使用して行いたい操作がかかれているボタンを押して下さい。",
                color=discord.Colour.blue(),
            )
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()


    @commands.command(name="list_custom_roles")
    async def list_custom_roles(self, ctx):
        custom_roles = get_custom_roles(ctx.guild.id)
        if not custom_roles:
            msg = await ctx.send("カスタムロールは存在しません。")
            await msg.delete(delay=2)
            await ctx.message.delete(delay=3)
            return

        view = ListView(self, ctx.guild.id, ctx.author.id)
        view.message = await ctx.send(embed=view.current_page_embed(), view=view)

    @commands.command(name="mention")
    async def mention(self, ctx, role_query: str, *, message: str = None):
        roles = get_custom_roles(ctx.guild.id)

        matched_role = discord.utils.find(
            lambda role: role.role_name.casefold() == role_query.casefold(),
            roles,
        )
        if matched_role:
            await self.send_role_mention(ctx, ctx.guild.id, matched_role.role_name, message)
            await self.delete_command_message(ctx)
            return

        candidates = [
            role for role in roles
            if role_query.casefold() in role.role_name.casefold()
        ]

        if not candidates:
            await ctx.send(f"「{role_query}」に一致するカスタムロールはありません。")
            await self.delete_command_message(ctx)
            return

        view = MentionRoleSelectView(
            cog=self,
            guild_id=ctx.guild.id,
            author_id=ctx.author.id,
            roles=candidates,
            message=message,
        )

        menu_message = await ctx.send(embed=view.current_page_embed(), view=view)
        view.message = menu_message
        await self.delete_command_message(ctx)

    async def delete_command_message(self, ctx) -> None:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    async def send_role_mention(self, channel, guild_id: int, role_name: str, message: str | None):
        users = get_users_by_role(guild_id, role_name)

        if not users:
            await channel.send(f"カスタムロール @{role_name} を持つユーザーはいません。")
            return

        mentions = " ".join(f"<@{user.discord_user_id}>" for user in users)
        text = f"@{role_name} を持つユーザーへのメンション:\n{mentions}"

        if message:
            text += f"\n{message}"

        await channel.send(
            text,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
            ),
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        # DB登録済みのカスタムロール用チャンネルだけが削除される。
        delete_custom_role_channel(channel.id)

async def setup(bot: commands.Bot):
    cog = CustomRoleCog(bot)
    await bot.add_cog(cog)

    # timeout=None と全コンポーネントのcustom_idにより、再起動後も既存パネルを受け取れる。
    bot.add_view(CustomRoleControlView(cog))
    bot.add_view(CustomRoleActionView(cog))
        
