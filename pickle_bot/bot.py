import asyncio
from dataclasses import dataclass
import logging

import discord
from discord.ext import commands

from pickle_bot.config import get_configuration
from pickle_bot.matches import get_random_matches, NotEnoughPlayersError

logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{",
    format="[{asctime}] [{levelname:8}] {name}: {message}",
)
log = logging.getLogger(__name__)


def to_list(s: str) -> [str]:
    return [name.strip().casefold() for name in s.split(",")]


@dataclass
class MsgContent:
    state_content: str
    matches_content: [str]
    errors_content: [str]

    def to_embed(self) -> discord.Embed:
        color = discord.Color.dark_green()
        lines = [self.state_content, ""]
        lines.extend(["__**Matches**__", "```"] + (self.matches_content or ["<none>"]) + ["```"])
        if self.errors_content:
            lines.extend(["__**Errors**__", "```"] + self.errors_content + ["```"])
            color = discord.Color.dark_red()
        description = "\n".join(lines)
        return discord.Embed(
            title="Pickleball Matches Generator", description=description, color=color
        )


@dataclass
class State:
    singles: str
    doubles: str
    players: [str]

    def get_msg_parts(self) -> (MsgContent, discord.ui.View):
        underlined_players = ", ".join([f"__{name}__" for name in self.players])
        state_content = "\n".join([
            f"**Player(s)**: {underlined_players} [{len(self.players)}]",
            f"**Singles court(s)**: {self.singles}",
            f"**Doubles court(s)**: {self.doubles}",
        ])
        matches_content = []
        errors_content = []

        try:
            log.info("Converting number of courts to numbers")
            singles = int(self.singles)
            doubles = int(self.doubles)
            log.info(f"Generating matches for ({singles}, {doubles}, {self.players})")
            matches = get_random_matches(singles, doubles, self.players)
            matches_content.extend([str(match) for match in matches])
        except ValueError as e:
            log.info(f"Number of courts is not an integer: {e}")
            errors_content.append(f"<number of courts not an integer>: {e}")
        except NotEnoughPlayersError as e:
            log.info(f"Not enough players to generate matches: {e}")
            errors_content.append(f"<not enough players>: {e}")
        msg_content = MsgContent(state_content, matches_content, errors_content)
        view = generate_view(self, len(errors_content) == 0)
        return (msg_content, view)


def generate_view(state: State, can_generate: bool) -> discord.ui.View:
    disabled = not can_generate
    style = discord.ButtonStyle.green if can_generate else discord.ButtonStyle.red

    class __View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.state = state

        @discord.ui.button(label="Generate", disabled=disabled, style=style)
        async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
            msg_content, view = self.state.get_msg_parts()
            await interaction.response.edit_message(embed=msg_content.to_embed(), view=view)

        @discord.ui.button(label="Edit", style=discord.ButtonStyle.blurple)
        async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(generate_modal(interaction, self.state))

    return __View()


def generate_modal(parent_interaction: discord.Interaction, state: State):
    class __Modal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Generate pickleball matches")
            self.state = state

        singles_input = discord.ui.TextInput(
            label="Singles court(s)", default=state.singles, placeholder="Number of courts"
        )
        doubles_input = discord.ui.TextInput(
            label="Doubles court(s)", default=state.doubles, placeholder="Number of courts"
        )
        players_input = discord.ui.TextInput(
            label="Player name(s)",
            default=", ".join(state.players),
            placeholder="Comma-separated list of names",
        )

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()
            msg_content, view = self.state.get_msg_parts()
            state = State(
                self.singles_input.value,
                self.doubles_input.value,
                to_list(self.players_input.value),
            )
            msg_content, view = state.get_msg_parts()
            await parent_interaction.followup.edit_message(
                parent_interaction.message.id, embed=msg_content.to_embed(), view=view
            )

    return __Modal()


class PickleBot(commands.Bot):
    def __init__(self):
        self.is_synced = False
        intents = discord.Intents.default()
        super().__init__(command_prefix="UNUSED", intents=intents)

        group = discord.app_commands.Group(
            name="pickle", description="A group of pickleball commands"
        )

        @group.command(description="Information about Pickle Bot")
        async def about(interaction: discord.Interaction):
            description = """
A [Discord Bot](https://discord.com/developers/docs/intro#bots-and-apps) for pickleball stuff

Current commands are:
* `about`:  Show information about Pickle Bot
* `pickle`: Open a helper to generate pickleball matches
"""
            embed = discord.Embed(title="About **Pickle Bot**", description=description)
            embed.set_image(url="attachement://picklebot.jpg")
            file = discord.File("picklebot.jpg")
            view = discord.ui.View()
            button = discord.ui.Button(
                label="GitHub",
                url="https://github.com/CalebLehman/pickle-bot",
                style=discord.ButtonStyle.link,
            )
            view.add_item(button)
            await interaction.response.send_message(
                embed=embed, view=view, file=file, ephemeral=True
            )

        @group.command(description="Generate random pickleball matches")
        @discord.app_commands.describe(
            players="Comma-separated list of player names",
            singles="Number of singles courts",
            doubles="Number of doubles courts",
        )
        async def match(
            interaction: discord.Interaction, players: str, singles: int = 0, doubles: int = 0
        ):
            state = State(str(singles), str(doubles), to_list(players))
            msg_content, view = state.get_msg_parts()
            await interaction.response.send_message(
                embed=msg_content.to_embed(), view=view, ephemeral=True
            )

        self.tree.add_command(group)

        @self.event
        async def on_ready():
            if not self.is_synced:
                await self.tree.sync()
                self.is_synced = True
                log.info("Synced tree")
            if self.user is not None:
                log.info(f"Logged in as {self.user.name!r}")

        @self.event
        async def on_app_command_completion(
            interaction: discord.Interaction, command: discord.app_commands.Command
        ):
            name = command.qualified_name
            args = ", ".join([str(arg) for arg in interaction.namespace])
            log.info(
                f"Ran {name!r} with ({args}) for {interaction.user} (ID {interaction.user.id})"
            )

    async def run(self, token: str):
        await self.start(token)


def main():
    config = get_configuration()
    logging.getLogger().setLevel(config.log_level)

    bot = PickleBot()
    try:
        asyncio.run(bot.run(config.token))
    except KeyboardInterrupt:
        log.info("Shutting down")
