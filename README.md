# 🖥️ Discord Wake-on-LAN Bot

A lightweight, reliable Discord bot written in Python that allows you to wake up a computer (via its Ethernet MAC address) by clicking a button in a Discord text channel.

---

## Features

- **No Privileged Intents Required**: The bot runs using default Discord permissions. You do **not** need to enable any privileged gateway intents (like Message Content Intent) in the Discord Developer Portal.
- **Zero Command Setup**: The bot automatically checks your configured Discord channel on startup. If the Wake-on-LAN Control Panel button has not been posted yet, it sends it. If it is already there, it registers the persistent button handler without spamming.
- **Local Message Caching**: Remembers the control panel message ID locally via a `.message_id` file, preventing duplicate posts on bot restarts.
- **Persistent UI Buttons**: The "Wake Server" button survives bot restarts. Once posted, it remains functional forever.
- **Native UDP Packets**: Utilizes Python's standard library `socket` implementation—no third-party CLI wrappers required for WOL broadcasts.
- **Ready for Ubuntu Service**: Easily configured to run in the background 24/7 as a systemd service.

---

## 🛠️ Step 1: Discord Developer Portal Setup

To host the bot, you must register a new Application with Discord:

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** in the top right, choose a name (e.g., `Wake-On-Lan Bot`), and click **Create**.
3. Go to the **Bot** tab on the left sidebar:
   - Click **Add Bot** and confirm.
   - Under **Token**, click **Reset Token** and copy the resulting string. **Save this token securely; it is your `DISCORD_TOKEN`.**
4. Go to the **OAuth2** tab, then select **URL Generator**:
   - In **Scopes**, check `bot`.
   - In **Bot Permissions**, check:
     - `Read Message History` (needed to check for existing buttons by ID)
     - `Send Messages`
     - `Embed Links`
   - Copy the generated URL at the bottom and open it in a new browser tab to invite the bot to your Discord Server.
5. Enable Developer Mode in Discord to get IDs:
   - Go to Discord App settings -> **Advanced** -> toggle **Developer Mode** ON.
   - Right-click the text channel where you want the bot button to live and choose **Copy Channel ID** (this is `DISCORD_CHANNEL_ID`).

---

## 🖥️ Step 2: Target Machine Setup (To be Woken Up)

Wake-on-LAN must be supported and enabled on the hardware level on the target machine you want to wake.

### 1. BIOS/UEFI Settings
- Boot the target computer, enter BIOS/UEFI (usually by pressing `F2`, `F12`, or `Del` on startup).
- Look for settings named:
  - **Wake-on-LAN** (enable)
  - **Power On By PCI-E** (enable)
  - **ErP Ready** (disable, as ErP turns off network card power completely when shutdown)
- Save and exit.

### 2. Operating System Settings

#### For Linux (Ubuntu target):
1. Install `ethtool`:
   ```bash
   sudo apt update && sudo apt install ethtool -y
   ```
2. Find your network interface name:
   ```bash
   ip a
   ```
   *(e.g., `eth0` or `enp3s0`)*
3. Enable Wake-on-LAN for that interface:
   ```bash
   sudo ethtool -s <interface_name> wol g
   ```
4. To make this persistent across reboots, you can create a systemd service or cron job that runs the command above on boot.

#### For Windows target:
1. Open **Device Manager** -> expand **Network adapters**.
2. Right-click your Ethernet adapter (e.g. Intel, Realtek) -> select **Properties**.
3. Under the **Power Management** tab:
   - Check **Allow this device to wake the computer**.
   - Check **Only allow a magic packet to wake the computer**.
4. Under the **Advanced** tab:
   - Find **Wake on Magic Packet** and set it to **Enabled**.
   - Find **Shutdown Wake-On-Lan** and set it to **Enabled**.

---

## 🚀 Step 3: Bot Installation on the Host Ubuntu Machine

Execute these commands on the Ubuntu machine that will host/run the bot:

### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

### 2. Clone/Upload Bot Files
Move this project directory to your Ubuntu machine (e.g. under `/opt/discord-wol-bot` or `/home/ubuntu/discord-wol-bot`).

### 3. Create Virtual Environment and Install Dependencies
Navigate into the bot folder and run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template file to `.env`:
```bash
cp .env.example .env
```
Open `.env` in a text editor (e.g., `nano .env`) and populate the variables:
```env
DISCORD_TOKEN=YOUR_BOT_TOKEN
DISCORD_CHANNEL_ID=YOUR_TEXT_CHANNEL_ID
TARGET_MAC=00:11:22:33:44:55
BROADCAST_IP=255.255.255.255
WOL_PORT=9
```

---

## ⚙️ Step 4: Daemonize as a Systemd Service

To ensure the bot runs in the background and restarts automatically if the Ubuntu machine reboots or the process crashes:

1. Create a new service file:
   ```bash
   sudo nano /etc/systemd/system/discord-wol.service
   ```
2. Paste the following configuration (replace `/home/ubuntu/discord-wol-bot` with the actual path to your bot folder and update the User if not using `ubuntu`):
   ```ini
   [Unit]
   Description=Discord Wake-on-LAN Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/discord-wol-bot
   ExecStart=/home/ubuntu/discord-wol-bot/venv/bin/python bot.py
   Restart=on-failure
   RestartSec=5
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```
3. Save and close (Ctrl+O, Enter, Ctrl+X).
4. Reload the systemd daemon:
   ```bash
   sudo systemctl daemon-reload
   ```
5. Enable the service to run on boot:
   ```bash
   sudo systemctl enable discord-wol.service
   ```
6. Start the service:
   ```bash
   sudo systemctl start discord-wol.service
   ```
7. Check the service status:
   ```bash
   sudo systemctl status discord-wol.service
   ```

To view real-time logs, run:
```bash
journalctl -u discord-wol.service -f
```

---

## 🎮 Step 5: How to Use

1. Start the bot on your Ubuntu host machine (using systemd or running `python bot.py`).
2. The bot will automatically check if it has a saved `.message_id` file.
3. If not found or if the message was deleted from Discord, the bot will post the **Wake Server 🖥️** panel and save the new message ID.
4. Go to that channel in Discord, and click the **Wake Server 🖥️** button!
   - The bot will send a Wake-on-LAN magic packet via UDP broadcast on the Ubuntu host.
   - An ephemeral response (*"Magic packet sent successfully!"*) will appear for you (only you can see this message).
