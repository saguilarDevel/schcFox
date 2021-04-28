import os

os.remove("logs.log")

for file in os.listdir("stats"):
    if file.startswith("stats"):
        os.remove("stats/{}".format(file))
        print("deleted {}".format(file))
