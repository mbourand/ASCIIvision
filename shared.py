import os


def get_sorted_text_files(folder: str):
	files = os.listdir(folder)
	files.sort(key=lambda filename: int(os.path.splitext(filename)[0]))
	return files