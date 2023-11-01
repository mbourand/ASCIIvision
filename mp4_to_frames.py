import cv2

def parse_mp4(video_path: str):
	vidcap = cv2.VideoCapture(video_path)
	success, image = vidcap.read()
	count = 0
	while success:
		cv2.imwrite(f"frames/{count}.jpg", image)
		success, image = vidcap.read()
		print(f"Converted {count} frames to images")
		count += 1