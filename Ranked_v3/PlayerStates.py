from dataclasses import dataclass


@dataclass()
class PlayerState:
    text: str
    color: str

    def __str__(self):
        return self.text

    def __hash__(self):
        return hash(self.text)


class PlayerStates:
    IN_LOBBY = PlayerState('', 'black')
    NOT_READY = PlayerState('NOT READY', '#DC143C')
    READY_SWISS = PlayerState('READY FOR SWISS', '#50C878')
    READY_RANKED = PlayerState('READY FOR RANKED', '#50C878')
    READY_AROUND_THE_WORLD = PlayerState('READY FOR AROUND THE WORLD', '#50C878')

    @staticmethod
    def SCORE_STATE(score):
        return PlayerState(text=score, color='black')
