# Machine Common Sense

## Project Description
Looking behavior is measured and used to explain a large number of phenomena in developmental psychology, especially in the areas of infant attention. To extract the pattern and duration of infant looks, researchers often retroactively annotate experiment videos or rely on tools such as eye trackers.

This repository aims to provide support for an automated workflow for looking time calculation using [iCatcher](https://github.com/yoterel/iCatcher), a CNN classifier for infant eye gaze in low-resolution videos. Specifically, support is provided for calculating aggregate looking times from the frame-based annotations outputted by iCatcher, given information on experiment trial onsets and offsets. Frame rates are extracted using video analysis packages such as ffmpeg to provide timestamps at the millisecond level per annotation. 
