import os
import pandas as pd
import numpy as np
import json


from scipy.stats import pearsonr

from lookit_info.lookit_json_parser import get_lookit_trial_onsets

from Scripts.video import get_frame_information


# decide whether to get trial onsets from lookit session info or datavyu hand coding
# 'lookit' -> from lookit json info, 'datavyu' -> from datavyu _annotation
# 'compare' -> get both and compare
trial_info_source = 'datavyu'

# This is only relevant if trial_info_source = 'lookit'. if set to true, it's going
# regenerate the json_table from the raw json files. if set to false, it'll try # TODO: retrieve
regenerate_json_table = True

# global directory path variables. make these your folder names under MCS
iCatcher_dir = 'iCatcherOutput'
Datavyu_in = 'InputFiles'
Datavyu_out = 'OutputFiles'
vid_dir = '../iCatcher/videos'


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
def run_analyze_output():

    if trial_info_source == 'lookit':
        if regenerate_json_table:
            #lookit_trial_info = get_lookit_trial_info
        else:
            # load saved lookit session info
            # lookit_trial_info = read_csv('lookit_info/lookit_trial_info.csv')


    for filename in listdir_nohidden(iCatcher_dir):

            input_file, output_file = get_input_output(filename)
            child_id = filename.split('_')[0]

            # get timestamp for each frame in the video
            vid_path = vid_dir + '/' + child_id + ".mp4"
            print('getting frame information for {}...'.format(vid_path))
            timestamps, length, _ = get_frame_information(vid_path)

            # initialize df with time stamps for iCatcher file
            icatcher_path = iCatcher_dir + '/' + filename
            icatcher = read_convert_output(icatcher_path, timestamps)

            if trial_info_source == 'datavyu' or trial_info_source == 'both':

            # get trial onsets and offsets in Datavyu input file, match to iCatcher file
                trial_sets = get_trial_sets_datavyu(input_file)
                assign_trial(icatcher, trial_sets)

                # sum on looks and off looks for each trial
                icatcher_times_w_datavyu_trial_info = get_on_off_times(icatcher)
                handcoded_times = get_output_times(output_file)

                # return comparison metrics
                icatcher_arr, datavyu_arr = np.array(icatcher_times_w_datavyu_trial_info).flatten(), np.array(handcoded_times).flatten()
                stat, p = pearsonr(icatcher_arr, datavyu_arr)
                print('Datavyu total on-off looks per trial: \n', datavyu_times)
                print('iCatcher total on-off looks per trial: \n', icatcher_times)
                print('Pearson R coefficient: {} \np-value: {}'.format(round(stat, 3), round(p, 3)))

            elif trial_info_source == 'lookit' or trial_info_source == 'both':

                # get trial sets from table for current child
                # trial_sets = lookit_trial_info[child_id]

                # get on and off looks for each trial
                # icatcher_times_w_lookit_trial_info = get_on_off_times(icatcher, trial_sets)

                # save icatcher times as csv
                # save(icatcher_times, 'icatcher_times.csv')

            elif trial_info_source == 'both':
                # compare looking times derived from handcoded trial info vs.
                # lookit trial info
                    
                #icatcher_times_w_datavyu_trial_info
                #icatcher_times_w_lookit_trial_info



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

    print(filename)

    # search for corresponding input file in Datavyu folder
    for folder in [Datavyu_in, Datavyu_out]:
        for f in os.listdir(folder):
            print(f)
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
    df = pd.read_csv(filename, names = ['frame', 'on_off'])

    # convert frames to ms using frame rate
    df['time_ms'] = df['frame'].apply(lambda x: stamps[x])
    df['time_ms'] = df['time_ms'].astype(int)

    df['on_off'] = df['on_off'].apply(lambda x: x.strip())
    # df['time'] = df['frame'].apply(lambda x: pd.to_datetime(x / frame_rate, unit='s').strftime('%H:%M:%S.%f'))

    return df


def get_trial_sets_datavyu(input_file):
    """
    Finds corresponding Datavyu input file for given iCatcher output file
    and returns a list of [onset, offset] times for each trial in
    milliseconds

    input_file (string): name of Datavyu input file
    rtype: List[List[int]]
    """
    input_file = Datavyu_in + '/' + input_file
    df = pd.read_csv(input_file)
    df_sets = df[['Trials.onset', 'Trials.offset']]

    df_sets.dropna(inplace=True)

    trial_sets = []
    for _, trial in df_sets.iterrows():
        trial_sets.append([int(trial['Trials.onset']), int(trial['Trials.offset'])])

    return trial_sets


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
    n_trials = len(pd.unique(df['trial']))
    looking_times = [[0, 0] for trial in range(n_trials - 1)]

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
    output_file = Datavyu_out + '/' + output_file
    df = pd.read_csv(output_file)
    df_looks = df[['Looks On Total (s)', 'Looks Off Total (s)']]
    df_looks.dropna(inplace=True)

    looking_times = []
    for _, trial in df_looks.iterrows():
        looking_times.append([round(trial['Looks On Total (s)'], 3), round(trial['Looks Off Total (s)'], 3)])

    return looking_times


if __name__ == "__main__":
    run_analyze_output()
