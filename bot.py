import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from wol import send_wol

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('WolBot')

# Load environment variables from .env
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

CHANNEL_ID_STR = os.getenv('DISCORD_CHANNEL_ID')
CHANNEL_ID = int(CHANNEL_ID_STR) if CHANNEL_ID_STR and CHANNEL_ID_STR.strip().isdigit() else None

TARGET_MAC = os.getenv('TARGET_MAC')
BROADCAST_IP = os.getenv('BROADCAST_IP', '255.255.255.255')
WOL_PORT_STR = os.getenv('WOL_PORT')
WOL_PORT = int(WOL_PORT_STR) if WOL_PORT_STR and WOL_PORT_STR.strip().isdigit() else 9

class WolView(discord.ui.View):
    """
    A persistent view that holds the Wake-on-LAN button.
    Being persistent means it will survive bot restarts without needing to recreate the message.
    """
    def __init__(self):
        super().__init__(timeout=None)  # None makes the view persistent

    @discord.ui.button(
        label="Wake Server 🖥️", 
        style=discord.ButtonStyle.green, 
        custom_id="wake_server_button_v1"
    )
    async def wake_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Defer interaction to allow processing time
        await interaction.response.defer(ephemeral=True)
        
        # 2. Check configuration
        if not TARGET_MAC:
            await interaction.followup.send(
                "❌ Error: `TARGET_MAC` is not configured on the bot server.", 
                ephemeral=True
            )
            return

        logger.info(f"Wake-on-LAN button clicked by {interaction.user} (ID: {interaction.user.id})")
        
        # 3. Trigger Wake-on-LAN
        try:
            send_wol(TARGET_MAC, BROADCAST_IP, WOL_PORT)
            await interaction.followup.send(
                f"✅ Magic packet sent successfully to MAC `{TARGET_MAC}`!", 
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to send Wake-on-LAN packet: {e}")
            await interaction.followup.send(
                f"❌ Failed to send Wake-on-LAN packet: {str(e)}", 
                ephemeral=True
            )

class WolBot(commands.Bot):
    """
    The main bot class handling application setup, persistence, and auto-posting the button.
    """
    def __init__(self):
        # Default intents do NOT require privileged gateway intents (no message_content needed)
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the persistent view so the button click events are captured
        self.add_view(WolView())

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Configured MAC Address: {TARGET_MAC or 'None'}")
        logger.info(f"Target Channel ID: {CHANNEL_ID or 'None'}")
        
        # Check and post the button if it is missing from the configured channel
        if CHANNEL_ID:
            try:
                channel = self.get_channel(CHANNEL_ID) or await self.fetch_channel(CHANNEL_ID)
                
                # Check if we have a locally cached message ID
                msg_file_path = os.path.join(os.path.dirname(__file__), '.message_id')
                message_id = None
                if os.path.exists(msg_file_path):
                    with open(msg_file_path, 'r') as f:
                        content = f.read().strip()
                        if content.isdigit():
                            message_id = int(content)
                
                already_posted = False
                if message_id:
                    try:
                        # Fetch the message by ID to see if it still exists.
                        # This works without Message Content Intent!
                        await channel.fetch_message(message_id)
                        already_posted = True
                        logger.info("WOL control panel already exists. Skipping post.")
                    except discord.NotFound:
                        logger.info("WOL control panel message was deleted. Reposting...")
                    except Exception as e:
                        logger.warning(f"Could not verify existing message ID {message_id}: {e}")
                
                if not already_posted:
                    embed = discord.Embed(
                        title="🖥️ Wake-on-LAN Control Panel",
                        description="Click the button below to send a Wake-on-LAN magic packet and turn on the server.",
                        color=discord.Color.dark_green()
                    )
                    embed.add_field(name="Target Machine MAC", value=f"`{TARGET_MAC or 'Not Configured'}`", inline=True)
                    embed.add_field(name="Broadcast Address", value=f"`{BROADCAST_IP}:{WOL_PORT}`", inline=True)
                    embed.set_footer(text="Wake-on-LAN Discord Bot • Ubuntu Service")
                    
                    message = await channel.send(embed=embed, view=WolView())
                    logger.info(f"Sent WOL control panel to channel #{channel.name} ({CHANNEL_ID})")
                    
                    # Save the message ID locally so we don't repost it on next startup
                    with open(msg_file_path, 'w') as f:
                        f.write(str(message.id))
                        
            except Exception as e:
                logger.error(f"Failed to check or post WOL panel to channel {CHANNEL_ID}: {e}")
                
        logger.info("------ Bot is Online ------")

bot = WolBot()

if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_TOKEN environment variable is missing. Check your .env file.")
    else:
        bot.run(TOKEN)
