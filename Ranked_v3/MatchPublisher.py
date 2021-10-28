from json.decoder import JSONDecodeError
from requests.exceptions import SSLError
from Filepaths import DATA_FOLDER
from Match import RankedMatch
import requests
import json


class MatchPublisher:
    MATCH_REPORT_URL = 'https://f0t66fsfkd.execute-api.us-east-2.amazonaws.com/default/receive_game_data'
    TIMELINE_DATA_URL = 'https://www.spypartydebrief.com/ranked_parsing'

    @staticmethod
    def publish(match: RankedMatch, validation_key: str, verbose=False, upload=True):
        match_id = match.games[0].uuid
        match_data = json.dumps({
            'match_id': match_id,
            'player_1_id': match.player_one.username,
            'player_1_display': match.player_one.display_name,
            'player_1_score': match.scores[match.player_one],
            'player_2_id': match.player_two.username,
            'player_2_display': match.player_two.display_name,
            'player_2_score': match.scores[match.player_two],
            'validation_key': validation_key,
            'game_uuids': [game.uuid for game in match.games],
            'scoreline': match.get_scoreline()
        })
        if verbose:
            print(f'uploading {match_data=}')
        if upload:
            response = requests.post(
                url=MatchPublisher.MATCH_REPORT_URL, params={'report_type': 'match_result'}, data=match_data)
            if response.ok:
                with open(DATA_FOLDER / 'matches_published.txt', 'a') as file:
                    file.write(match_id)
                    file.write('\n')

        for replay in match.games:
            replay_data = replay.to_dictionary(
                spy_username='spy_user', sniper_username='sniper_user',
                spy_displayname='spy_display', sniper_displayname='sniper_display',
                playid=None, variant=None)
            replay_data['selected_missions'] = str(replay.selected_missions)
            replay_data['completed_missions'] = str(
                replay_data['completed_missions']) if replay.completed_missions else []
            if replay_data['picked_missions'] is None:
                del replay_data['picked_missions']
            else:
                replay_data['picked_missions'] = str(replay_data['picked_missions']) if replay.picked_missions else []

            replay_data['timeline'] = []
            with open(replay.filepath, 'rb') as replay_file:
                try:
                    if upload:
                        response = requests.post(MatchPublisher.TIMELINE_DATA_URL, files={'file': replay_file})
                        if response.ok:
                            replay_data['timeline'] = json.dumps(response.json())
                except (SSLError, JSONDecodeError):
                    pass  # the most common, nothing to do about it
                except Exception as e:
                    # if any other kind of exception occurs, I do want to know about that
                    if verbose:
                        print(type(e), e)

            game_data = json.dumps(replay_data)
            if verbose:
                print(f'uploading {game_data=}')
            if upload:
                requests.post(
                    url=MatchPublisher.MATCH_REPORT_URL, params={'report_type': 'game_result'}, data=game_data)
