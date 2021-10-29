from Leaderboard import RankedLeaderboard
from dataclasses import dataclass
from SpyPartyReplay import Player
from Match import FixedLengthMatch


K_VALUE = 32


@dataclass
class EloDelta:
    max_loss: float
    max_gain: float


def get_max_elo_deltas(leaderboard: RankedLeaderboard, match: FixedLengthMatch) -> dict[Player: EloDelta]:
    p1_start_elo = leaderboard.get_rating(match.player_one)
    p2_start_elo = leaderboard.get_rating(match.player_two)
    p1_score, p2_score = match.get_scores()
    remaining_games = match.match_length - p1_score - p2_score

    # ex: score is 2-5, 5 games remain
    # evaluate at 7-5, get p1_elo_max_gain & p2_elo_max_loss
    p1_max_gain, p2_max_loss = evaluate(p1_start_elo, p2_start_elo, p1_score + remaining_games, p2_score)
    # evaluate at 2-10, get p1_elo_max_loss & p2_elo_max_gain
    p1_max_loss, p2_max_gain = evaluate(p1_start_elo, p2_start_elo, p1_score, p2_score + remaining_games)

    return {
        match.player_one: EloDelta(p1_max_loss, p1_max_gain),
        match.player_two: EloDelta(p2_max_loss, p2_max_gain)
    }


def evaluate(elo1, elo2, score1, score2):

    return 0, 0


def expected(rating):
    return 10 ** (rating / 400)


def share(ints):
    total = sum(ints)
    return map(lambda i: i / total, ints)


def elo_value(rating0, rating1):
    score0 = expected(rating0)
    score1 = expected(rating1)
    share0, share1 = share((score0, score1))
    return K_VALUE * share1, K_VALUE * share0



