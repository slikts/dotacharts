#!/usr/bin/env python

import json
import sys
import math
import io
import datetime

from glob import glob

from smoke.io.wrap import demo as io_wrp_dm
from smoke.replay import demo as rply_dm

from heroes import heroes

def parse(filename):
    with io.open(filename, 'rb') as infile:
        demo_io = io_wrp_dm.Wrap(infile)
        demo_io.bootstrap() 
        demo = rply_dm.Demo(demo_io)
        demo.bootstrap()

        received_tables = demo.match.recv_tables
        class_info = demo.match.class_info

        game_meta_tables = received_tables.by_dt['DT_DOTAGamerulesProxy']
        game_status_index = game_meta_tables.by_name['dota_gamerules_data.m_nGameState']

        match_id = None

        match_heroes = []

        time_offset = None
        last_minutes = -1
        gold = None

        top_row = ["Minute"]
        results = {
            'gpm': [],
            'xpm': [],
            'deaths': [],
            'lh': [],
        }

        resolution = float(30)
        resolution_scale = resolution / 60

        print 'Resolution:', int(resolution), 'seconds'

        for match in demo.play():
            game_meta = match.entities.by_cls[class_info['DT_DOTAGamerulesProxy']][0].state
            current_game_status = game_meta.get(game_status_index)

            if match_id is None:
                match_id = game_meta.get(game_meta_tables.by_name['dota_gamerules_data.m_unMatchID'])
                print 'Match ID:', match_id

            if current_game_status < 5:
                continue

            time = game_meta.get(game_meta_tables.by_name['dota_gamerules_data.m_fGameTime'])

            if time_offset is None:
                time_offset = time


            time -= time_offset

            time_formatted = round((time / 60) * 10) / 10

            time_round = int(math.floor(time / resolution))
        
            if time_round > last_minutes:
                last_minutes = time_round
            elif current_game_status < 6:
                continue
            else:
                winner = game_meta.get(game_meta_tables.by_name['dota_gamerules_data.m_nGameWinner'])

            world_data = match.entities.by_cls[class_info['DT_DOTA_PlayerResource']]

            rt = received_tables.by_dt['DT_DOTA_PlayerResource']

            npc_info_table = received_tables.by_dt['DT_DOTA_BaseNPC']

            current_data = world_data[0].state

            gpm_row = [time_formatted]
            xpm_row = [time_formatted]
            lh_row = [time_formatted]
            deaths_row = [time_formatted]

            for i in range(10):

                hero_ehandle_index = rt.by_name['m_hSelectedHero.{:04d}'.format(i)]
                hero_id_index = rt.by_name['m_nSelectedHeroID.{:04d}'.format(i)]

                hero_id = current_data.get(hero_id_index)
                hero_ehandle = current_data.get(hero_ehandle_index)
                localized_hero_name = heroes[hero_id]['localized_name']

                lh = current_data.get(rt.by_name['m_iLastHitCount.{:04d}'.format(i)])
                deaths = current_data.get(rt.by_name['m_iDeaths.{:04d}'.format(i)])

                gold = current_data.get(rt.by_name['EndScoreAndSpectatorStats.m_iTotalEarnedGold.{:04d}'.format(i)])
                xp = current_data.get(rt.by_name['EndScoreAndSpectatorStats.m_iTotalEarnedXP.{:04d}'.format(i)])

                if time_round == 0:
                    gpm = gold
                    xpm = xp

                    match_heroes.append(hero_id)
                    top_row.append(localized_hero_name)
                else:
                    gpm = round(gold / time_formatted)
                    xpm = round(xp / time_formatted)

                gpm_row.append(gpm)
                xpm_row.append(xpm)
                lh_row.append(lh)
                deaths_row.append(deaths)

            if time_round == 1:
                print 'Heroes:', ', '.join(top_row[1:])

            results['xpm'].append(xpm_row)
            results['gpm'].append(gpm_row)
            results['lh'].append(lh_row)
            results['deaths'].append(deaths_row)

            if current_game_status == 6:
                break

        duration = game_meta.get(game_meta_tables.by_name['dota_gamerules_data.m_flGameEndTime']) - time_offset

        print 'Duration:', str(datetime.timedelta(seconds=duration)).split('.')[0]

    return {
        'id': match_id,
        'heroes': match_heroes,
        'top_row': top_row,
        'duration': duration,
        'resolution': resolution,
        'winner': winner,
        'charts': [
            {
                'name': 'Gold / Minute',
                'data': results['gpm'],
            },
            {
                'name': 'Experience / Minute',
                'data': results['xpm'],
            },
            {
                'name': 'Last Hits',
                'data': results['lh'],
            },
            #{
            #    'name': 'Deaths',
            #    'data': results['deaths'],
            #},
        ]
    }

def table(data):
    return '<table>' +\
    '\n'.join(map(lambda x: '<tr><td>' + '</td><td>'.join(x) + '</td></tr>', data)) +\
    '</table>'

def save(data):
    data_json = json.dumps(data)
    data_json_format = json.dumps(data, indent=2)
    json_name = '{}.json'.format(data['id'])
    open(json_name, 'wb').write(data_json_format)
    template = open('templates/match.html', 'r').read()
    print json_name, 'written'

    if data['winner'] == 3:
        winner = 'Dire'
    else:
        winner = 'Radiant'

    title = '{} &ndash; {} Victory'.format(data['id'], winner)

    meta = [
        ['Date', 123],
        ['ID', data['id']],
        ['Winner', winner],
    ]

    html_name = '{}.html'.format(data['id'])
    open(html_name, 'w').write(template.format(title=title,
        data=data_json,
        #meta=table(meta),
        meta='',
        css=open('main.css', 'r').read(),
        js=open('main.js', 'r').read()))
    print html_name, 'written'

    index()

def index():
    html = open('templates/index.html', 'r').read().format('\n'.join(map(lambda x: '<li><a href="{}">{}</a></li>'.format(x, x.split('/')[-1].split('.')[-2]), glob('[0-9]*.html'))))

    open('index.html', 'w').write(html)

    print 'index.html written'

if __name__ == '__main__':
    save(parse(sys.argv[1]))