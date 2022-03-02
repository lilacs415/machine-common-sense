

# paths
iCatcher_dir = 'iCatcherOutput'

def get_lookit_trial_onsets():

    sessionA_file = open('lookit_info_sessionA.json')
    sessionA_dict = json.load(f)

    sessionB_file = open('lookit_info_sessionB.json')
    sessionB_dict = json.load(f)


    # loop through all child id's in iCatcher directory
    for filename in listdir_nohidden(iCatcher_dir):
        child_id = filename.split('_')[0]

    # find child id in json

    # throw error if child id isn't in json

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
