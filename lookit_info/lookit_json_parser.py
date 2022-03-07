from datetime import datetime 
import pandas as pd
from string import digits


iCatcher_dir = 'iCatcherOutput'

def get_lookit_trial_onsets():

    f = open('lookit_info/lookit_info_sessionA.json')
    sessionA_info = json.load(f)

    f = open('lookit_info/lookit_info_sessionB.json')
    sessionB_info = json.load(f)

    # combine info from both sessions
    dictionaries_combined = sessionA_info + sessionB_info

    # dataframe in which info will be accumulated
    trial_timing_info = pd.DataFrame()

    for session_info in dictionaries_combined:

        # get key of recording start
        recording_start_key = [v for v in session_info['exp_data'].keys() if v.endswith('start-recording-with-image')] 
        
        # only continue if this part of the dictionary has a 'start-recording-with-image' frame
        if recording_start_key:
            child_id = session_info['child']['hashed_id']     

            # timestamp of start of recording
            video_onset = datetime.fromisoformat(session_info['exp_data'][recording_start_key[0]]['eventTimings'][5]['timestamp'][0:-1])

            # create dict, which has 5 columns: child id, recording onset, trial type, 
            # absolute trial onset, relative trial onset and trial number
            trial_timestamps = \
                [{'child_id': child_id, 'video_onset': video_onset, 'trial_type': key, \
                                'absolute_onset': datetime.fromisoformat(value['eventTimings'][2]['timestamp'][0:-1]), \
                                'absolute_offset': datetime.fromisoformat(value['eventTimings'][-3]['timestamp'][0:-1])} \
                                for key, value in session_info['exp_data'].items() \
                                    # get fam and test trials (but not attention getters)
                                    if ('fam' in key or 'test' in key) and 'attention' not in key] 

            trial_timing_info = trial_timing_info.append(pd.DataFrame(trial_timestamps))

    
    # get trial onset/offset relative to onset of video recording
    trial_timing_info['relative_onset'] = trial_timing_info['absolute_onset'] - trial_timing_info['video_onset']
    trial_timing_info['relative_offset'] = trial_timing_info['absolute_offset'] - trial_timing_info['video_onset']
    
    # clean up trial type to be ready for parsing
    trial_timing_info['trial_type'] = trial_timing_info['trial_type'].str.replace('\d+-', '')

    # parse trial type into fam vs. test and scene
    trial_timing_info[['fam_or_test', 'scene']] = trial_timing_info['trial_type'].str.split('-', 1, expand = True)

    # sort whole df by trial onset
    trial_timing_info.sort_values(by='absolute_onset', inplace=True)

    # get trial number using absolute onsets
    trial_timing_info['trial_number'] = trial_timing_info.groupby('child_id').cumcount()+1





        # throw error if child id isn't in json
        if child_id not in sessionA_dict or sessionB_dict:
            raise Exception('child id not found in lookit info')


    # goal is to reformat dict such that key is child_id, and value is trial sets (in ms)
    # alternatively: make it a pandas dataframe where columns are child id, and rows are onset offset onffset etc.
    # think about to what extent it's worth it to extract trial info here
    # (because we could derive this from the condition of the subject which is recorded in the log,
    # however condition alone doesn't account for e.g. repeated trials and other funky things that might happen during the session)

    # 1. find start-image-recording timestamps and save it as t = 0
    # 2. find all other starts and stops of relevant trials (all fam and test trials)
    # 3. calculate their timestamps in ms from t=0
    # 4.
    #


    # save file to csv
    # write_csv(lookit_trial_info, 'lookit_trial_info.csv')

    return lookit_trial_info
