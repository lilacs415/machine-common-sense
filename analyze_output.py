import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from scipy.stats import pearsonr

from Scripts.video import get_frame_information

# global directory path variables. make these your folder names under MCS
ICATCHER_DIR = 'iCatcherOutput'

# trial info
TRIAL_INFO_DIR = 'lookit_info/lookit_trial_timing_info.csv'

# directory for videos
VID_DIR = '/nese/mit/group/saxelab/users/galraz/mcs/videos/BBB'

# add absolute path to iCatcher repo
ICATCHER = '/Users/gracesong/dev/iCatcher'
sys.path.append(ICATCHER)

###################
## HELPER FUNCTIONS ##
####################
def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

###################
## ANALYSIS SCRIPT ##
####################
def run_analyze_output(data_filename="BBB_output.csv", session=None):
    """
    Given an iCatcher output directory and Datavyu input and output 
    files, runs iCatcher over all videos in vid_dir that have not been
    already run, computes looking times for all iCatcher outputs, and
    compares with Datavyu looking times. 
    data_filename (string): name of file you want comparison data to be written
            to. Must have .csv ending. 
    session (string): ID of the experiment session. If session is not
            specified, looks for videos only within VID_DIR, otherwise
            searches within [VID_DIR]/session[session]
    """
    for filename in listdir_nohidden(ICATCHER_DIR):
        child_id = filename.split('.')[0]

        # skip if child data already added
        output_file = Path(data_filename)
        if output_file.is_file():
            output_df = pd.read_csv(data_filename, index_col=0)
            ids = output_df['child'].unique()
            if child_id in ids: 
                print(child_id + ' already processed')
                continue
        
        vid_path = VID_DIR + '/'
        if session:
            vid_path += "session" + session + '/'
        vid_path = vid_path + child_id + ".mp4"

        # get timestamp for each frame in the video
        print('getting frame information for {}...'.format(vid_path))
        timestamps, length = get_frame_information(vid_path)
        if not timestamps:
            print('video not found for {} in {} folder'.format(child_id, VID_DIR))
            continue
        
        # initialize df with time stamps for iCatcher file
        icatcher_path = ICATCHER_DIR + '/' + filename
        icatcher = read_convert_output(icatcher_path, timestamps)

        # get trial onsets and offsets from input file, match to iCatcher file
        trial_sets, df = get_trial_sets(child_id)
        assign_trial(icatcher, trial_sets)
        
        # sum on looks and off looks for each trial
        icatcher_times = get_on_off_times(icatcher)
        # datavyu_times = get_output_times(output_file)

        # check whether number of trials from trial info is the same as 
        if icatcher['trial'].max() != len(df):
            print('mismatch in # of trials between icatcher and session info: {} in {} folder'.format(child_id, VID_DIR))
            continue

        write_to_csv(data_filename, child_id, icatcher_times, session, df['fam_or_test'], df['scene'], icatcher)

        # return comparison metrics 
        # icatcher_arr, datavyu_arr = np.array(icatcher_times).flatten(), np.array(datavyu_times).flatten()
        #stat, p = pearsonr(icatcher_arr, datavyu_arr)
       # print('Datavyu total on-off looks per trial: \n', datavyu_times)
      #  print('iCatcher total on-off looks per trial: \n', icatcher_times)
      #  print('Pearson R coefficient: {} \np-value: {}'.format(round(stat, 3), round(p, 3)))


#####################
## HELPER FUNCTIONS ##
#####################

def get_input_output(filename):
    """
    Returns the filenames for the input and output Datavyu files
    corresponding to the iCatcher video coded in filename
    
    filename (string): name of tabulated iCatcher output file in format
    '[CHILD_ID]_annotation.txt'
    rtype: List[string]
    """
    child_id = filename.split('_')[0]
    input_output = []

    # search for corresponding input file in Datavyu folder
    for folder in [DATAVYU_IN, DATAVYU_OUT]:
        for f in os.listdir(folder):
            if child_id in f:
                input_output.append(f)
                break
    if len(input_output) < 2:
        raise Exception('Missing Datavyu files for {}.'.format(child_id))
    return input_output


def read_convert_output(filename, stamps):
    """
    Given a tabular data file containing columns for frames and looks,
    converts to pandas DataFrame with another column mapping each frame
    to its time stamp in the video
    
    filename (string): name of tabulated iCatcher output file in format
    '[CHILD_ID]_annotation.txt'
    stamps (List[int]): time stamp for each frame, where stamps[i] is the 
    time stamp at frame i
    rtype: DataFrame
    """
    npz = np.load(filename)
    df = pd.DataFrame([])

    lst = npz.files

    df['frame'] = range(1, len(npz[lst[0]]) + 1)
    df['on_off'] = ['on' if frame > 0 else 'off' for frame in npz[lst[0]]]
    df['confidence'] = npz[lst[1]]

    # convert frames to ms using frame rate
    df['time_ms'] = stamps
    df['time_ms'] = df['time_ms'].astype(int)
    
    return df


