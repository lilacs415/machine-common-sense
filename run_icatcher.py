import os
import subprocess

# change these to your video directory and output directory as needed 
vid_dir = '../TEMP_video'
output_dir = '../Datavyu/iCatcherOutput'

def run_sequential():
    """
    runs iCatcher over all the videos in vid_dir that do not 
    already have an output in output_dir. Writes each annotation
    file as [VIDEO_NAME]_annotation.txt to output_dir
    """
    videos = [v for v in os.listdir(vid_dir)]
    existing_outputs = [f for f in os.listdir(output_dir)]

    def has_vid(name):
        child_id = name.split('.')[0]
        for f in existing_outputs:
            if child_id in f:
                return False
        return True

    # filter out the videos that iCatcher has already run 
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

