import os

for file in os.listdir("stats"):
    if file.startswith("LoPy"):
        os.remove("stats/{}".format(file))