def get_trial_sets(child_id):
    """
    Finds corresponding Datavyu input file for given iCatcher output file
    and returns a list of [onset, offset] times for each trial in 
    milliseconds
    
    input_file (string): name of Datavyu input file
    rtype: List[List[int]]
    """
    df = pd.read_csv(TRIAL_INFO_DIR)

    # get part of df from current child
    df = df[df['child_id'] == child_id] 

    # there's two different file formats -- updated as needed 
    df_sets = df[['relative_onset', 'relative_offset']]
    df_sets = df_sets.rename(columns={"relative_onset": "onset", "relative_offset": "offset"})
    
    df_sets.dropna(inplace=True)

    trial_sets = []
    for _, trial in df_sets.iterrows():
        trial_sets.append([int(trial['onset']), int(trial['offset'])])

    def unique(sequence):
        seen = set()
        return [x for x in sequence if not (tuple(x) in seen or seen.add(tuple(x)))]

    return unique(trial_sets), df


def assign_trial(df, trial_sets):
    """
    Given trial onsets and offsets, makes a 'trial' column in df mapping indicating
    which trial each frame belongs in, or 0 if no trial
    
    df (DataFrame): pandas Dataframe with time information
    trial_sets (List[List[int]]): list of trial [onset, offset] pairs in ms
    rtype: None
    """
    
    # mapping function
    def map_to_range(value, ranges):
        """
        Modifies df to have a column mapping value to one of the ranges provided, or 0 if not 
        """
        for start, end in ranges:
            if value in range(start, end + 1): 
                return ranges.index([start, end]) + 1
        return 0
    # rewrite this with logicals
    df['trial'] = df['time_ms'].apply(lambda x: map_to_range(x, trial_sets))


def get_on_off_times(df):
    """
    Calculates the total on and off look times per trial and returns a list of 
    [on time, off time] pairs for each trial in seconds
    
    df (DataFrame): DataFrame containing trial information per frame
    stamps (List[int]): time stamp for each frame, where stamps[i] is the 
    time stamp at frame i
    rtype: List[List[float]]
    """
    n_trials = df['trial'].max()
    looking_times = [[0, 0] for trial in range(n_trials)]
    
    # separate times by trial
    trial_groups = df.groupby(['trial'])
    for trial_num, group in trial_groups:
        # 0 means does not belong in a trial
        if trial_num == 0:
            continue

        last_look, start_time = None, None

        for index, row in group.iterrows():
            time, look = row['time_ms'], row['on_off']

            # start of on or off look
            if not(last_look and start_time):
                last_look, start_time = look, time
                look_time = 0

            if look == last_look:
                look_time = (time - start_time) / 1000

            # end of a look or end of trial
            else:
                ind = ['on', 'off'].index(last_look)
                looking_times[trial_num - 1][ind] += look_time

                # reset values
                last_look, start_time = None, None

        # special case where entire trial is one look
        if last_look and start_time:
                ind = ['on', 'off'].index(last_look)
                looking_times[trial_num - 1][ind] += look_time   

    looking_times = [[round(on, 3), round(off, 3)] for on, off in looking_times]
    
    return looking_times


def get_output_times(output_file):
    """
    Finds corresponding Datavyu output file for given iCatcher output file
    and returns a list of [on times, off times] for each trial in 
    seconds
    
    output_file (string): name of Datavyu output file
    rtype: List[List[int]]
    """
    output_file = DATAVYU_OUT + '/' + output_file
    df = pd.read_csv(output_file)
    df_looks = df[['Looks On Total (s)', 'Looks Off Total (s)']]
    df_looks.dropna(inplace=True)
     
    looking_times = []
    for _, trial in df_looks.iterrows():
        looking_times.append([round(trial['Looks On Total (s)'], 3), round(trial['Looks Off Total (s)'], 3)])
    
    return looking_times


def write_to_csv(data_filename, child_id, icatcher_data, session, trial_type, stim_type, icatcher):
    """
    checks if output file is in directory. if not, writes new file
    containing looking times computed by iCatcher and Datavyu for child
    with Lookit ID id. 
    
    child_id (string): unique child ID associated with subject
    icatcher_data (List[List[int]]): list of [on times, off times] per trial
                calculated form iCatcher
    datavyu_data (List[List[int]]): list of [on times, off times] per trial
                calculated form iCatcher
    session (string): the experiment session the participant was placed in
    rtype: None
    """
    # assert(len(icatcher_data) == len(datavyu_data))
    num_trials = len(icatcher_data)
    id_arr = [child_id] * len(icatcher_data)
    data = {
        'child': id_arr,
        'session': [session] * num_trials,
        'trial_num': [i + 1 for i in range(len(icatcher_data))],
        'trial_type': trial_type,
        'stim_type': stim_type,
        'confidence': list(icatcher[(icatcher['on_off'] == 'on') & (icatcher['trial'] != 0)].groupby('trial')[['confidence']].mean().squeeze()),
        'iCatcher_on(s)': [trial[0] for trial in icatcher_data],
        'iCatcher_off(s)': [trial[1] for trial in icatcher_data]
    }

    df = pd.DataFrame(data)

    output_file = Path(data_filename)
    if not output_file.is_file():
        df.to_csv(data_filename)
        return
    
    output_df = pd.read_csv(data_filename, index_col=0)
    ids = output_df['child'].unique()

    if child_id not in ids:
        output_df = output_df.append(df, ignore_index=True)
        output_df.to_csv(data_filename)
    

if __name__ == "__main__":
    run_analyze_output()