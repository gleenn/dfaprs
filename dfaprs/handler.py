import aprslib
import json
import logging
import os
import sys
import time
import re
import urllib2

from collections import Counter
from uuid import UUID,uuid4,uuid3
from pprint import pprint

APRS_NAMESPACE = UUID('a3eed8c0-106d-4917-8eb3-8779302bb8b1')

# http://www.aprs.org/symbols/symbolsX.txt
SYMBOLS = {
    '/>': [('mobile', 'vehicle')], 
    '\>': [('mobile', 'vehicle')],
    '\^': [('mobile', 'aircraft')],
    '/^': [('mobile', 'aircraft')],
    '/g': [('mobile', 'aircraft')],
    '/=': [('mobile', 'train')], 
}

target_urls = []
errstats = Counter() 
symstats = Counter()
typestats = Counter()


def init(urls):
    global target_urls
    target_urls = urls

def tags_for_symbol(symbol,table):
    if not symbol or not table:
        return []
    key =  table.strip() + symbol.strip()
    symstats[key] += 1
    res = SYMBOLS.get(key,[]);
    return res


def create_feature(uuid, parsed_packet):
    callsign = parsed_packet['from']
    feat = {
        "type": "Feature",
        "properties": {
            "uuid": uuid,
            "callsign": callsign,
            "source": 'aprs',
            "slug": callsign.lower(),
        },    
    }
    for (k,v) in tags_for_symbol(parsed_packet.get('symbol'), parsed_packet.get('symbol_table')):
       feat['properties'][k] = v
    return update_feature(feat, parsed_packet)


def update_feature(feat, parsed_packet):
    lat = parsed_packet.get('latitude')
    lng = parsed_packet.get('longitude')

    feat['geometry'] = None if not lat or not lng else {
        "type": "Point", "coordinates": [lng,lat]}

    props = [
        ('posambiguity','locationaccuracy'),
        ('timestamp','lastseen'),
        ('comment','aprscomment'),
    ]
    for (aprsprop,featprop) in props:
        val = parsed_packet.get(aprsprop)
        if val:
            feat['properties'][featprop] = val if featprop != 'lastseen' else int(val)
    
    if not feat['properties'].get('lastseen'):
        feat['properties']['lastseen'] = int(time.time())        
    if feat['properties'].get('source') != 'aprs':
        feat['properties']['locationsource'] = 'aprs'        
    return feat        


def process_packet(raw_packet):
    global target_urls,errstats
    errstats['receive'] += 1
    logging.debug("\n")
    try:
        raw_packet = re.sub(r'[\n\r]', '', raw_packet)
        parsed_packet = aprslib.parse( raw_packet )
        logging.debug(json.dumps(parsed_packet,indent=3,sort_keys=True))
        errstats['parse:ok'] += 1
    except Exception as err:
        logging.error( 'ERR failed to parse, %s: %s', err, raw_packet)
        errstats['parse:err'] += 1
        return

    logging.info('RCV %(tags)s %(callsign)s%(comment)s @ [%(lng)s, %(lat)s]%(ts)s' % dict(
            lat=parsed_packet.get('latitude'),
            lng=parsed_packet.get('longitude'),
            tags= ' '.join([':'.join(tag) for tag in tags_for_symbol(parsed_packet.get('symbol'), parsed_packet.get('symbol_table'))]),
            comment = ' (' + parsed_packet.get('comment') + ')'\
                if 'comment' in parsed_packet else '',
            ts = ' on ' + time.ctime(parsed_packet['timestamp'])\
                if 'timestamp' in parsed_packet else '',
            callsign = parsed_packet.get('from')))
    for base_url in target_urls:
        try:
            callsign = parsed_packet['from']
            uuid = str(uuid3(APRS_NAMESPACE,callsign.encode('ascii')))
            url = "%s/features/%s/" % (base_url,uuid)
            req = urllib2.Request(url)
            feat = json.loads(urllib2.urlopen(req).read())
            update_feature(feat, parsed_packet)
            logging.info('UPD %s:%s', callsign, uuid)
        except Exception as err:
            errstats['get:err'] += 1
            if isinstance(err, urllib2.HTTPError) and err.getcode() == 404:
                feat = create_feature(uuid, parsed_packet)
                logging.info('NEW %s:%s', callsign, uuid)
            else:
                logging.error('ERR failed to get, %s: %s', err, url)
                continue

        logging.debug(json.dumps(feat,indent=3,sort_keys=True))

        try:
            req = urllib2.Request( url, json.dumps(feat), {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req).read()
            logging.info('SND %s', url)
            errstats['post:ok'] += 1
        except Exception as err:
            errstats['post:err'] += 1
            logging.error('ERR failed to post, %s: %s', err, url)
