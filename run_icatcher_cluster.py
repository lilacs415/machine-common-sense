import os
import subprocess

vid_dir = '../../Desktop/TEMP_video'
output_dir = '../../Desktop/Datavyu/iCatcherOutput'

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