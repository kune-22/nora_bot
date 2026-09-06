from collections.abc import Awaitable, Callable, Sequence

import discord


RoleSelectedCallback = Callable[[discord.Interaction, str], Awaitable[None]]


class PaginatedRoleSelectView(discord.ui.View):
    """カスタムロール名を25件ずつ表示する共通ドロップダウン。"""

    PAGE_SIZE = 25

    def __init__(
        self,
        role_names: Sequence[str],
        on_role_selected: RoleSelectedCallback,
        *,
        placeholder: str,
        author_id: int | None = None,
        timeout: float | None = 180,
        delete_on_timeout: bool = False,
    ):
        if not role_names:
            raise ValueError("role_names must not be empty")

        super().__init__(timeout=timeout)
        self.role_names = list(role_names)
        self.on_role_selected = on_role_selected
        self.placeholder = placeholder
        self.author_id = author_id
        self.delete_on_timeout = delete_on_timeout
        self.page = 0
        self.message: discord.Message | None = None
        self._build_components()

    @property
    def page_count(self) -> int:
        return (len(self.role_names) + self.PAGE_SIZE - 1) // self.PAGE_SIZE

    def _build_components(self) -> None:
        self.clear_items()
        start = self.page * self.PAGE_SIZE
        page_roles = self.role_names[start : start + self.PAGE_SIZE]

        options = [
            discord.SelectOption(
                # Discordのラベルは100文字まで。
                label=role_name[:100],
                value=str(start + index),
            )
            for index, role_name in enumerate(page_roles)
        ]
        select = discord.ui.Select(placeholder=self.placeholder, options=options, row=0)
        select.callback = self._select_role
        self.add_item(select)

        if self.page_count > 1:
            previous = discord.ui.Button(
                label="前へ",
                style=discord.ButtonStyle.secondary,
                disabled=self.page == 0,
                row=1,
            )
            previous.callback = self._previous_page
            self.add_item(previous)

            next_button = discord.ui.Button(
                label="次へ",
                style=discord.ButtonStyle.secondary,
                disabled=self.page >= self.page_count - 1,
                row=1,
            )
            next_button.callback = self._next_page
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "このメニューはコマンドを実行した人だけが操作できます。",
                ephemeral=True,
            )
            return False
        return True

    async def _select_role(self, interaction: discord.Interaction) -> None:
        select = interaction.data.get("values", []) if interaction.data else []
        if not select:
            await interaction.response.send_message("ロールを選択できませんでした。", ephemeral=True)
            return

        role_name = self.role_names[int(select[0])]
        await self.on_role_selected(interaction, role_name)

    async def _previous_page(self, interaction: discord.Interaction) -> None:
        self.page -= 1
        self._build_components()
        await interaction.response.edit_message(view=self)

    async def _next_page(self, interaction: discord.Interaction) -> None:
        self.page += 1
        self._build_components()
        await interaction.response.edit_message(view=self)

    async def on_timeout(self) -> None:
        if self.message is not None:
            try:
                if self.delete_on_timeout:
                    await self.message.delete()
                else:
                    await self.message.edit(view=None)
            except discord.HTTPException:
                pass
