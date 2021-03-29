import datetime
from pathlib import Path
import pandas as pd


def main():
    vil_pop_max = 9999
    vil_pop_min = 0
    acc_pop_max = 9999
    acc_vil_max = 9999
    vil_growth_max = 0
    acc_growth_max = 0
    my_x = 0
    my_y = 0
    days_to_compare = 2
    server = "ts1.x1.international"
    safety = False
    filter_farmlist = False
    inactives_all_dates = get_lists(days_to_compare, server)
    inverted_inactives_all_dates = [invert_list(my_list) for my_list in inactives_all_dates]
    test_list_inversion(inactives_all_dates[0], inverted_inactives_all_dates[0])

    inactives = invert_list(add_pop_previous_dates(inverted_inactives_all_dates, days_to_compare))
    player_stats = get_player_stats(inactives, days_to_compare)
    filtered_inactives = filter_players(inactives, player_stats, acc_pop_max, acc_growth_max, acc_vil_max)

    no_growth = filter_villages(filtered_inactives, vil_growth_max, vil_pop_max, vil_pop_min)
    if filter_farmlist:
        farms = read_farmlist(server)
        no_growth = filter_farms(no_growth, farms)
    incl_distance = add_distance(no_growth, my_x, my_y)
    sorted_inactives = sort_distance(incl_distance)
    sorted_inactives = add_links(sorted_inactives, server)
    sorted_inactives = translate_tribes(sorted_inactives)

    export_stats(sorted_inactives, server, safety, str(my_x) + "_" + str(my_y))
    export_to_html(server, safety, str(my_x) + "_" + str(my_y))


def read_farmlist(server):
    farms = file_to_2d_list("output/" + server + "_farms_" + str(datetime.date.today()) + ".tsv")[0]
    farms = process_farmlist(farms)
    return farms


def filter_farms(inactives, farms):
    return [inactives[0]] + [vil for vil in inactives[1:] if (int(vil[1]), int(vil[2])) not in farms]


def process_farmlist(farms):
    return [tuple(map(int, farm.replace("'", "").replace("(", "").replace(")", "").split(", "))) for farm in farms]


class Player:
    def __init__(self, p_id, days_to_compare):
        self.id = p_id
        self.villages = []
        self.pop = [0] * days_to_compare
        self.differences = [0] * (days_to_compare-1)


def get_lists(days_to_compare, server):
    inactives_all_dates = []
    for i in range(days_to_compare):
        filename = "input/" + server + "_inactives_" + str(datetime.date.today() - datetime.timedelta(i)) + ".txt"
        if Path(filename).is_file():
            inactives_all_dates.append(file_to_2d_list(filename))
    return inactives_all_dates


def file_to_2d_list(filename):
    text_file = open(filename, "r", encoding="utf-8")
    lines = text_file.readlines()
    my_array = []
    for line in lines:
        my_array.append(line.replace("\n", "").split("\t"))
    return my_array


class ListError(Exception):
    """Base class for other exceptions"""
    pass


def invert_list(my_list):
    inverted_list = []
    for x in range(len(my_list[0])):
        column = []
        for y in range(len(my_list)):
            column.append(my_list[y][x])
        inverted_list.append(column)

    return inverted_list


def test_list_inversion(my_list, my_inverted_list):
    assert(my_list[10][0] == my_inverted_list[0][10])
    assert (my_list[0][10] == my_inverted_list[10][0])
    assert (my_list[10][3] == my_inverted_list[3][10])


def add_pop_previous_dates(inverted_inactives_all_dates, days_to_compare):
    inactives = inverted_inactives_all_dates[0]
    for j in range(1, days_to_compare):
        inactives_previous_date = inverted_inactives_all_dates[j]
        pop_previous_date = ["Pop_" + str(j) + "_days_ago"]
        for i in range(1, len(inactives[0])):
            try:
                index = inactives_previous_date[4].index(inactives[4][i])
                pop_previous_date.append(inactives_previous_date[10][index])
            except ValueError:
                pop_previous_date.append(0)
        inactives.append(pop_previous_date)
        difference = list_subtraction(inactives[10][1:], pop_previous_date[1:], "difference" + str(j))
        inactives.append(difference)
    return inactives


def list_subtraction(list1, list2, title=None):
    title = [] if title is None else [title]
    if len(list1) != len(list2):
        raise ListError("Lists need to be of same length")
    return title + [int(list1[i])-int(list2[i]) for i in range(len(list1))]


def get_player_stats(inactives, days_to_compare):
    inverted_inactives = invert_list(inactives)
    players = set(inverted_inactives[6][1:])
    player_stats = []
    for player in players:
        p = Player(player, days_to_compare)
        for i in range(1, len(inactives)):
            if inactives[i][6] == player:
                p.pop[0] += int(inactives[i][10])
                for j in range(1, days_to_compare):
                    p.pop[j] += int(inactives[i][9+j*2])
                    p.differences[j-1] += int(inactives[i][10+j*2])
                p.villages.append(inactives[i][4])

        player_stats.append(p)
    return player_stats


