import os
import sys
import time
import shutil
from tqdm import tqdm
import subprocess
from concurrent.futures import ProcessPoolExecutor

import cv2
import ffmpeg
import numpy as np

# パスの設定
root_path = "/Users/sugawaradaichi/4nonome/py_prac/pyfolder/bad-apple"
name = "【東方】Bad Apple!! ＰＶ【影絵】-FtutLA63Cp8.mkv"
video_path = os.path.join(root_path, f"video/{name}")
music_path = os.path.join(root_path, f"music/badapple.wav")

# 映像情報の取得
video_info = ffmpeg.probe(video_path)
width = video_info["streams"][0]['width']
height = video_info["streams"][0]['height']
# duration = float(video_info["format"]['duration'])
duration = 10


out, _ = (
    ffmpeg
    .input(video_path, ss=0, t=duration)
    .output('pipe:', format='rawvideo', pix_fmt='rgb24')
    .run(capture_stdout=True)
)

arr = (
    np
    .frombuffer(out, np.uint8)
    .reshape([-1, height, width, 3])
)

# ターミナルウィンドウサイズの取得
terminal_size = shutil.get_terminal_size()
fix_height = terminal_size.lines  # 64
fix_width = terminal_size.columns  # 204


frame = arr.shape[0]
text_array = np.full((frame, fix_height, fix_width), None)
for i in tqdm(range(frame)):
    resize_im = cv2.resize(arr[i], dsize=(fix_width, fix_height))
    gray_sca = resize_im[:, :, 0] * 0.299 + \
        resize_im[:, :, 1] * 0.587 + resize_im[:, :, 2] * 0.114
    for j in range(fix_height):
        for k in range(fix_width):
            if 0 <= gray_sca[j, k] < 30:
                text_array[i, j, k] = " "
            elif 30 <= gray_sca[j, k] < 80:
                text_array[i, j, k] = "`"
            elif 80 <= gray_sca[j, k] < 160:
                text_array[i, j, k] = "+"
            else:
                text_array[i, j, k] = "@"

frame_per_time = (duration / frame)


def video():
    global fix_height, text_array, frame, frame_per_time
    base_time = time.time()
    next_time = 0
    back_n = np.array(["\n" for _ in range(fix_height)]).reshape((-1, 1))
    for i in range(frame):
        im = text_array[i]
        text = np.hstack([im, back_n]).reshape(-1)
        sys.stdout.write("\r{}".format("".join(text)))
        sys.stdout.flush()
        next_time = ((base_time - time.time()) % frame_per_time)
        time.sleep(next_time)


def music():
    global music_path
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-hide_banner", music_path],
                        timeout=duration, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print("再生終了")


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as executor:
        executor.submit(music)
        executor.submit(video)


# video(fix_height, text_array, frame, frame_per_time)
# music()

# 時計スレッドを用意、
# 音基準で映像を出力する.  https://python-sounddevice.readthedocs.io/en/0.4.5/usage.html#callback-streams
# await
