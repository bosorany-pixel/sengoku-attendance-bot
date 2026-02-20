"""Stats commands (POV and similar)."""
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


@app_commands.command(name="pov_stats", description="Статистика POV: кто без ссылок и у кого последний POV старше недели")
async def pov_stats(interaction: discord.Interaction):
    if not _check_allowed(interaction):
        await interaction.response.send_message(
            "У вас нет прав для просмотра этой статистики.", ephemeral=True
        )
        return
    await interaction.response.defer()
    try:
        # Users with 0 pov_count (or NULL)
        zero_pov = db_worker.fetchall(
            f"""SELECT uid, server_username
                FROM USERS
                WHERE COALESCE(pov_count, 0) = 0 and server_username is not null and server_username!='' and roles like '%Half Orc%'
                ORDER BY server_username""",
            (),
        )
        # Users with last_pov older than 7 days (and have at least one POV)
        week_ago = db_worker.fetchall(
            f"""SELECT uid, server_username, last_pov
                FROM USERS
                WHERE last_pov IS NOT NULL AND last_pov < datetime('now', '-7 days') AND server_username is not null and server_username!='' and roles like '%Half Orc%'
                ORDER BY last_pov ASC""",
            (),
        )
        name = lambda r: (r[1] or str(r[0]) or "—").strip() or f"uid:{r[0]}"
        zero_list = "\n".join(name(r) for r in zero_pov) if zero_pov else "—"
        week_list = "\n".join(name(r) for r in week_ago) if week_ago else "—"
        # Discord embed field value limit 1024
        def truncate(s: str, max_len: int = 1020) -> str:
            if len(s) <= max_len:
                return s
            return s[: max_len - 3].rstrip() + "..."
        embed = discord.Embed(
            title="POV статистика",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name=f"Нет ни одного POV (0) — {len(zero_pov)} чел.",
            value=truncate(zero_list),
            inline=False,
        )
        embed.add_field(
            name=f"Последний POV старше недели — {len(week_ago)} чел.",
            value=truncate(week_list),
            inline=False,
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")
