# source code adapted from Yotam Erel

import subprocess
from pathlib import Path
import json


def get_frame_information(video_file_path):
    commands_list = [
        "ffprobe",
        "-show_frames",
        "-show_streams",
        "-print_format", "json",
        video_file_path
        ]  

    # run command on terminal and store output as a json file
    ffmpeg = subprocess.Popen(commands_list, stderr=subprocess.PIPE, stdout = subprocess.PIPE)
    output, err = ffmpeg.communicate()
    output = json.loads(output)

    # filter out video frame info only 
    video_frames = [frame for frame in output['frames'] if frame['media_type'] == 'video']
    frame_times = [frame["pkt_pts_time"] for frame in video_frames]
    video_stream_info = next(s for s in output['streams'] if s['codec_type'] == 'video')
    assert len(frame_times) == int(video_stream_info["nb_frames"])

    # convert to milliseconds
    frame_times_ms = [int(1000*float(x)) for x in frame_times]
    assert frame_times_ms[0] == 0.0

    # returns timestamps in milliseconds

    return frame_times_ms, int(video_stream_info["nb_frames"]), video_stream_info["time_base"]

# if __name__ == "__main__":
#     vid_path = "../TEMP_video/NFYDcF.mp4"
#     print(get_frame_information(vid_path))