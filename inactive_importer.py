import requests
from datetime import date

NUMBER_OF_COLUMNS_CONSTANT = 11


def main():
    servers = ["ts1.x1.international"]
    for server in servers:
        raw_map_data = get_map_sql_file(server)
        line_starts, line_ends = find_villages(raw_map_data)
        my_table = make_table(raw_map_data, line_starts, line_ends)
        with open("input/" + server + "_inactives_" + str(date.today()) + ".txt", "x", encoding="utf-8") as file:
            file.writelines('\t'.join(str(j) for j in i) + '\n' for i in my_table)
        with open("map_sql_files/" + server + "_map_sql_" + str(date.today()) + ".txt", "x", encoding="utf-8") as file:
            file.write(raw_map_data)


def get_map_sql_file(subdomain):
    url = "https://" + subdomain + ".travian.com/map.sql"
    r = requests.get(url, allow_redirects=True)
    return r.content.decode("utf-8")


def find_villages(raw_data):
    line_starts = []
    line_ends = []
    end = 0
    while raw_data.find(")", end) != -1:
        start = raw_data.find("(", end)
        line_starts.append(start)
        for i in range(NUMBER_OF_COLUMNS_CONSTANT):
            start = raw_data.find(",", start) + 1
        line_ends.append(raw_data.find(")", start))
        end = raw_data.find(")", start) + 1
    return line_starts, line_ends


def make_table(raw_map_data, line_starts, line_ends):
    column_names = ["ID", "x", "y", "Tribe", "VID", "Village", "User_ID", "Player", "AID", "Alliance", "Pop"]
    my_table = [column_names]
    for i in range(min(len(line_ends), len(line_starts))):
        splitted_row = split_skip(raw_map_data[line_starts[i] + 1:line_ends[i]], ",", "'")
        if len(splitted_row) != NUMBER_OF_COLUMNS_CONSTANT:
            # needs custom error
            print(i)

        for j in range(len(splitted_row)):
            splitted_row[j] = splitted_row[j].replace("'", "")
        my_table.append(splitted_row)
    return my_table


def split_skip(string, split_char, skip_char_start, skip_char_end=None):
    if skip_char_end is None:
        skip_char_end = skip_char_start
    my_list = []
    next_split = string.find(split_char)
    next_skip = string.find(skip_char_start)
    while next_split >= 0:
        if 0 <= next_skip <= next_split:
            start_pos = string.find(skip_char_start)
            end_pos = string[start_pos+1:].find(skip_char_end) + start_pos + 1
            my_list.append(string[:string[end_pos:].find(split_char)+end_pos])
            string = string[string[end_pos:].find(split_char)+end_pos+1:]
        else:
            my_list.append(string[:next_split])
            string = string[next_split+1:]
        next_split = string.find(split_char)
        next_skip = string.find(skip_char_start)

    return my_list


main()
