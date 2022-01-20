import os
import gzip
import json
import requests
import time
from ReplayParser import ReplayParser
from pathlib import Path

###There's some extraneous code in here that stems from the fact that I originally built this to parse the entire file after SpyParty had closed.
###It's a little messy, but it's more work than I'm willing to commit to to rebuild it to be more efficient while parsing constantly instead.

def read_log(log_name, prev_line_count):
    replay_list = []
    matches = {}
    ranked_is_on = False
    swiss_ranked_on = False
    with gzip.open(log_name, 'rt') as file:
        full_match = False
        line_count = 0
        pid = ""
        local_time = ""
        try:
            for line in file:
                line_count += 1
                if line_count == 1:
                    pid = line.split("PID ")[1].strip()
                if line_count == 2:
                    local_time = line.split("Local Time: ")[1].split(", GMT:")[0].strip()
                
                if line_count > prev_line_count:
                    # Turns on ranked when key phrase is found in local chat logs
                    if line.count("SWISSRANKEDON") and line.count("LobbyClient sending chat message"):
                        swiss_ranked_on = True
                        replay_list = []
                    # Turns off ranked when match ends
                    elif line.count("RANKEDON") and line.count("LobbyClient sending chat message"):
                        ranked_is_on = True
                        replay_list = []
                    elif ranked_is_on and line.count("LobbyClient leaving match"):
                        print("Ranked deactivated due to match termination")
                        ranked_is_on = False
                    elif swiss_ranked_on and line.count("LobbyClient leaving match"):
                        print("Ranked deactivated due to match termination")
                        swiss_ranked_on = False
                    # Finds and saves replay paths while ranked is on
                    elif line.count("RANKEDRESUME") and line.count("LobbyClient sending chat message"):
                        ranked_is_on = True
                    elif line.count("SWISSRANKEDRESUME") and line.count("LobbyClient sending chat message"):
                        swiss_ranked_on = True
                    elif line.count("RANKEDUNDO") and line.count("LobbyClient sending chat message"):
                        print("Ranked game undone.")
                        replay_list.pop(-1)
                    elif (ranked_is_on or swiss_ranked_on) and line.count("Writing replay"):
                        replay_find = line.split(": ")
                        path_string = replay_find[2]
                        path_string = path_string.rstrip()
                        path_string = path_string.strip('\"')
                        replay_list.append(path_string)
                    if ranked_is_on and len(replay_list) == 12:
                        ranked_is_on = False
                        full_match = True
                        # Adds the replay list from the parsed match to the match dictionary to dilineate from other
                        # matches in the same log.
                        matches[len(matches)] = replay_list
                        #Clears replay log for other matches.
                        replay_list = []
                    if swiss_ranked_on and len(replay_list) == 8:
                        swiss_ranked_on = False
                        full_match = True
                        matches[len(matches)] = replay_list
                        replay_list = []
        except EOFError as e:
            games_played = len(replay_list)
            validation_key = pid + local_time
            game_closed = False
            return matches, validation_key, full_match, line_count, swiss_ranked_on, ranked_is_on, games_played, game_closed
        games_played = len(replay_list)
        game_closed = True
        validation_key = pid + local_time
    return matches, validation_key, full_match, line_count, swiss_ranked_on, ranked_is_on, games_played, game_closed
    
def get_data(replay, path):
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
    timeline_data = []
    with open(path, 'rb') as replay_file:
        try:
            response = requests.post('https://www.spypartydebrief.com/ranked_parsing', files={'file': replay_file})
            if response.ok:
                print(path, "Success")
                response_data = response.json()
                timeline_data = json.dumps(response_data)
            else:
                print(path, "Failed")
        except Exception as e:
            print(e)
    replay_data['timeline'] = timeline_data
    return replay_data

def find_log_path():
    return rf"{Path.home()}\AppData\Local\SpyParty\logs"

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
        'player_1_score': 0,
        'player_2_score': 0,
        'validation_key': validation_key,
        'game_uuids': []
    }
    player_assignments = (
        ('player_1_id', 'player_1_score'),
        ('player_2_id', 'player_2_score'),
    )
    for game in match_data:
        spy, sniper, result = game['spy_user'], game['sniper_user'], game['result']
        for role, outcomes in (
            (sniper, ('Spy Shot', 'Time Out')),
            (spy, ('Missions Win', 'Civilian Shot')),
        ):
            if result in outcomes:
                for player_id, player_score in player_assignments:
                    if role == formatted_match[player_id]:
                        formatted_match[player_score] += 1
        formatted_match['game_uuids'].append(game['uuid'])
        formatted_match['scoreline'] = str(formatted_match['player_1_score']) + "-" + str(formatted_match['player_2_score'])
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
    URL = "https://cza2vp6wxh.execute-api.us-east-2.amazonaws.com/default/receive_game_data"

    def one_loop(prev_line_count):
        log_path = find_log(parent_dir)
        if log_path and log_path not in finished_logs:
            matches, validation_key, full_match, line_count, swiss_ranked_on, ranked_is_on, games_played, game_closed = read_log(log_path, prev_line_count)
            if full_match:
                for game_list in matches.values(): ###This whole section is to parse full matches and send them in. Should only trigger if there are full matches.
                    if game_list != []:
                        path_dictionary = {}
                        cleaned_replay_dicts = []
                        for replay in game_list:
                            replay_object = hummus.parse(replay)
                            path_dictionary[replay] = replay_object
                        for path in path_dictionary:
                            replay = path_dictionary[path]
                            cleaned_replay_dicts.append(get_data(replay, path))
                        for game in cleaned_replay_dicts:
                            send_data = json.dumps(game)
                            requests.post(url=URL, params={'report_type': 'game_result'}, data=send_data)
                        formatted_match = format_match(cleaned_replay_dicts, validation_key)
                        match_data = json.dumps(formatted_match)
                        requests.post(url=URL, params={'report_type': 'match_result'}, data=match_data)
                        print("###########################")
                        print("Match submitted.")
                        print("Ranked is inactive.")
                    if game_closed == True:
                        with open('read_files.txt', 'a') as write_path:
                            finished_logs.add(log_path)
                            write_path.write(log_path + "\n")
                return line_count
            elif full_match == False:
                print("###########################")
                if ranked_is_on == True:
                    print("Ranked is active.")
                    print("Games played: " + str(games_played))
                elif swiss_ranked_on == True:
                    print("Swiss Ranked is active.")
                    print("Games played: " + str(games_played))
                else:
                    print("Ranked is inactive.")
                return prev_line_count

    line_count = 0
    while running.get_state():
        line_count = one_loop(line_count)
        time.sleep(5)

if __name__ == '__main__':
    main()