def filter_players(inactives, player_stats, pop_max=9999, growth_max=9999, vil_max=9999):
    player_ids = [player.id for player in player_stats if player.pop[0] <= pop_max and player.differences[0] <= growth_max and len(player.villages) <= vil_max]
    return [inactives[0]] + [inactives[i] for i in range(1, len(inactives)) if inactives[i][6] in player_ids]


def filter_villages(inactives, growth_max, pop_max, pop_min=0):
    return [inactives[0]] + [inactives[i] for i in range(1, len(inactives)) if int(inactives[i][12]) <= growth_max and pop_min <= int(inactives[i][10]) <= pop_max]


def add_distance(inactives, x, y):
    distance = calculate_distance(inactives, x, y)
    return [inactives[i] + [distance[i]] for i in range(len(distance))]


def calculate_distance(inactives, x, y):
    return ["distance"] + [str(round((abs(int(inactives[i][1]) - x)**2 + abs(int(inactives[i][2]) - y)**2)**0.5, 1)) for i in range(1, len(inactives))]


def sort_distance(inactives):
    table = invert_list(inactives[1:])
    table[-1] = [float(i) for i in table[-1]]
    inv_table = invert_list(table)
    return [inactives[0]] + [inv_table[i] for i in sorted(range(len(table[-1])), key=lambda k: table[-1][k])]


def add_links(inactives, server):
    links = generate_links(inactives, server)
    inactives = invert_list(inactives)
    inactives.append(links)
    return invert_list(inactives)


def generate_links(inactives, server):
    links = ['links']
    for i in range(1, len(inactives)):
        x = inactives[i][1]
        y = inactives[i][2]
        links.append("https://" + server + ".travian.com/karte.php?x=" + str(x) + "&y=" + str(y))
    return links


def translate_tribes(inactives):
    tribes_translation = ["Roman", "Teuton", "Gaul", "Nature", "Natars", "Egyptian", "Huns"]
    for i in range(1, len(inactives)):
        inactives[i][3] = tribes_translation[int(inactives[i][3])-1]
    return inactives


def export_stats(inactives, server, safety, extra=""):
    if extra != "":
        extra += "_"
    if safety:
        with open("output/" + server + extra + "_inactives_" + str(datetime.date.today()) + ".tsv", "x", encoding="utf-8") as file:
            file.writelines('\t'.join(str(j) for j in i) + '\n' for i in inactives)
    else:
        with open("output/" + server + extra + "_inactives_" + str(datetime.date.today()) + ".tsv", "w", encoding="utf-8") as file:
            file.writelines('\t'.join(str(j) for j in i) + '\n' for i in inactives)


def export_to_html(server, safety, extra=""):
    if extra != "":
        extra += "_"

    base_file_name = "output/" + server + extra + "_inactives_" + str(datetime.date.today())
    df = pd.read_csv(base_file_name + ".tsv", sep="\t", header=0)
    df = df.drop(["ID", "VID", "User_ID", "AID"], axis=1)
    df['links'] = df.apply(lambda x: make_clickable(x['links'], x['links']), axis=1)
    if safety:
        with open(base_file_name + ".html", "x", encoding="utf-8") as html_file:
            html_file.write(df.to_html(index=False, escape=False))
    else:
        with open(base_file_name + ".html", "w", encoding="utf-8") as html_file:
            html_file.write(df.to_html(index=False, escape=False))


def make_clickable(url, name):
    return '<a href="{}" rel="noopener noreferrer" target="_blank">{}</a>'.format(url, name)


main()

# Obsolete functions
# def get_new_villages(villages_to_compare):
#     new_villages = []
#     for village in villages_to_compare[0]:
#         if village not in villages_to_compare[1]:
#             new_villages.append(village)
#     return new_villages
#
#
# def get_removed_villages(villages_to_compare):
#     removed_villages = []
#     for village in villages_to_compare[1]:
#         if village not in villages_to_compare[0]:
#             removed_villages.append(village)
#     return removed_villages
#
#
# def get_villages_list(inactives_all_dates):
#     villages_to_compare = []
#     for j in range(len(inactives_all_dates)):
#         inactives = inactives_all_dates[j]
#         villages = []
#         for i in range(1, len(inactives)):
#             if len(inactives[i]) == 11:
#                 villages.append(inactives[i][4])
#             else:
#                 print("failed import: ", str(inactives[i][4]), str(inactives[i][5]))
#         villages_to_compare.append(villages)
#     return villages_to_compare
