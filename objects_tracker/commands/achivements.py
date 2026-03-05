"""Commands for managing BP levels and achievements. No user-specific data."""
import discord
from discord import app_commands
from objects_tracker.utils.data_store import load_allowed_roles
from src.db_worker import DBWorker

db_worker = DBWorker()


def _check_allowed(interaction: discord.Interaction) -> bool:
    """Return True if user is allowed to run admin-level commands."""
    allowed_role_ids = load_allowed_roles(interaction.guild.id)
    if not allowed_role_ids:
        return True
    user_role_ids = [r.id for r in interaction.user.roles]
    return any(rid in allowed_role_ids for rid in user_role_ids)


@app_commands.command(name="eddit_level", description="Редактировать порог посещений и достижение для уровня")
@app_commands.describe(
    level="Номер уровня батлпаса",
    attendance="Сколько посещений нужно на этот уровень",
    description="Описание награды/достижения за уровень (необязательно — можно создать уровень без достижения)",
    picture="URL или текст картинки (необязательно)",
)
async def eddit_level(
    interaction: discord.Interaction,
    level: int,
    attendance: int,
    description: str | None = None,
    picture: str = "",
):
    if not _check_allowed(interaction):
        await interaction.response.send_message(
            "У вас нет прав для добавления данных.", ephemeral=True
        )
        return
    if level < 1 or attendance < 0:
        await interaction.response.send_message(
            "Уровень должен быть ≥ 1, посещения ≥ 0.", ephemeral=True
        )
        return
    try:
        db_worker.set_level_attendance(level, attendance)
        if description is not None:
            db_worker.set_achievement_for_level(level, description, picture or "")
        msg = f"Уровень **{level}** обновлён: посещений **{attendance}**."
        if description is not None:
            msg += " Достижение задано."
        await interaction.response.send_message(msg, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"Ошибка: {e}", ephemeral=True
        )


@app_commands.command(name="create_achievement", description="Создать достижение")
@app_commands.describe(
    bp_level="Уровень батлпаса для этого достижения",
    description="Описание достижения",
    picture="URL или текст картинки (необязательно)",
)
async def create_achievement(
    interaction: discord.Interaction,
    bp_level: int,
    description: str,
    picture: str = "",
):
    if not _check_allowed(interaction):
        await interaction.response.send_message(
            "У вас нет прав для добавления данных.", ephemeral=True
        )
        return
    if bp_level < 1:
        await interaction.response.send_message(
            "Уровень должен быть ≥ 1.", ephemeral=True
        )
        return
    try:
        aid = db_worker.create_achievement(bp_level, description, picture or "")
        await interaction.response.send_message(
            f"Достижение создано (id **{aid}**) для уровня **{bp_level}**.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Ошибка: {e}", ephemeral=True
        )


@app_commands.command(name="edit_achievement", description="Редактировать достижение по id")
@app_commands.describe(
    achievement_id="ID достижения",
    bp_level="Уровень батлпаса",
    description="Описание достижения",
    picture="URL или текст картинки (необязательно)",
)
async def edit_achievement(
    interaction: discord.Interaction,
    achievement_id: int,
    bp_level: int,
    description: str,
    picture: str = "",
):
    if not _check_allowed(interaction):
        await interaction.response.send_message(
            "У вас нет прав для добавления данных.", ephemeral=True
        )
        return
    if bp_level < 1:
        await interaction.response.send_message(
            "Уровень должен быть ≥ 1.", ephemeral=True
        )
        return
    ok = db_worker.update_achievement(
        achievement_id, bp_level, description, picture or ""
    )
    if not ok:
        await interaction.response.send_message(
            f"Достижение с id **{achievement_id}** не найдено.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"Достижение **{achievement_id}** обновлено.", ephemeral=True
    )


@app_commands.command(name="delete_achievement", description="Удалить достижение по id")
@app_commands.describe(achievement_id="ID достижения")
async def delete_achievement(
    interaction: discord.Interaction,
    achievement_id: int,
):
    if not _check_allowed(interaction):
        await interaction.response.send_message(
            "У вас нет прав для добавления данных.", ephemeral=True
        )
        return
    ok = db_worker.delete_achievement(achievement_id)
    if not ok:
        await interaction.response.send_message(
            f"Достижение с id **{achievement_id}** не найдено.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"Достижение **{achievement_id}** удалено.", ephemeral=True
    )


@app_commands.command(name="list_levels", description="Список уровней и достижений (без данных об пользователях)")
async def list_levels(interaction: discord.Interaction):
    try:
        levels = db_worker.get_bp_levels()
        achievements = db_worker.get_all_achievements()
    except Exception as e:
        await interaction.response.send_message(
            f"Ошибка: {e}", ephemeral=True
        )
        return

    if not levels and not achievements:
        await interaction.response.send_message(
            "Уровней и достижений пока нет.", ephemeral=True
        )
        return

    lines = []
    if levels:
        lines.append("**Уровни (порог посещений):**")
        for level, attendance in levels:
            lines.append(f"  Уровень {level}: **{attendance}** посещений")
        lines.append("")
    if achievements:
        lines.append("**Достижения:**")
        for aid, bp_level, desc, pic in achievements:
            pic_preview = (pic[:50] + "…") if pic and len(pic) > 50 else (pic or "—")
            lines.append(f"  id {aid} | уровень {bp_level} | {desc[:60]}{'…' if len(desc) > 60 else ''} | {pic_preview}")

    await interaction.response.send_message(
        "\n".join(lines) if lines else "Пусто.",
        ephemeral=True,
    )
