import json


data = json.load(open('heroes.json', 'rb'))['result']['heroes']

heroes = {}

for x in data:
  heroes[x['id']] = {
    'name': x['name'],
    'localized_name': x['localized_name']
  }
