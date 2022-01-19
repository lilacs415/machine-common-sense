import os
import subprocess

vid_dir = '../../Desktop/TEMP_video'
output_dir = '../../Desktop/Datavyu/iCatcherOutput'

videos = [v for v in os.listdir(vid_dir)]
existing_outputs = [f for f in os.listdir(output_dir)]


def has_vid(name):
    child_id = name.split('.')[0]
    for f in existing_outputs:
        if child_id in f:
            return False
    return True


to_run = list(filter(has_vid, videos))

for video in to_run:
    vid_path = vid_dir + '/' + video
    commands_list = [
        "python", "icatcher.py",
        "--source_type", "file",
        vid_path,
        "--show_output",
        "--output_annotation", output_dir,
        "--output_format", "raw_output",
        "--on_off",
        "--model", "icatcher+"
    ]

    result = subprocess.run(commands_list)
    print("The exit code was: {}".format(result.returncode))

print("finished running")

