import math
import os
import cv2
import numpy as np

from shared import get_sorted_text_files

BRAILLE_WIDTH = 2
BRAILLE_HEIGHT = 4

def num_to_braille(n):
	if n == 0:
		return chr(0x2800 + 1)
	flags = 0
	flags += (n & 0b00001000) << 3
	flags += (n & 0b01110000) >> 1
	flags += n & 0b10000111
	return chr(flags + 0x2800)

def get_braille_pixel_mask(x: int, y: int, value: bool):
	return value << (x * BRAILLE_HEIGHT + y)

def get_edge_braille_character(start_pixel_x: int, start_pixel_y: int, edges: list[int], braille_to_pixel_ratio: tuple[int, int]):
	has_set_braille = False
	braille_nb = 0
	for braille_x_offset in range(BRAILLE_WIDTH):
		for braile_y_offset in range(BRAILLE_HEIGHT):
			total_x_pixel = int(start_pixel_x + (braille_x_offset * braille_to_pixel_ratio[0] / BRAILLE_WIDTH))
			total_y_pixel = int(start_pixel_y + (braile_y_offset * braille_to_pixel_ratio[1] / BRAILLE_HEIGHT))
			if total_x_pixel >= edges.shape[1] or total_y_pixel >= edges.shape[0]:
				total_x_pixel = edges.shape[1] - 1
				total_y_pixel = edges.shape[0] - 1
			is_edge = edges[total_y_pixel, total_x_pixel] > 0
			if is_edge:
				braille_nb |= get_braille_pixel_mask(braille_x_offset, braile_y_offset, True)
				has_set_braille = True

	inverted_braille_nb = (~braille_nb) & 0xFF
	if inverted_braille_nb == 0:
		return num_to_braille(1 << 6)
	return num_to_braille(inverted_braille_nb) if has_set_braille else ' '

def get_color_braille_character(start_pixel_x: int, start_pixel_y: int, image: np.ndarray, braille_to_pixel_ratio: tuple[int, int], color_threshold: int):
	has_set_braille = False
	braille_nb = 0
	for braille_x_offset in range(BRAILLE_WIDTH):
		for braile_y_offset in range(BRAILLE_HEIGHT):
			total_x_pixel = int(start_pixel_x + (braille_x_offset * braille_to_pixel_ratio[0] / BRAILLE_WIDTH))
			total_y_pixel = int(start_pixel_y + (braile_y_offset * braille_to_pixel_ratio[1] / BRAILLE_HEIGHT))
			if total_x_pixel >= image.shape[1] or total_y_pixel >= image.shape[0]:
				total_x_pixel = image.shape[1] - 1
				total_y_pixel = image.shape[0] - 1
			grayscale = image[total_y_pixel, total_x_pixel, :3].mean()
			if grayscale > color_threshold:
				braille_nb |= get_braille_pixel_mask(braille_x_offset, braile_y_offset, True)
				has_set_braille = True

	return num_to_braille(braille_nb) if has_set_braille else num_to_braille(1 << 6)

def get_braille_screen_size(image_width: int, image_height: int, max_characters_per_frame: int, braille_display_aspect_ratio: float):
	"""
		maximiser w tel que :
		w * (w / ratio) < MAX_CHARACTERS_PER_FRAME
	"""
	ratio = image_width / image_height * braille_display_aspect_ratio
	braille_screen_width = math.floor(math.sqrt(max_characters_per_frame * ratio))
	braille_screen_height = int(braille_screen_width / ratio)
	return braille_screen_width, braille_screen_height

def get_image_edges(image: np.ndarray):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	edges = cv2.Canny(gray, 30, 100)
	edges = cv2.blur(edges, (5, 5))
	edges[edges > 0] = 255
	return edges

def compute_text_frame(image: np.ndarray, edges: np.ndarray, braille_to_pixel_ratio: tuple[int, int], color_threshold: int, braille_screen_width: int, braille_screen_height: int):
	edges_text = ""
	color_text = ""
	for pix_y in range(0, int(braille_to_pixel_ratio[1]) * braille_screen_height, int(braille_to_pixel_ratio[1])):
		for pix_x in range(0, int(braille_to_pixel_ratio[0]) * braille_screen_width, int(braille_to_pixel_ratio[0])):
			edges_text += (get_edge_braille_character(pix_x, pix_y, edges, braille_to_pixel_ratio))
			color_text += (get_color_braille_character(pix_x, pix_y, image, braille_to_pixel_ratio, color_threshold))
		edges_text += "\n"
		color_text += "\n"

	merged_text = ""
	for i in range(len(color_text)):
		merged_text += edges_text[i] if edges_text[i] != " " and color_text[i] == num_to_braille(0xFF) else color_text[i]
	return merged_text

def frames_to_textframes(frames_folder: str, text_frames_folder: str, max_characters_per_frame: int, color_threshold: int, braille_display_aspect_ratio: float):
	files = get_sorted_text_files(folder=frames_folder)
	count = 0
	for file in files:
		image = cv2.imread(os.path.join(frames_folder, file))
		image_height, image_width, *_ = image.shape
		edges = get_image_edges(image)

		braille_screen_width, braille_screen_height = get_braille_screen_size(
			image_width,
			image_height,
			max_characters_per_frame,
			braille_display_aspect_ratio
		)

		braille_to_pixel_ratio = (image_width / braille_screen_width, image_height / braille_screen_height)

		text_frame = compute_text_frame(
			image,
			edges,
			braille_to_pixel_ratio,
			color_threshold,
			braille_screen_width,
			braille_screen_height
		)

		with open(os.path.join(text_frames_folder, f"{count}.txt"), "w+", encoding='utf-8') as f:
			f.write(text_frame)

		count += 1
		print(f"Converted {count} images to textframe")