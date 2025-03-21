import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("TOKEN")


# Define bot intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure commands are properly synced
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=None)  # Force sync application commands
        print(f"✅ Slash commands synced! Logged in as {bot.user}")
    except Exception as e:
        print(f"⚠️ Failed to sync commands: {e}")
# Define the required role name
REQUIRED_ROLE = 'CTF Admin'

def has_required_role(interaction: discord.Interaction) -> bool:
    """Check if the user has the required role."""
    if interaction.user is None:
        return False
    return any(role.name == REQUIRED_ROLE for role in interaction.user.roles)
# Define the slash command for upcoming CTF events
@bot.tree.command(name="upcoming_ctfs", description="Displays upcoming CTF events.")
async def upcoming_ctfs(interaction: discord.Interaction, limit: int = 5):
    """
    Fetches and displays upcoming CTF events from CTFtime.
    
    :param interaction: The interaction object for the command.
    :param limit: The number of events to display (default is 5).
    """
    current_time = int(datetime.utcnow().timestamp())
    api_url = f"https://ctftime.org/api/v1/events/?limit={limit}&start={current_time}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        events = response.json()

        if not events:
            await interaction.response.send_message("No upcoming CTF events found.")
            return

        # Create a single embed to hold all events
        embed = discord.Embed(
            title="Upcoming CTF Events",
            color=discord.Color.blue(),
            description="Here are the upcoming CTF competitions from CTFtime:"
        )

        for event in events:
            title = event.get('title', 'N/A')
            url = event.get('url', 'N/A')
            start_str = event.get('start', 'N/A')
            finish_str = event.get('finish', 'N/A')

            # Convert timestamps to UNIX timestamps and format for Discord
            if start_str != 'N/A':
                dt_start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S%z")
                start = f"<t:{int(dt_start.timestamp())}:F>"
            else:
                start = "N/A"

            if finish_str != 'N/A':
                dt_finish = datetime.strptime(finish_str, "%Y-%m-%dT%H:%M:%S%z")
                finish = f"<t:{int(dt_finish.timestamp())}:F>"
            else:
                finish = "N/A"

            # Add event details as a field in the embed
            embed.add_field(
                name=f"🔹 [{title}]({url})",
                value=f"**Start:** {start}\n**End:** {finish}",
                inline=False
            )

        embed.set_footer(text="Data provided by CTFtime.org")
        await interaction.response.send_message(embed=embed)

    except requests.RequestException as e:
        await interaction.response.send_message(f"An error occurred while fetching CTF events: {e}")


# Define the slash command for team info with scraping of additional details
@bot.tree.command(name="team_info", description="Displays information about a specific CTF team, including members and upcoming events.")
async def team_info(interaction: discord.Interaction, team_id: int = 370924):
    """
    Fetches and displays information about a specific CTF team from CTFtime,
    including their current members and planned participation in upcoming events.

    :param interaction: The interaction object for the command.
    :param team_id: The ID of the team to retrieve information for.
    """
    api_url = f"https://ctftime.org/api/v1/teams/{team_id}/"
    team_page_url = f"https://ctftime.org/team/{team_id}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        # Fetch team information from the API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        team = response.json()

        # Extract team details
        name = team.get('name', 'N/A')
        country = team.get('country', 'N/A')
        logo = team.get('logo', None)
        description = team.get('description', 'No description available.')
        website = team.get('website', 'N/A')
        aliases = team.get('aliases', [])

        # Create an embed to display team information
        embed = discord.Embed(
            title=name,
            description=description,
            color=discord.Color.blue()
        )
        if logo:
            embed.set_thumbnail(url=logo)
        embed.add_field(name="Country", value=country, inline=True)
        embed.add_field(name="Website", value=website, inline=True)
        embed.add_field(name="Aliases", value=', '.join(aliases) if aliases else 'None', inline=False)

        # Fetch the team's webpage to scrape additional information
        page_response = requests.get(team_page_url, headers=headers)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.content, 'html.parser')

        # Scrape current team members
        members_section = soup.find('div', id='recent_members')
        if members_section:
            members_table = members_section.find('table', class_='table table-striped')
            if members_table:
                members = [row.get_text(strip=True) for row in members_table.find_all('tr')]
                embed.add_field(name="Current Members", value=', '.join(members) if members else 'None', inline=False)

        # Scrape planned participation in upcoming CTF events
        events_section = soup.find('h3', string='Plan to participate in CTF events')
        if events_section:
            events_table = events_section.find_next('table', class_='table table-striped')
            if events_table:
                events = []
                for row in events_table.find_all('tr')[1:]:  # Skip header row
                    columns = row.find_all('td')
                    if len(columns) == 2:
                        event_name = columns[0].get_text(strip=True)
                        event_date = columns[1].get_text(strip=True)
                        events.append(f"{event_name} - {event_date}")
                embed.add_field(name="Planned CTF Participation", value='\n'.join(events) if events else 'None', inline=False)

        embed.set_footer(text="Data provided by CTFtime.org")
        await interaction.response.send_message(embed=embed)

    except requests.RequestException as e:
        await interaction.response.send_message(f"An error occurred while fetching team information: {e}")
    except ValueError:
        await interaction.response.send_message("Invalid response received from CTFtime API.")
@bot.tree.command(name="ctf_info", description="Announces a CTF event in the current channel.")
@app_commands.checks.has_role("CTF Admin")  # Replace with your role name
@app_commands.describe(event_id="The CTFtime Event ID")
async def create_ctf(interaction: discord.Interaction, event_id: int):
    if not interaction.guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    # Defer response early to prevent timeout
    if not interaction.response.is_done():
        await interaction.response.defer()

    api_url = f"https://ctftime.org/api/v1/events/{event_id}/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        event = response.json()

        title = event.get('title', 'N/A')
        url = event.get('url', 'N/A')
        description = event.get('description', 'No description available.')
        start = event.get('start', 'N/A')
        finish = event.get('finish', 'N/A')
        duration = event.get('duration', {})
        duration_days = duration.get('days', 0)
        duration_hours = duration.get('hours', 0)
        duration_minutes = duration.get('minutes', 0)
        is_online = event.get('onsite', False)
        location = event.get('location', 'N/A') if is_online else 'Online'
        format = event.get('format', 'N/A')
        logo = event.get('logo', None)

        start_str = f"<t:{int(datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z').timestamp())}:F>" if start != 'N/A' else 'N/A'
        finish_str = f"<t:{int(datetime.strptime(finish, '%Y-%m-%dT%H:%M:%S%z').timestamp())}:F>" if finish != 'N/A' else 'N/A'

        embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), url=url)
        if logo:
            embed.set_thumbnail(url=logo)
        embed.add_field(name="Start Time", value=start_str, inline=True)
        embed.add_field(name="Finish Time", value=finish_str, inline=True)
        embed.add_field(name="Duration", value=f"{duration_days}d {duration_hours}h {duration_minutes}m", inline=True)
        embed.add_field(name="Format", value=format, inline=True)
        embed.add_field(name="Location", value=location, inline=True)
        embed.set_footer(text="Data provided by CTFtime.org")

        await interaction.followup.send(embed=embed)
    except requests.RequestException as e:
        await interaction.followup.send(f"An error occurred while fetching event information: {e}")
    except ValueError:
        await interaction.followup.send("Invalid response received from CTFtime API.")




# 🔥 Global Error Handler for Missing Role
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole) or isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message("❌ You do not have permission to use this command!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ An error occurred while processing the command.", ephemeral=True)


# Run the bot with your token
bot.run(token)
