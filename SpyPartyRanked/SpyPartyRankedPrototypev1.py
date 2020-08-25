import os
import gzip
from ReplayParser import * ##Import parse function
def read_log(log_name):
    
    replay_list = []
    ranked_is_on = 0
    try:
        with gzip.open(logName, 'rt') as file:
            log_lines = file.readlines()
            for line in log_lines:
                if line.count("Ranked mode on") and line.count("LobbyClient sending chat message") == 1: ##Turns on ranked when key phrase is found in local chat logs
                    ranked_is_on = 1
                    print("Ranked is on")
                elif rankedIsOn == 1 and line.count("LobbyClient starting to lobby from IN_MATCH") == 1: ##Turns off ranked when match ends
                    ranked_is_on = 0
                    print("Ranked is off")
                elif ranked_is_on == 1 and line.count("Writing replay") == 1: ##Finds and saves replay paths while ranked is on
                    replay_find = line.split(": ")
                    path_string = replay_find[2]
                    path_string = path_string.rstrip()
                    path_string = path_string.strip('\"')
                    replay_list.append(path_string) 
                    print("Found replay, saving path")
            file.close
            return replay_list
    except:
        print("SpyParty is running!")

def get_result(replay_path):
    hummus = ReplayParser()
    replay = hummus.parse(replayPath)
    print(replay.venue, replay.spy, replay.sniper, replay.result)

def find_log_path():
    Dir = os.getcwd()
    parent_dir = os.path.dirname(Dir)
    return(parent_dir + "\\logs")

def find_log(log_path):
    last_edited = 0
    log_file = ""
    for file in os.scandir(log_path):
        if os.path.getctime(file) > last_edited:
            last_edited = os.path.getctime(file)
            log_file = os.path.join(log_path, file)
    return log_file      

