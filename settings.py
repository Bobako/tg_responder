import configparser

cfg = configparser.ConfigParser()
cfg.read("cfg.ini")
API_ID = cfg["API"]["id"]
API_HASH = cfg["API"]["hash"]

ONLY_USER_MSGS = True

ACTION_DELAY = 5

MSG_MATCH = 0.9  # 0.8
