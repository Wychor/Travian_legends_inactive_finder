from bs4 import BeautifulSoup as bs
import codecs
import datetime


def get_coords(farmlist):
    farms = farmlist.find_all("a", href=True)
    vil_coords = []
    for i in range(0, len(farms), 3):
        text = farms[i]["href"]
        x = text[text.find("x=")+2:text.find("y=")-1]
        y = text[text.find("y=")+2:]
        vil_coords.append((x, y))
    return vil_coords


def export_farms(vil_coords, server):
    with open("output/" + server + "_farms_" + str(datetime.date.today()) + ".tsv", "w", encoding="utf-8") as file:
        file.write('\t'.join(str(j) for j in vil_coords))


def main():
    farmlist = 0
    server = "ts81"
    f = codecs.open("input/" + server + ".html", 'r', encoding="utf8")
    document = bs(f.read(), features="html.parser")
    farms = document.find_all("table")[farmlist]
    coords = get_coords(farms)
    export_farms(coords, server)


main()
