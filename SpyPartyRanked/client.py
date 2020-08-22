from os import walk, path
from Config import Config
from collections import Counter
from ReplayParser import ReplayParser
import PySimpleGUI as sgui
import datetime


start_clock_times = {
    "%d:%02d" % (t // 60, t % 60): t for t in range(0, 400, 15)
}

venue_list = [
    "Aquarium",
    "Balcony",
    "Ballroom",
    "Courtyard",
    "High-Rise",
    "Gallery",
    "Library",
    "Moderne",
    "Pub",
    "Redwoods",
    "Teien",
    "Terrace",
    "Veranda"
]
game_result_list = [
    'Spy Shot',
    'Civilian Shot',
    'Missions Win',
    'Time Out'
]
mission_list = [
    "Bug",
    "Contact",
    "Transfer",
    "Swap",
    "Inspect",
    "Seduce",
    "Purloin",
    "Fingerprint"
]
good_styles = [
    'Reddit',
    'DarkGrey5',
    'DarkGrey6',
    'DarkTeal11',
]

def print_most_common_from_counter(ctr, label=None, indent=" ", n=None):
    if label:
        print(label)
    largest_count_length = len(str(ctr.most_common(1)[0][1]))
    for value, count in ctr.most_common(n=n):
        print(f"{indent}{str(count).rjust(largest_count_length)}x {value}")

def clean_displayname(entry: str, lower=True):
    if entry.endswith("/steam"):
        entry = entry[:-6]
    if lower:
        entry = entry.lower()
    return entry

def locate_replays_directory(def_dir=""):
    new_replays_directory = sgui.popup_get_folder(
        title='Configure Replays Directory',
        message='Please select your directory containing .replay files',
        keep_on_top=True, initial_folder=def_dir, default_path=def_dir
    )
    if new_replays_directory:
        if len(new_replays_directory) > 3:
            return new_replays_directory
        else:
            if sgui.popup_ok_cancel(f'Directory "{new_replays_directory}" was not accepted') == "OK":
                locate_replays_directory(def_dir)

def scan_and_filter_replays(replays_directory, criteria):
    replays = []
    for root, _, files in walk(replays_directory):
        if "/__" in root:
            continue
        for file in files:
            if file.endswith(".replay"):
                file_path = path.join(root, file)
                if len(file_path) > 255:
                    continue
                replays.append(file_path)
    return list(filter(lambda r: all(crit(r) for crit in criteria), map(lambda r: ReplayParser(r).parse(), replays)))

def game_search_window(cfg):
    sgui.theme(cfg["theme"])

    window = sgui.Window(title='ReParty', layout=[
        [
            sgui.Menu([
                ['File', ['Cancel', 'Reset', '---', 'Exit', ]],
                ['Edit', ['Clear Entries', 'Paste', ['Special', 'Normal', ]]],
                ['Configure', ['Replays Directory', 'Choose Style', good_styles]],
                ['Help', 'About...'],
            ])
        ],
        [
            sgui.Text(" Players:"),
            sgui.Input(size=(22, 1), key='alias_left', default_text=''),
            sgui.Button('vs', tooltip='Click to swap the player entries.', key='button_flip'),
            sgui.Input(size=(22, 1), key='alias_right', default_text=''),
            sgui.Text("as", pad=(0, 0)),
            sgui.Combo(['Either', 'Sniper', 'Spy'], default_value='Either', key='role_matching')
        ],
        [sgui.HorizontalSeparator()],
        [
            sgui.Column([
                [
                    sgui.Button('Venues:', key='venue_selection'),
                    sgui.Text("Any", pad=(0, 4),
                              key='venue_setup_prefix'),
                    sgui.Spin(['X', '2', '3', '4', '5'], pad=(3, 4),
                              initial_value='X',
                              enable_events=True,
                              key='venue_setup_any'),
                    sgui.Text("of", pad=(0, 4)),
                    sgui.Spin(['X', '3', '4', '5', '6', '7', '8'], pad=(3, 4),
                              initial_value='X',
                              enable_events=True,
                              key='venue_setup_of')
                ],
                [sgui.Listbox(values=venue_list, size=(20, 8), select_mode='multiple', key='venues_wanted')],
                # [
                #     sgui.Text("Clock: [", pad=(0, 4)),
                #     sgui.Combo(list(start_clock_times), pad=(0, 4),
                #                default_value='0:00'),
                #     sgui.Text(", ", pad=(0, 4)),
                #     sgui.Combo(list(start_clock_times)[::-1], pad=(0, 4),
                #                default_value='6:30'),
                #     sgui.Text("]", pad=(0, 4))
                # ],
                # [
                #     sgui.Text("Guests:   [", pad=(0, 4)),
                #     sgui.Spin([f"0{x}" if x < 10 else str(x) for x in range(3, 22)], pad=(0, 4),
                #               initial_value='03',
                #               enable_events=True,
                #               key='guests_at_least'),
                #     sgui.Text(", ", pad=(0, 4)),
                #     sgui.Spin([f"0{x}" if x < 10 else str(x) for x in range(3, 22)], pad=(0, 4),
                #               initial_value='21',
                #               enable_events=True,
                #               key='guests_at_most'),
                #     sgui.Text("]", pad=(0, 4))
                # ]
            ]),
            sgui.VerticalSeparator(),
            sgui.Column([
                [sgui.Button('Missions:', pad=(3, 4))],
                [
                    sgui.Listbox(mission_list, size=(20, 8),
                                 no_scrollbar=True,
                                 select_mode='multiple',
                                 enable_events=True,
                                 key='missions_wanted')
                ],
                # [
                #     sgui.Text("at least"),
                #     sgui.Spin(tuple(range(0, 9)),
                #               initial_value=0,
                #               enable_events=True,
                #               key='missions_at_least'),
                # ],
                # [
                #     sgui.Text("at most"),
                #     sgui.Spin(tuple(range(0, 9)),
                #               initial_value=8,
                #               enable_events=True,
                #               key='missions_at_most')
                # ]
            ]),
            sgui.VerticalSeparator(),
            sgui.Column([
                [sgui.Button('Results:', pad=(3, 4))],
                [sgui.Listbox(values=game_result_list, size=(20, 4),
                              no_scrollbar=True,
                              select_mode='multiple',
                              key='results_wanted')],
                [sgui.Checkbox(text="Reaches countdown?", pad=(0, 0), key='option_countdown')]
            ]),
            # sgui.ProgressBar(1000, orientation='h', size=(20, 20))
            # sgui.Column([
            #     [
            #         sgui.Column([
            #             [sgui.Text("")],
            #             [sgui.Text("After:")],
            #             [sgui.Text("Before:")],
            #             [sgui.Text("", pad=(0, 2))]
            #         ]),
            #         sgui.Column([
            #             [sgui.Text("Dates:")],
            #             [sgui.Button("Select", key='date_after')],
            #             [sgui.Button("Select", key='date_before')]
            #         ]),
            #         sgui.Column([
            #             [sgui.Text("Times:")],
            #             [sgui.Button("Select", key='time_after')],
            #             [sgui.Button("Select", key='time_before')],
            #         ])
            #     ]
            # ])
        ],
        [sgui.HorizontalSeparator()],
        [
            sgui.Button('Search', key='button_search'),
            sgui.Text('', key='search_progress', size=(20, 1))
        ],
    ])

    replay_batch = []

    while True:
        event, values = window.read()
        if event == sgui.WIN_CLOSED:
            break
        elif event == 'button_flip':
            left, right = values['alias_left'], values['alias_right']
            window['alias_left'](right)
            window['alias_right'](left)

        # elif event == 'venue_selection':
        #     res = venue_select_window(cfg)
        #     print(res)

        # elif event in {'date_after', 'date_before'}:
        #     temp_date = sgui.popup_get_date()
        #     if temp_date:
        #         real_date = "%02d/%02d/%d" % temp_date
        #         window[event](real_date)
        #     else:
        #         window[event]("Select")
        # elif event in {'time_after', 'time_before'}:
        #     pass

        # elif event == 'guests_at_least':
        #     al = values['guests_at_least']
        #     am = values['guests_at_most']
        #     if al > am:
        #         window['guests_at_most'](al)
        # elif event == 'guests_at_most':
        #     al = values['guests_at_least']
        #     am = values['guests_at_most']
        #     if am < al:
        #         window['guests_at_least'](am)

        # elif event == 'missions_at_least':
        #     al = values['missions_at_least']
        #     ms = len(values['missions_wanted'])
        #     if al > ms:
        #         window['missions_at_least'](ms)
        #     else:
        #         am = values['missions_at_most']
        #         if al >= am:
        #             window['missions_at_most'](al)
        # elif event == 'missions_at_most':
        #     am = values['missions_at_most']
        #     ms = len(values['missions_wanted'])
        #     if am >= ms:
        #         window['missions_at_most'](ms)
        #     else:
        #         al = values['missions_at_least']
        #         if al >= am:
        #             window['missions_at_least'](am)

        # elif event == 'missions_wanted':
        #     ms = len(values['missions_wanted'])
        #     window['missions_at_most'](ms)
        #     window['missions_at_least'](ms)

        elif event == 'venue_setup_any':
            setup_any = values['venue_setup_any']
            setup_of = values['venue_setup_of']
            if setup_any > setup_of:
                window['venue_setup_of'](setup_any)
        elif event == 'venue_setup_of':
            setup_any = values['venue_setup_any']
            setup_of = values['venue_setup_of']
            if setup_any != "X" and setup_any > setup_of:
                window['venue_setup_any'](setup_of)

        elif event == 'Replays Directory':
            selected = locate_replays_directory(cfg["replays_directory"])
            if selected:
                cfg["replays_directory"] = selected
        elif event in good_styles:
            cfg["theme"] = event
            sgui.theme(event)
            sgui.popup_ok(
                f"Selected theme: \"{event}\"\nThis will take effect on the next launch.",
                title=""
            )
        elif event == 'Clear Entries':
            window['alias_left']('')
            window['alias_right']('')
            window['role_matching']('Either')
            window['venue_setup_any']('X')
            window['venue_setup_of']('X')
            window['venues_wanted'](venue_list)
            # window['guests_at_least'](0)
            # window['guests_at_most'](0)
            window['missions_wanted'](mission_list)
            # window['missions_at_least'](0)
            # window['missions_at_most'](0)
            window['results_wanted'](game_result_list)
        elif event == 'button_search':
            criteria = []
            alias_left = [clean_displayname(name.strip()) for name in values['alias_left'].split(",") if name]
            alias_right = [clean_displayname(name.strip()) for name in values['alias_right'].split(",") if name]
            role_match = values['role_matching']
            if role_match == 'Spy':
                if alias_left:
                    criteria.append(lambda rep: clean_displayname(rep["sniper_displayname"]) in alias_left)
                if alias_right:
                    criteria.append(lambda rep: clean_displayname(rep["spy_displayname"]) in alias_right)
            elif role_match == 'Sniper':
                if alias_left:
                    criteria.append(lambda rep: clean_displayname(rep["spy_displayname"]) in alias_left)
                if alias_right:
                    criteria.append(lambda rep: clean_displayname(rep["sniper_displayname"]) in alias_right)
            elif role_match == 'Either':
                if alias_left:
                    criteria.append(lambda rep:
                                    clean_displayname(rep["spy_displayname"]) in alias_left or
                                    clean_displayname(rep["sniper_displayname"]) in alias_left)
                if alias_right:
                    criteria.append(lambda rep:
                                    clean_displayname(rep["spy_displayname"]) in alias_right or
                                    clean_displayname(rep["sniper_displayname"]) in alias_right)
            # description = (
            #     f"{alias_left if alias_left else 'Any player'} vs {alias_right if alias_right else 'Any player'}"
            #     f"{f' as {role_match}' if role_match != 'Either' else ''}"
            # )

            setup_any = values['venue_setup_any']
            setup_of = values['venue_setup_of']
            if setup_any == setup_of != "X":
                mode = f"k{setup_any}"
                criteria.append(lambda rep: rep["game_type"] == mode)
                # description += f" {mode}"
            else:
                if setup_any != "X":
                    criteria.append(lambda rep: rep["game_type"][1] == setup_any)
                if setup_of != "X":
                    criteria.append(lambda rep: rep["game_type"][3] == setup_of)
                # if setup_any + setup_of != "XX":
                #     description += f" a{setup_any}/{setup_of}"

            venues_wanted = values['venues_wanted']
            if venues_wanted:
                criteria.append(lambda rep: rep["level"] in venues_wanted)
            # num_venues = len(venues_wanted)
            # if num_venues in {0, len(venue_list)}:
            #     description += " on any venue"
            # elif num_venues == 1:
            #     description += f" on {venues_wanted[0]}"
            # elif num_venues == 2:
            #     description += f" on {venues_wanted[0]} or {venues_wanted[1]}"
            # else:
            #     description += f" on {', '.join(venues_wanted[:-1])}, or {venues_wanted[-1]}"

            # guests_atl, guests_atm = int(values['guests_at_least']), int(values['guests_at_most'])
            # criteria.append(lambda rep: guests_atl <= rep["guest_count"] <= guests_atm)

            missions_wanted = set(values['missions_wanted'])
            if missions_wanted:
                criteria.append(lambda rep: len(missions_wanted - set(rep["completed_missions"])) == 0)
            # miss_atl, miss_atm = values['missions_at_least'], values['missions_at_most']
            # if missions_wanted:
            #     criteria.append(lambda rep:
            #                     miss_atl <= len(set(rep["completed_missions"]) & missions_wanted) <= miss_atm)
            # elif values['missions_at_most']:
            #     criteria.append(lambda rep: len(rep["completed_missions"]) in
            #                     range(miss_atl, miss_atm + 1))
            # if values['missions_at_least']:
            #     description += f" with at least {values['missions_at_least']}"
            #     if values['missions_at_most']:
            #         description += f" and at most {values['missions_at_most']}"
            # elif values['missions_at_most']:
            #     description += f" with at most {values['missions_at_most']}"

            results_wanted = values['results_wanted']
            if results_wanted:
                criteria.append(lambda rep: rep["result"] in results_wanted)
            if values["option_countdown"]:
                criteria.append(lambda rep: len(rep["completed_missions"]) >= int(rep["game_type"][1]))

            window['search_progress']("Scanning replays...please wait")
            replay_batch = scan_and_filter_replays(
                replays_directory=cfg["replays_directory"],
                criteria=criteria
            )
            count = len(replay_batch)
            window['search_progress'].update(f"{count} result{'' if count == 1 else 's'} found")

            if count:
                replay_analysis_window(replay_batch, primary_role=role_match)

    window.close()
def venue_select_window(cfg):
    sgui.theme(cfg["theme"])

    __statue_counts = [0, 2, 4, 6, 7, 8]
    __convo_counts = [1, 2, 3, 4, 5]
    __book_counts = [0, 2, 3]
    __sda_counts = [0, 1, 2, 3]

    window = sgui.Window(title='ReParty: Venue Selection', layout=[
        [
            sgui.Menu([
                ['File', ['Cancel', 'Reset', '---', 'Exit', ]],
                ['Edit', ['Clear Entries', 'Paste', ['Special', 'Normal', ]]],
                ['Configure', ['Replays Directory', 'Choose Style', good_styles]],
                ['Help', 'About...'],
            ])
        ],
        [
            sgui.Column([[
                sgui.Column([
                    [sgui.Text("Viewing Angle:")],
                    [sgui.Text("Conversations:")],
                    [sgui.Text("Bookshelves:")],
                    [sgui.Text("Statues:")],
                    [sgui.Text("\"Minspects\":", tooltip="Minimum statue visits required to complete Inspects")],
                    [sgui.Text("SDAs:", tooltip="Suspected Double Agents")],
                    [sgui.Text("Toby:")]
                ]),
                sgui.Column([
                    [sgui.Combo(['Either', 'High', 'Low'], default_value='Either')],
                    [sgui.Spin(__convo_counts, initial_value=1, key='convos_min'),
                     sgui.Spin(__convo_counts, initial_value=5, key='convos_max')],
                    [sgui.Spin(__book_counts, initial_value=0, key='books_min'),
                     sgui.Spin(__book_counts, initial_value=3, key='books_max')],
                    [sgui.Spin(__statue_counts, initial_value=0, key='statues_min'),
                     sgui.Spin(__statue_counts, initial_value=8, key='statues_max')],
                    [sgui.Combo(['X', '1', '2'], default_value='X', key='minspects')],
                    [sgui.Spin(__sda_counts, initial_value=0, key='sdas_min'),
                     sgui.Spin(__sda_counts, initial_value=3, key='sdas_max')],
                    [sgui.Combo(['Either', 'Waiter', 'Bartender'], default_value='Either')]

                    # sgui.Checkbox("Bookshelf Inspects?", key='books_inspects')
                ])
            ]]),
            sgui.Column([
                [sgui.Multiline(default_text="# TODO PUT VENUE GRID HERE")]
            ]),
        ],
        [
            sgui.Button("Cancel", key='button_cancel'),
            sgui.Button("Submit", key='button_submit')
        ]
    ])

    values = None
    running = True
    while running:
        event, values = window.read()
        if event == "button_submit":
            running = False
        elif event == 'button_cancel':
            break
        elif event == sgui.WIN_CLOSED:
            break
    else:
        # criteria = []
        print(values)
        # return list(filter(None, __venues))

    window.close()
def replay_analysis_window(replays, **params):
    snipers = {}
    spies = {}
    for rep in replays:
        if rep["result"] == "In Progress":
            continue
        spy_win = rep["result"] in {"Missions Win", "Civilian Shot"}
        snipers.setdefault(clean_displayname(rep["sniper_displayname"], lower=False), Counter())[not spy_win] += 1
        spies.setdefault(clean_displayname(rep["spy_displayname"], lower=False), Counter())[spy_win] += 1

    class PlayerResult:
        def __init__(self, name, sn_w, sn_l, sp_w, sp_l):
            self.name = name

            self.sn_w = sn_w
            self.sn_l = sn_l
            self.sn_g = sn_w + sn_l
            self.sn_wr = sn_w / self.sn_g if self.sn_g else None

            self.sp_w = sp_w
            self.sp_l = sp_l
            self.sp_g = sp_w + sp_l
            self.sp_wr = sp_w / self.sp_g if self.sp_g else None

            self.ov_w = sn_w + sp_w
            self.ov_l = sn_l + sp_l
            self.ov_g = self.ov_w + self.ov_l
            self.ov_wr = self.ov_w / self.ov_g

        def overall_wins(self):
            return f"{self.ov_w}W"

        def overall_losses(self):
            return f"{self.ov_l}L"

        def overall_winrate(self):
            return f"{round(100 * self.ov_wr, 1)}%"

        def sniper_wins(self):
            return f"{self.sn_w}W"

        def sniper_losses(self):
            return f"{self.sn_l}L"

        def sniper_winrate(self):
            return f"{round(100 * self.sn_wr, 1)}%" if self.sn_wr is not None else ""

        def spy_wins(self):
            return f"{self.sp_w}W"

        def spy_losses(self):
            return f"{self.sp_l}L"

        def spy_winrate(self):
            return f"{round(100 * self.sp_wr, 1)}%" if self.sp_wr is not None else ""

    data_list = []
    for pl in set(snipers) | set(spies):
        sn_w, sn_l = (snipers[pl][True], snipers[pl][False]) if pl in snipers else (0, 0)
        sp_w, sp_l = (spies[pl][True], spies[pl][False]) if pl in spies else (0, 0)
        data_list.append(PlayerResult(pl, sn_w, sn_l, sp_w, sp_l))

    sn_label = "Snipers"
    sp_label = "Spies"
    # found = False
    # for sn in snipers:
    #     if snipers[sn][True] > 0 or snipers[sn][False] > 0:
    #         if found:
    #             break
    #         found = True
    # else:
    #     display_overall = False
    #     sn_label = "Sniper"
    #
    # found = False
    # for sp in spies:
    #     if spies[sp][True] > 0 or spies[sp][False] > 0:
    #         if found:
    #             break
    #         found = True
    # else:
    #     sp_label = "Spy"
    #     display_overall = False

    p_role = params["primary_role"]
    one_snipe, one_spy = len(snipers) == 1, len(spies) == 1
    if one_snipe + one_spy == 2:
        if p_role == "Spy":
            data_list.sort(key=lambda pr: (pr.sp_w, pr.sp_g) if pr.sp_g else (0, 0), reverse=True)
        elif p_role == "Sniper":
            data_list.sort(key=lambda pr: (pr.sn_w, pr.sn_g) if pr.sn_g else (0, 0), reverse=True)
        elif p_role == "Either":
            print("HOW DID THIS HAPPEN TO ME?")
    elif one_snipe + one_spy == 0:
        data_list.sort(key=lambda pr: (pr.ov_w, pr.ov_g), reverse=True)
    elif one_snipe:
        data_list.sort(key=lambda pr: (pr.sp_w, pr.sp_g) if pr.sp_g else (0, 0), reverse=True)
    elif one_spy:
        data_list.sort(key=lambda pr: (pr.sn_w, pr.sn_g) if pr.sn_g else (0, 0), reverse=True)

    layout = [
        sgui.Menu([
            ['File', ['Cancel', 'Reset', '---', 'Exit', ]],
            ['Edit', ['Clear Entries', 'Paste', ['Special', 'Normal', ]]],
            ['Configure', ['Replays Directory', 'Choose Style', good_styles]],
            ['Help', 'About...'],
        ]),
        sgui.Column([
            [sgui.Button("Players", size=(20, 1), key='sort_alpha')],
            [sgui.Column([[sgui.Text(pr.name, size=(19, 1), justification='right')] for pr in data_list])]
        ])
    ]

    sniper_segment = [
        sgui.VerticalSeparator(),
        sgui.Column([
            [sgui.Button(sn_label, size=(20, 1), key='sort_sniper')],
            [
                sgui.Column([
                    [sgui.Text(pr.sniper_wins(), justification='right', size=(4, 1), pad=(0, 3))]
                    for pr in data_list
                ]),
                sgui.Column([
                    [sgui.Text(pr.sniper_losses(), justification='right', size=(4, 1), pad=(0, 3))]
                    for pr in data_list
                ]),
                sgui.Column([
                    [sgui.Text(pr.sniper_winrate(), justification='right', size=(6, 1), pad=(0, 3))]
                    for pr in data_list
                ])
            ],
        ])
    ]
    spy_segment = [
        sgui.VerticalSeparator(),
        sgui.Column([
            [sgui.Button(sp_label, size=(20, 1), key='sort_spy')],
            [
                sgui.Column([
                    [sgui.Text(pr.spy_wins(), justification='right', size=(4, 1), pad=(0, 3))]
                    for pr in data_list
                ]),
                sgui.Column([
                    [sgui.Text(pr.spy_losses(), justification='right', size=(4, 1), pad=(0, 3))]
                    for pr in data_list
                ]),
                sgui.Column([
                    [sgui.Text(pr.spy_winrate(), justification='right', size=(6, 1), pad=(0, 3))]
                    for pr in data_list
                ])
            ]
        ])
    ]

    if p_role == 'Either':
        layout.extend([
            sgui.VerticalSeparator(),
            sgui.Column([
                [sgui.Button("Overall", size=(20, 1), key='sort_overall')],
                [
                    sgui.Column([
                        [sgui.Text(pr.overall_wins(), justification='right', size=(4, 1), pad=(0, 3))]
                        for pr in data_list
                    ]),
                    sgui.Column([
                        [sgui.Text(pr.overall_losses(), justification='right', size=(4, 1), pad=(0, 3))]
                        for pr in data_list
                    ]),
                    sgui.Column([
                        [sgui.Text(pr.overall_winrate(), justification='right', size=(6, 1), pad=(0, 3))]
                        for pr in data_list
                    ])
                ]
            ])
        ])
        layout.extend(sniper_segment)
        layout.extend(spy_segment)
    elif p_role == 'Sniper':
        layout.extend(sniper_segment)
        layout.extend(spy_segment)
    elif p_role == 'Spy':
        layout.extend(spy_segment)
        layout.extend(sniper_segment)

    window = sgui.Window(title='ReParty: Results', layout=[
        # [sgui.Button()],
        [sgui.Column([layout], scrollable=True)]
    ])

    while True:
        event, values = window.read()
        if event == sgui.WIN_CLOSED:
            break
        # elif event == 'sort_alpha':
        #     pass
        # elif event == 'sort_overall':
        #     pass
        # elif event == 'sort_sniper':
        #     pass
        # elif event == 'sort_spy':
        #     pass
    window.close()
def export_replays_to_practice_set(cfg, replays):
    window = sgui.Window(title='ReParty: Replay Export', layout=[

    ])

    # TODO exports
    #  checkbox for anonimization (scrubs player names)
    #  keep a list of exported sets in the config, allow deletion

    while True:
        event, values = window.read()
        if event == sgui.WIN_CLOSED:
            break
    window.close()


if __name__ == '__main__':
    config = Config("reparty_config.json", default_config={
        "replays_directory": None,
        "theme": 'DarkGrey5',
        "export_directory": None,
    }, load_logging=False)
    sgui.theme(config["theme"])
    if not config["replays_directory"]:
        config["replays_directory"] = locate_replays_directory()

    game_search_window(cfg=config)
    config.save()

#
storage_format = {
    "uuid": {
        ""
    }
}
