from SpyPartyReplay import SpyPartyReplay


class RankedMatch:
    def __init__(self, first_game):
        self.player_one = first_game.sniper
        self.player_two = first_game.spy
        self.scores = {self.player_one: 0, self.player_two: 0}
        self.games = []
        self.add_game(first_game)

    def add_game(self, replay: SpyPartyReplay) -> bool:
        self.games.append(replay)
        self.scores[replay.winner] += 1
        return True

    def is_complete(self) -> bool:
        """return True if the match has reached a conclusion, False otherwise."""
        return False  # a default (v1) RankedMatch had no end condition

    def get_player_score(self, username) -> int:
        return self.scores.get(username, -1)

    def get_scores(self) -> tuple[int, int]:
        return self.scores.get(self.player_one), self.scores.get(self.player_two)

    def get_scoreline(self) -> str:
        return '-'.join(map(str, self.get_scores()))

    def get_scoreline_with_names(self) -> str:
        return f'{self.player_one.display_name} {self.get_scoreline()} {self.player_two.display_name}'

    @staticmethod
    def description(game: SpyPartyReplay) -> str:
        return '%s on %s %s (%s)' % (game.spy, game.venue, game.get_setup(), game.get_game_result())

    def __str__(self) -> str:
        return self.get_scoreline_with_names() + str(list(map(self.description, self.games)))

    def __repr__(self) -> str:
        return self.get_scoreline_with_names()


class FixedLengthMatch(RankedMatch):
    def __init__(self, first_game, match_length):
        self.match_length = match_length  # moving this below the super init causes an issue???
        RankedMatch.__init__(self, first_game)

    def is_complete(self):
        return len(self.games) >= self.match_length

    def add_game(self, replay: SpyPartyReplay):
        if replay.result == 4:
            return False  # prevent In Progress games from being added at all
        if self.is_complete():
            return False  # prevent matches from exceeding the match length
        return RankedMatch.add_game(self, replay)


class AroundTheWorldMatch(RankedMatch):
    VENUE_LIST = [
        'Aquarium', 'Balcony', 'Ballroom', 'Courtyard', 'Gallery', 'High-rise',
        'Library', 'Moderne', 'Pub', 'Redwoods', 'Teien', 'Terrace', 'Veranda']

    def __init__(self, first_game):
        RankedMatch.__init__(self, first_game)
        self.combinations = {}
        for venue in self.VENUE_LIST:
            self.combinations[venue, self.player_one] = False
            self.combinations[venue, self.player_two] = False

    def is_complete(self) -> bool:
        return all(self.combinations.values())

    def add_game(self, replay: SpyPartyReplay):
        combination = (replay.venue, replay.spy)
        if self.combinations.get(combination):  # This spy already played a game on this venue
            return False
        self.combinations[combination] = True
        return RankedMatch.add_game(self, replay)


