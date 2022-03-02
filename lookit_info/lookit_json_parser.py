

# paths
iCatcher_dir = 'iCatcherOutput'

def get_lookit_trial_onsets():

    sessionA_file = open('lookit_info_sessionA.json')
    sessionA_dict = json.load(f)

    sessionB_file = open('lookit_info_sessionB.json')
    sessionB_dict = json.load(f)


    # loop through all child id's in iCatcher directory


    # save file to csv
    # write_csv(lookit_trial_info, 'lookit_trial_info.csv')

    return lookit_trial_info
