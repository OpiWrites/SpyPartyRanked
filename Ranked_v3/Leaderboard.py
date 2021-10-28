from SpyPartyReplay import Player
from dataclasses import dataclass
from collections import Counter
import threading
import requests


class RankedLeaderboard:
    URL = 'https://f0t66fsfkd.execute-api.us-east-2.amazonaws.com/default/receive_game_data'

    def __init__(self):
        self.players = {}
        self.min_rating = 1400
        self.max_rating = 1401
        self.__refreshing = False

    def get_rating(self, player, default=1400):
        if record := self.players.get(player):
            return round(record.elo_rating)
        return default

    # todo add rank imagery
    # DIVISIONS = [
    #     'Bamboo', 'Oak', 'Obsidian', 'Iron', 'Copper',
    #     'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', '#1'
    # ]
    #
    # def get_division_name(self, rating) -> str:
    #     num_divs = len(self.DIVISIONS)
    #     division_index = (rating - self.min_rating) / (self.max_rating - self.min_rating) * num_divs // 1
    #     division_index = min(max(division_index, 0), num_divs - 1)
    #     return self.DIVISIONS[division_index]
    #
    # def get_division_image(self, rating):
    #     div_name = self.get_division_name(rating)
    #     return '%s 447x471.png' % div_name.lower()

    def refresh(self, callback=None):
        if self.__refreshing:
            return

        def __refresh():
            response = requests.get(self.URL, params={'query_type': 'Elo_List'})
            if response.ok:
                for record_json in response.json():
                    match record_json:
                        case {'player_id': username, 'player_display': display_name,
                              'matches_played': matches_played, 'Elo': elo_rating, **opponents}:  # perfection
                            player = Player(username, display_name)
                            rating = float(elo_rating)
                            if rating > self.max_rating:
                                self.max_rating = rating
                            if rating < self.min_rating:
                                self.min_rating = rating
                            self.players[player] = RankedRecord(
                                player, int(matches_played), float(elo_rating), Counter(opponents))
                        case _:
                            print('did not match!', record_json)

                self.max_rating = max(record.elo_rating for record in self.players.values())

                if callback:
                    callback(self)
            self.__refreshing = False

        self.__refreshing = True
        threading.Thread(target=__refresh).start()

    def __repr__(self):
        return str(list(self.players.values()))

    def __str__(self):
        ordered_by_elo = sorted(self.players.values(), key=lambda r: -r.elo_rating)
        longest_name_length = max(len(player.display_name) for player in self.players) if self.players else 0
        percent_string = f'%{longest_name_length}s %d %.1f'
        return 'Ranked Leaderboard\n' + '\n'.join(percent_string % (
            record.player.display_name, record.matches_played, record.elo_rating) for record in ordered_by_elo)


@dataclass
class RankedRecord:
    player: Player
    matches_played: int
    elo_rating: float
    opponents: Counter

    def __str__(self):
        return '%s (%.1f)' % (self.player, self.elo_rating)


def main():
    lb = RankedLeaderboard()
    lb.refresh()
    print(lb)


if __name__ == '__main__':
    main()
