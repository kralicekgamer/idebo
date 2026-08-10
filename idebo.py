import os
import configparser

from mpvnet_cz_api import Api

reset = "\033[0m"
red = "\033[31m"
blue = "\033[34m"

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if config["Config"]["HomeStop"] == "0":
        print("Configure me in config.ini.")
        exit()

    api = Api(config["Config"]["HomeStop"], config["Config"]["Operator"])
    data = api.sync()

    data = data[:int(config["Config"]["NumberOfConnections"])]

    for connection in data:
        if connection["line"] in ("1", "2", "3", "5", "11", "X2", "X3", "X5", "X11"):
            print(f"""
[{red}Tram {connection["line"]}{reset}] 
{connection["departure"]} {connection["destination"]}""")

        else:
            print(f"""
[{blue}Bus {connection["line"]}{reset}] 
{connection["departure"]} {connection["destination"]}""")

if __name__ == "__main__":
    main()