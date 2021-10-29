from Match import FixedLengthMatch, RankedMatch, AroundTheWorldMatch
from Filepaths import CWD, get_default_directory_os_independent
from PlayerStates import PlayerStates, PlayerState
from SpyPartyReplay import SpyPartyReplay, Player
from tkinter.filedialog import askdirectory
from MatchPublisher import MatchPublisher
from Leaderboard import RankedLeaderboard
from LogObserver import LogObserver
from Config import Config
import tkinter as tk
import pathlib
import os

DEBUG = False


class Ranked(tk.Tk):
    KEYWORD_GAME_DIR = 'SpyParty_directory'

    MATCH_KEYWORDS = {
        'RANKEDON': PlayerStates.READY_RANKED,
        'SWISSRANKEDON': PlayerStates.READY_SWISS,
        # 'RANKEDAROUNDTHEWORLD': PlayerStates.READY_AROUND_THE_WORLD,
    }
    MATCH_FACTORIES = {
        PlayerStates.READY_SWISS: lambda replay: FixedLengthMatch(replay, 8),
        PlayerStates.READY_RANKED: lambda replay: FixedLengthMatch(replay, 12),
        PlayerStates.READY_AROUND_THE_WORLD: lambda replay: AroundTheWorldMatch(replay),
    }

    user_player = Player('player', 'Player')
    user_ready_state: PlayerState = PlayerStates.IN_LOBBY
    oppo_ready_state: PlayerState = PlayerStates.IN_LOBBY
    display_names = {}

    def __init__(self):
        tk.Tk.__init__(self)
        self.title('SpyParty Ranked')
        self.minsize(450, 250)

        self.ranked_config = Config(CWD / 'SpyPartyRanked_config.json', default_config=lambda: {
            self.KEYWORD_GAME_DIR: get_default_directory_os_independent()
        }, load_logging=True)
        self.current_opponent = None
        self.validation_key = None
        self.observer = None
        self.matches = {}

        self.leaderboard = RankedLeaderboard()
        self.leaderboard.refresh()

        toolbar = tk.Menu(self)
        self.config(menu=toolbar)

        menu_file = tk.Menu(toolbar, tearoff=0)
        menu_file.add_command(label="Locate SpyParty Directory", command=self.pick_logs_directory)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.on_window_close)
        toolbar.add_cascade(label="Menu", menu=menu_file)

        menu_ranked = tk.Menu(toolbar, tearoff=0)
        menu_ranked.add_command(label='Refresh Rankings', command=self.refresh_rankings)  # aka "cost Opi $0.0001"
        toolbar.add_cascade(label='Ranked', menu=menu_ranked)

        self.__status_bar = tk.Label(self, text="Finding log...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.__status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        big_frame = tk.Frame(self)
        big_frame.pack(anchor=tk.CENTER)

        self.user_frame = tk.LabelFrame(big_frame, text='Welcome!', width=200)
        self.user_frame.grid(row=0, column=0)
        self.__user_status_label = tk.Label(self.user_frame)
        self.__user_status_label.pack()
        tk.Label(big_frame, text='vs.').grid(row=0, column=1)
        self.oppo_frame = tk.LabelFrame(big_frame, text='No Current Opponent', width=200)
        self.oppo_frame.grid(row=0, column=2)
        self.__oppo_status_label = tk.Label(self.oppo_frame)
        self.__oppo_status_label.pack()

        self.games_listbox = tk.Listbox(big_frame, height=12, width=50)

        self.update_log_observer()

        # since SpyParty updates the log when it loses focus, we can guarantee an up-to-date log by observing it when
        #  the Ranked window gains focus
        self.after(3000, self.bind, "<FocusIn>", self.became_focused)
        # self.after(4, self.became_focused, 0)

    def get_logs_directory(self):
        return pathlib.Path(self.ranked_config[self.KEYWORD_GAME_DIR]) / 'logs'

    def pick_logs_directory(self):
        if path := askdirectory(
                title='Please select your SpyParty folder',
                initialdir=self.ranked_config[self.KEYWORD_GAME_DIR]):
            self.ranked_config[self.KEYWORD_GAME_DIR] = path
            self.update_log_observer()

    def update_log_observer(self):
        latest_file = pathlib.Path(max(all_files_under(self.get_logs_directory()), key=os.path.getmtime))
        if not self.observer or latest_file != self.observer.get_log_path():
            print('NEW LOG', latest_file)
            self.observer = LogObserver(latest_file)
            self.set_program_status(self.observer.name)
            line1, line2 = self.observer.read_lines(limit=2)
            pid = line1.split("PID ")[1].strip()
            local_time = line2.split("Local Time: ")[1].split(", GMT:")[0].strip()
            self.validation_key = pid + local_time
            more_lines = self.observer.read_lines(limit=20)
            for line in more_lines:  # parse out username + display_name
                self.parse(line)
            # skip routine loading information
            self.observer.read_lines_until(lambda log_line: log_line.endswith('Closing splashscreen...\n'))
            return True
        return False

    def became_focused(self, _):
        self.update_log_observer()
        new_lines = self.observer.read_lines()
        for line in new_lines:
            self.parse(line)
        # skip = 3500
        # for line in new_lines[:skip]:
        #     self.parse(line)
        # for i, line in enumerate(new_lines[skip:]):
        #     self.after(i * 10, self.parse, line)

        if DEBUG:
            print()
            print(f'{self.user_player=}')
            print(f'{self.display_names}')
            print(f'{self.current_opponent=}')
            print(f'{self.user_ready_state=}')
            print(f'{self.oppo_ready_state=}')
            print(f'{self.matches=}')
            print(f'{self.leaderboard=}')

    def parse(self, log_line):
        match log_line.split():
            # 2021/09/16-21:51:28-0: Username: s76561198089868938/steam
            # 2021/09/17-19:53:56-0: Username: legorvegenine
            case [_, 'Username:', name]:
                self.user_player = Player(name, name)
                self.update_welcome_message()

            # 2021/09/16-21:51:28-0: Steam Persona Name: Legorve Genine, ID: 76561198089868938
            case [_, 'Steam', 'Persona', 'Name:', *name_parts, 'ID:', _]:
                name = ' '.join(name_parts).rstrip(',')
                self.user_player.display_name = name
                self.update_welcome_message()

            # 2021/09/16-22:04:53-231726: LobbyClient sending chat message "hello!"
            case [_, 'LobbyClient', 'sending', 'chat', 'message', *message_parts]:
                message = unquote(''.join(message_parts))
                if state := self.MATCH_KEYWORDS.get(message):
                    self.set_user_state(state)
                    self.confirm_agreement()

            # todo detect whispers

            # 2021/09/16-22:04:54-232506: LobbyClient message beanie 4 8105 1 "Hiya"
            # 2021/09/16-22:04:58-236094: LobbyClient message <none> 2 0 0 "Other player set spectation game delay."
            # 2021/09/16-22:57:54-991821: LobbyClient message <none> 3 0 0 "peer disconnected"
            # 2021/09/16-22:58:50-1024311: LobbyClient message <none> 7 0 1 "beanie left Lobby."
            case [_, 'LobbyClient', 'message', self.current_opponent, _, _, _, *message_parts]:
                #                              ^ this works wonderfully!
                message = unquote(''.join(message_parts))
                if state := self.MATCH_KEYWORDS.get(message):
                    self.set_opponent_state(state)
                    self.confirm_agreement()

            # 2021/09/16-21:51:57-11624: LobbyClient got client 7902 "cptbasch" "cptbasch", Away
            #   LobbyClient got client 8111 "s76561197988678841/steam" "Crazy Diamond/steam", Joining
            case [_, 'LobbyClient', 'got', 'client', _, username, display_name, _]:
                username, display_name = unquote(username), unquote(display_name)
                self.display_names[username] = display_name.removesuffix('/steam')

            # 2021/09/16-22:57:54-991859: LobbyClient got leave match in IN_LOBBY for match
            #   rPL1Q8qvTsqtS23KPCv1KA, switching to LEAVING_MATCH
            case [_, 'LobbyClient', 'got', 'leave', 'match', 'in', 'IN_LOBBY', 'for', 'match',
                  _, 'switching', 'to', 'LEAVING_MATCH']:  # this one seems a bit excessive...
                self.clear_opponent()
                self.games_listbox.grid_forget()  # hide match listbox
                self.games_listbox.delete(0, tk.END)  # remove listbox entries
                self.set_user_state(PlayerStates.IN_LOBBY)
                self.set_opponent_state(PlayerStates.IN_LOBBY)

            # 2021/09/16-22:04:50-228731: LobbyClient beanie reports v0.1.7269.0
            case [_, 'LobbyClient', opponent_username, 'reports', _]:
                oppo_display_name = self.display_names.get(opponent_username, opponent_username)
                self.current_opponent = Player(opponent_username, oppo_display_name)
                self.update_players(self.leaderboard)

            # 2021/09/16-22:11:54-481310: Writing replay, 338301/628085 packet bytes:
            #   "D:\Game Data\SpyParty\replays\Matches\2021-09\Legorve Genine%2fsteam vs beanie - 20210916-22-04-51\
            #   SpyPartyReplay-20210916-22-06-49-beanie-vs-Legorve Genine%2fsteam-Rj1kQc25Qn6M4xhkorItoQ-v27.replay"
            case [_, 'Writing', 'replay', _, 'packet', 'bytes:', *filepath_parts]:
                replay_filepath = ' '.join(filepath_parts)[1:-1]  # slice off open and close quotes
                try:
                    replay = SpyPartyReplay(replay_filepath)
                    self.handle_replay(replay)
                except SpyPartyReplay.ParsingException as e:
                    print(replay_filepath, e)

    def handle_replay(self, replay: SpyPartyReplay):
        if replay.result == 4:
            print('replay unused (ineligible)')
        elif match := self.matches.get(self.current_opponent):  # match already started, add on
            print('replay added to existing match')
            match.add_game(replay)
            self.listbox_add(match.description(replay))
            self.update_scores(match)
            if match.is_complete():
                self.set_program_status('Uploading match...')
                MatchPublisher.publish(match, self.validation_key, verbose=DEBUG, upload=not DEBUG)
                self.set_user_state(PlayerStates.NOT_READY)
                self.set_opponent_state(PlayerStates.NOT_READY)
                del self.matches[self.current_opponent]
        elif self.user_ready_state is self.oppo_ready_state:  # players are in agreement
            if match_factory := self.MATCH_FACTORIES.get(self.user_ready_state):  # start match, if valid agreement
                print('replay used to start match')
                match = self.matches.setdefault(self.current_opponent, match_factory(replay))
                self.listbox_add(match.description(replay))
                self.update_scores(match)
        else:
            print('replay unused')

    def refresh_rankings(self):
        # refresh the leaderboard then update ratings
        self.leaderboard.refresh(self.update_players)
        # todo has plenty of potential to produce no change:
        #  1) so soon after uploading the match itself
        #  2) both players must have completed their upload to validate the match
        #  maybe worth a 3-5 minute wait? or a refresh button (aka the cost Opi $0.00001 button)

    def update_players(self, lb: RankedLeaderboard):
        self.user_frame['text'] = '%s (%s)' % (
            self.user_player, lb.get_rating(self.user_player, 'Unranked'))
        # todo show minimum/maximum rating deltas during match
        self.oppo_frame['text'] = '%s (%s)' % (
            self.current_opponent, lb.get_rating(self.current_opponent, 'Unranked'))

    def update_scores(self, match: RankedMatch):
        user_score = match.get_player_score(self.user_player)
        self.set_user_state(PlayerStates.SCORE_STATE(user_score))
        oppo_score = match.get_player_score(self.current_opponent)
        self.set_opponent_state(PlayerStates.SCORE_STATE(oppo_score))

    def listbox_add(self, line):
        self.games_listbox.insert(tk.END, line)

    def update_welcome_message(self):
        self.user_frame['text'] = self.user_player.display_name

    def clear_opponent(self):
        self.current_opponent = None
        self.oppo_frame['text'] = 'No Current Opponent'

    def set_user_state(self, state: PlayerState):
        self.set_label_state(self.__user_status_label, state)
        self.user_ready_state = state

    def set_opponent_state(self, state: PlayerState):
        self.set_label_state(self.__oppo_status_label, state)
        self.oppo_ready_state = state

    @staticmethod
    def set_label_state(player_status_label: tk.Label, state: PlayerState):
        player_status_label['text'] = state.text
        player_status_label['fg'] = state.color

    def confirm_agreement(self):
        if self.user_ready_state is self.oppo_ready_state:
            if match_len := self.MATCH_FACTORIES.get(self.user_ready_state):
                print('BOTH', self.user_ready_state)
                self.games_listbox['height'] = match_len
                self.games_listbox.grid(row=1, column=0, columnspan=3)
        elif match := self.matches.get(self.current_opponent):
            print('in hide:', match)
            self.games_listbox.grid_forget()

    def set_program_status(self, status_update):
        self.__status_bar['text'] = status_update

    def on_window_close(self):
        self.ranked_config.save()

        if self.matches:
            print('You still have ongoing matches!')
        else:
            self.destroy()


def unquote(string):
    """Eliminates quotes surrounding a string"""
    return '"'.join(string.split('"')[1:-1])


def all_files_under(path):
    """Iterates through all files that are under the given path."""
    for cur_path, _, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(cur_path, filename)


def main():
    ranked = Ranked()
    try:
        ranked.mainloop()
        # if any problems unexpectedly occur while Ranked is running, dump that to the config
    except Exception as e:
        print(e)
        ranked.ranked_config.default('CRASH REPORT', []).append(str(e))
        ranked.ranked_config.save()


if __name__ == '__main__':
    # pyinstaller --add-data './assets;assets' -n 'ReParty v1.1' -w -F RePartyApplication.py
    # pyinstaller -n 'SpyParty Ranked v3.0.0' -F NewRanked.py
    main()

