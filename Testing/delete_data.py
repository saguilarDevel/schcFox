import os


for file in os.listdir("../stats"):
    if file.startswith("stats"):
        os.remove("stats/{}".format(file))
        print("deleted {}".format(file))
