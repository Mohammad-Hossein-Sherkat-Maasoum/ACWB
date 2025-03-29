import discord
import aiohttp
from io import BytesIO
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

# Discord bot token and server/channel IDs
TOKEN = "شسیشسیشسیشسیشسیشسیشسیشسی"
GUILD_ID = 1071754085361008690  # Server ID
WELCOME_CHANNEL_ID = 1072197211766657024  # Welcome channel ID

# File paths for images and font
WELCOME_IMAGE_PATH = "welcome_image.jpg"  # Background image for welcome message
DEFAULT_AVATAR_PATH = "default_avatar.jpg"  # Default avatar
EXTRA_IMAGE_PATH = "extra_image.png"  # Additional image to be placed below text
FONT_PATH = "Vazir-Bold.ttf"  # Persian font for text

# Set up Discord intents
intents = discord.Intents.default()
intents.members = True  # Required to detect new member joins

# Initialize Discord client
client = discord.Client(intents=intents)

async def get_user_avatar(user):
    """Download the user's avatar, or return None if no avatar exists."""
    try:
        if user.avatar:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.avatar.url)) as resp:
                    if resp.status == 200:
                        avatar_data = await resp.read()
                        return Image.open(BytesIO(avatar_data)).convert("RGBA")
        return None
    except Exception as e:
        print(f"Error downloading avatar: {e}")
        return None

async def create_welcome_image(user):
    """Create a welcome image with the user's avatar, default avatar, and welcome text."""
    try:
        # Load the user's avatar (if exists)
        user_avatar = await get_user_avatar(user)

        # Load the default avatar and mirror it
        default_avatar = Image.open(DEFAULT_AVATAR_PATH).convert("RGBA")
        default_avatar = ImageOps.mirror(default_avatar)

        # Resize the avatars
        if user_avatar:
            user_avatar = user_avatar.resize((115, 115), Image.Resampling.LANCZOS).convert("RGBA")
        default_avatar = default_avatar.resize((155, 155), Image.Resampling.LANCZOS).convert("RGBA")

        # Load the background image
        base_image = Image.open(WELCOME_IMAGE_PATH).convert("RGBA")
        base_image = base_image.resize((600, 400), Image.Resampling.LANCZOS).convert("RGBA")
        canvas = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        canvas.paste(base_image, (0, 0))

        # Position the user's avatar (top-left)
        if user_avatar:
            user_avatar_x = 60
            user_avatar_y = 50
            canvas.paste(user_avatar, (user_avatar_x, user_avatar_y), user_avatar)

        # Position the default avatar (top-right)
        default_avatar_x = base_image.width - default_avatar.width - 40
        default_avatar_y = 30
        canvas.paste(default_avatar, (default_avatar_x, default_avatar_y), default_avatar)

        # Set up the welcome text
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.truetype(FONT_PATH, 35)

        # Welcome message in Persian
        welcome_text = f"سلام {user.name} خوش اومدی!\nاز الآن عضو کُلایدر آرمی هستی!"
        reshaped_text = get_display(reshape(welcome_text))
        
        # Calculate text size
        lines = reshaped_text.split('\n')
        line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
        total_text_height = sum(line_heights) + (len(lines) - 1) * 10

        text_y = (base_image.height - total_text_height) // 2 + 20  # Move text slightly lower
        current_y = text_y
        for line in lines:
            text_width = draw.textbbox((0, 0), line, font=font)[2]
            text_x = (base_image.width - text_width) // 2  # Center text horizontally
            draw.text((text_x, current_y), line, font=font, fill="white")
            current_y += line_heights[0] + 10

        # Load and position extra image below text
        if os.path.exists(EXTRA_IMAGE_PATH):
            extra_image = Image.open(EXTRA_IMAGE_PATH).convert("RGBA")
            extra_size = int(min(base_image.width // 6, base_image.height // 6) * 1.25)  # Increase size by 5%
            extra_image = extra_image.resize((extra_size, extra_size), Image.Resampling.LANCZOS)
            extra_x = (base_image.width - extra_size) // 2
            extra_y = current_y - 15  # Move image slightly lower
            canvas.paste(extra_image, (extra_x, extra_y), extra_image)

        # Save the image
        output_path = f"welcome_{user.id}.png"
        canvas.save(output_path, "PNG")
        return output_path

    except Exception as e:
        print(f"Error creating welcome image: {e}")
        return None

@client.event
async def on_ready():
    print(f"{client.user} is online and ready!")

@client.event
async def on_member_join(member):
    """Send a welcome message with an image when a new member joins."""
    if member.guild.id != GUILD_ID:
        return

    welcome_channel = client.get_channel(WELCOME_CHANNEL_ID)
    if not welcome_channel:
        print("❌ Welcome channel not found!")
        return

    welcome_image_path = await create_welcome_image(member)
    if welcome_image_path and os.path.exists(welcome_image_path):
        await welcome_channel.send(f"🎉 {member.mention} خوش اومدی!", file=discord.File(welcome_image_path))
        os.remove(welcome_image_path)
    else:
        await welcome_channel.send(f"🎉 {member.mention} خوش اومدی! (Could not generate welcome image.)")

# Run the bot
client.run(TOKEN)
