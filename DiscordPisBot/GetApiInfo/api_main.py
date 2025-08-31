import requests

base_url = "https://www.gamerpower.com/api/filter?platform=epic-games-store.steam"

response = requests.get(base_url)

data = response.json()

def getGamesInfo():
    return data