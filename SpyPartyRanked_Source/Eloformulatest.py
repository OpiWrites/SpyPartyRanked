def calc_elo(elo_1, elo_1_venue, elo_2, elo_2_venue, elo_1_wins, elo_2_wins):
    elo_1_change = 0
    elo_1_venue_change = 0
    elo_2_change = 0
    elo_2_venue_change = 0
    iterations = 0
    while iterations < elo_1_wins:
        overall_elo_change = 8*(1-(1/(10**((elo_2-elo_1)/400)+1)))
        venue_elo_change = 8*(1-(1/(10**((elo_2_venue-elo_1_venue)/400)+1)))
        combined_elo_change = (overall_elo_change*.75) + (venue_elo_change*.25)
        elo_1_change += combined_elo_change
        elo_1_venue_change += venue_elo_change
        elo_2_change -= combined_elo_change
        elo_2_venue_change -= venue_elo_change
        iterations += 1
    iterations = 0
    while iterations < elo_2_wins:
        overall_elo_change = 8*(1-(1/(10**((elo_1-elo_2)/400)+1)))
        venue_elo_change = 8*(1-(1/(10**((elo_1_venue-elo_2_venue)/400)+1)))
        combined_elo_change = (overall_elo_change*.75) + (venue_elo_change*.25)
        elo_2_change += combined_elo_change
        elo_2_venue_change += venue_elo_change
        elo_1_change -= combined_elo_change
        elo_1_venue_change -= venue_elo_change
        iterations += 1
    elo_1 += elo_1_change
    elo_1_venue += elo_1_venue_change
    elo_2 += elo_2_change
    elo_2_venue += elo_2_venue_change
    return elo_1, elo_1_venue, elo_2, elo_2_venue

print(calc_elo(1430, 1430, 1368, 1368, 7, 5))
