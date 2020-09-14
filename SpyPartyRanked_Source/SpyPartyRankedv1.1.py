import os
import gzip
import json
import requests
import time
from SpyPartyRanked_Source.ReplayParser import ReplayParser
from infi.systray import SysTrayIcon
from pathlib import Path

def read_log(log_name):
    replay_list = []
    matches = {}
    ranked_is_on = False
    try:
        with gzip.open(log_name, 'rt') as file:
            line1, line2, *log_lines = file.readlines()
            pid = line1.split("PID ")[1].strip()
            local_time = line2.split("Local Time: ")[1].split(", GMT:")[0].strip()
            validation_key = pid + local_time
            for line in log_lines:
                # Turns on ranked when key phrase is found in local chat logs
                if line.count("RANKEDON") and line.count("LobbyClient sending chat message"):
                    ranked_is_on = True
                    print("Ranked mode on")
                # Turns off ranked when match ends
                elif ranked_is_on and line.count("LobbyClient leaving match"):
                    ranked_is_on = False
                    # Adds the replay list from the parsed match to the match dictionary to dilineate from other
                    # matches in the same log.
                    matches[len(matches)] = replay_list
                    #Clears replay log for other matches.
                    replay_list = []
                    print("Ranked off, saving set data")

                # Finds and saves replay paths while ranked is on
                elif ranked_is_on and line.count("Writing replay"):
                    replay_find = line.split(": ")
                    path_string = replay_find[2]
                    path_string = path_string.rstrip()
                    path_string = path_string.strip('\"')
                    replay_list.append(path_string)
                    print("Replay found, writing path")

        if ranked_is_on and replay_list:
            matches[len(matches)] = replay_list
        return matches, validation_key
    except:
        print("SpyParty is running!")
        return {}, validation_key

def get_data(replay):
    replay_data = replay.to_dictionary(
        spy_username='spy_user', sniper_username='sniper_user',
        spy_displayname='spy_display', sniper_displayname='sniper_display',
        playid=None, variant=None
    )
    replay_data['selected_missions'] = str(replay.selected_missions)
    replay_data['completed_missions'] = (str(replay_data['completed_missions']) if replay.completed_missions else [])
    if replay_data['picked_missions'] is None:
        del replay_data['picked_missions']
    else:
        replay_data['picked_missions'] = str(replay_data['picked_missions']) if replay.picked_missions else []
    return replay_data

def find_log_path():
    return rf"{Path.home()}\AppData\Local\SpyParty\logs"
    # Dir = os.getcwd()
    # parent_dir = os.path.dirname(Dir)
    # return parent_dir + "\\logs"

def find_log(log_path):
    last_edited = 0
    log_file = ""
    for file in os.scandir(log_path):
        if os.path.getctime(file) > last_edited:
            last_edited = os.path.getctime(file)
            log_file = os.path.join(log_path, file)
    return log_file

def format_match(match_data, validation_key):
    formatted_match = {
        'match_id': match_data[0]['uuid'],
        'player_1_id': match_data[0]['sniper_user'],
        'player_1_display': match_data[0]['sniper_display'],
        'player_2_id': match_data[0]['spy_user'],
        'player_2_display': match_data[0]['spy_display'],
        'player_1_totalscore': 0,
        'player_2_totalscore': 0,
        'validation_key' : validation_key
    }

    player_assignments = (
        ('player_1_id', 'player_1_score', 'player_1_totalscore'),
        ('player_2_id', 'player_2_score', 'player_2_totalscore'),
    )

    for game in match_data:
        venue = game['venue']
        if venue not in formatted_match:
            formatted_match[venue] = {}
            formatted_match[venue]['player_1_score'] = 0
            formatted_match[venue]['player_2_score'] = 0
        spy, sniper, result = game['spy_user'], game['sniper_user'], game['result']
        for role, outcomes in (
            (sniper, ('Spy Shot', 'Time Out')),
            (spy, ('Missions Win', 'Civilian Shot')),
        ):
            if result in outcomes:
                for player_id, player_score, player_totalscore in player_assignments:
                    if role == formatted_match[player_id]:
                        formatted_match[venue][player_score] += 1
                        formatted_match[player_totalscore] += 1
    return formatted_match

class State:
    def __init__(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

def main():
    try:
        with open('read_files.txt', 'r') as file:
            finished_logs = {line.strip() for line in file.readlines()}
    except FileNotFoundError:
        with open('read_files.txt', 'w') as file:
            file.write('read files:\n')
            finished_logs = set()

    running = State(True)
    hummus = ReplayParser()
    parent_dir = find_log_path()
    URL = "https://f0t66fsfkd.execute-api.us-east-2.amazonaws.com/default/receive_game_data"

    def one_loop(*_):
        log_path = find_log(parent_dir)
        print(log_path)
        if log_path and log_path not in finished_logs:
            matches, validation_key = read_log(log_path)
            print(validation_key)
            if matches:
                for game_list in matches.values():
                    replay_objects = [hummus.parse(replay, list) for replay in game_list]
                    cleaned_replay_dicts = [get_data(replay) for replay in replay_objects]
                    for game in cleaned_replay_dicts:
                        send_data = json.dumps(game)
                        requests.post(url=URL, params={'report_type': 'game_result'}, data=send_data)
                        print(send_data)
                    formatted_match = format_match(cleaned_replay_dicts, validation_key)
                    match_data = json.dumps(formatted_match)
                    requests.post(url=URL, params={'report_type': 'match_result'}, data=match_data)
                    print(match_data)
            with open('read_files.txt', 'a') as write_path:
                finished_logs.add(log_path)
                write_path.write(log_path + "\n")

    def end_loop(_):
        running.set_state(False)

    stray = SysTrayIcon("k.ico", "SpyParty Ranked", (
         ('Manual Submit', None, one_loop),
    ), on_quit=end_loop, default_menu_index=1)
    stray.start()

    while running.get_state():
        one_loop()
        time.sleep(15)

if __name__ == '__main__':
    main()

