import argparse
import discord
from discord import app_commands, Interaction

import os
import time
from dotenv import load_dotenv
from frames_to_text import frames_to_textframes

from mp4_to_frames import parse_mp4
from shared import get_sorted_text_files

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

FRAMES_FOLDER = os.getenv("FRAMES_FOLDER")
TEXT_FRAMES_FOLDER = os.getenv("TEXT_FRAMES_FOLDER")

TIME_BETWEEN_FRAMES = int(os.getenv('TIME_BETWEEN_FRAMES'))
COLOR_THRESHOLD = int(os.getenv("COLOR_THRESHOLD"))
MAX_CHARACTERS_PER_FRAME = int(os.getenv("MAX_CHARACTERS_PER_FRAME"))

BRAILLE_DISPLAY_RATIO = float(os.getenv("BRAILLE_DISPLAY_RATIO"))


guild = discord.Object(id=GUILD_ID)
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class AntiSpam:
	def __init__(self) -> None:
		self.start = self._current_time()

	def _current_time(self):
		return int(round(time.time() * 1000))

	def time_left(self, cooldown_time: int):
		return (cooldown_time - (self._current_time() - self.start)) / 1000

def get_file_content(file_path: str):
	with open(file_path, "r", encoding='utf-8') as f:
		return f.read()

async def send_video_messages(channel: discord.TextChannel):
	files = get_sorted_text_files(folder=TEXT_FRAMES_FOLDER)

	for file in files:
		anti_spam = AntiSpam()
		file_path = os.path.join(TEXT_FRAMES_FOLDER, file)
		file_content = get_file_content(file_path=file_path)

		await channel.send("```" + file_content + "```")

		time_left = anti_spam.time_left(cooldown_time=TIME_BETWEEN_FRAMES) > 0
		if time_left > 0:
			time.sleep(time_left)
		else:
			print("Late by %d ms" % -time_left)



@tree.command(name="start", description="Starts the video", guild=guild)
async def start(interaction: Interaction):
	await interaction.response.send_message("Starting video...")
	await interaction.delete_original_response()
	await send_video_messages(channel=interaction.channel)

@client.event
async def on_ready():
	print(f"Logged in as {client.user}")
	await tree.sync(guild=guild)

def main():
	arg_parser = argparse.ArgumentParser(description="Converts a video to ascii art", prog="ascii_vision")
	arg_parser.add_argument("--video", help="The video to convert")
	arg_parser.add_argument("--frames-folder", help="The folder where the frames are stored", default=FRAMES_FOLDER)
	arg_parser.add_argument("--text-frames-folder", help="The folder where the textframes are stored", default=TEXT_FRAMES_FOLDER)

	arg_parser.add_argument("--max-characters-per-frame", help="The maximum amount of characters per frame", default=MAX_CHARACTERS_PER_FRAME, type=int)
	arg_parser.add_argument("--braille-display-ratio", help="The ratio of the braille display", default=BRAILLE_DISPLAY_RATIO, type=float)
	arg_parser.add_argument("--color-threshold", help="The color threshold", default=COLOR_THRESHOLD, type=int)
	arg_parser.add_argument("--time-between-frames", help="The time between frames in ms", default=TIME_BETWEEN_FRAMES, type=int)

	arg_parser.add_argument("--to-images", help="Convert the video to jpeg frames", action="store_true")
	arg_parser.add_argument("--to-text", help="Convert the jpeg frames to textframes", action="store_true")
	arg_parser.add_argument("--bot", help="Start the discord bot", action="store_true")

	args = arg_parser.parse_args()

	if not args.to_images and not args.to_text and not args.bot:
		arg_parser.error("No action requested, add at least one of --to_images, --to_text or --bot")
	if args.to_images:
		if not args.video:
			arg_parser.error("No video specified")
		parse_mp4(args.video)
	if args.to_text:
		frames_to_textframes(
			frames_folder=args.frames_folder,
			text_frames_folder=args.text_frames_folder,
			max_characters_per_frame=args.max_characters_per_frame,
			color_threshold=args.color_threshold,
			braille_display_aspect_ratio=args.braille_display_ratio
		)
	if args.bot:
		client.run(DISCORD_TOKEN)

if __name__ == "__main__":
	main()