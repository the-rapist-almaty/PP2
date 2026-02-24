import json

with open('sample-data.json', 'r') as file:
    data = json.load(file)


print('''

Interface Status
================================================================================
DN                                                 Description           Speed    MTU  
-------------------------------------------------- --------------------  ------  ------''')
for i in range(len(data["imdata"])):
    beautiful = ''
    if len(data["imdata"][i]["l1PhysIf"]["attributes"]["dn"]) == 41: beautiful += ' '
    print(f'{data["imdata"][i]["l1PhysIf"]["attributes"]["dn"]} {beautiful}                              {data["imdata"][i]["l1PhysIf"]["attributes"]["speed"]} {data["imdata"][i]["l1PhysIf"]["attributes"]["mtu"]}')

