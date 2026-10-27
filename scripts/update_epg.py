#!/usr/bin/env python3
"""
Daily EPG Updater for Live Channels (Android TV)
Downloads upstream XMLTV feeds from epgshare01, filters and maps them to the
75 curated channels, generates Kenyan regional schedules, and builds guide.xml.gz.
"""

import os
import re
import gzip
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M3U_PATH = os.path.join(REPO_DIR, "working_channels.m3u")
OUTPUT_GZ = os.path.join(REPO_DIR, "guide.xml.gz")
TEMP_DIR = os.path.join(REPO_DIR, ".cache_epg")

FEEDS = [
    ("uk1.xml.gz", "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"),
    ("ke1.xml.gz", "https://epgshare01.online/epgshare01/epg_ripper_KE1.xml.gz"),
    ("us2.xml.gz", "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz"),
]

DIRECT_MAP = {
    # UK Channels
    'BBCOne.uk': 'BBC.One.Yorks.HD.uk',
    'BBCTwo.uk': 'BBC.Two.HD.uk',
    'BBCThree.uk': 'BBC.Three.HD.uk',
    'BBCFour.uk': 'BBC.Four.HD.uk',
    'BBCScotland.uk': 'BBC.Scotland.HD.uk',
    'BBCAlba.uk': 'BBC.Alba.uk',
    'S4C.uk': 'S4C.HD.uk',
    'BBCNews.uk': 'BBC.News.HD.uk',
    'BBCParliament.uk': 'BBC.Parliament.uk',
    'GBNews.uk': 'GB.News.uk',
    'TalkTV.uk': 'TalkTV.uk',
    'CNBCUK.uk@SD': 'CNBC.Europe.uk',
    'GREATMovies.uk': 'GREAT!.movies.uk',
    'GREATRomance.uk': 'GREAT!.romance.uk',
    'TrueCrimeUK.uk': 'TRUE.CRIME.uk',
    'CBBC.uk': 'CBBC.HD.uk',
    'CBeebies.uk': 'CBeebies.HD.uk',
    'MUTV.uk': 'MUTV.HD.uk',
    'talkSPORT.uk': 'talkSPORT.uk',
    'BBCRadio1.uk': 'BBC.Radio.1.uk',
    'BBCRadio2.uk': 'BBC.Radio.2.uk',
    'BBCRadio4.uk': 'BBC.Radio.4.FM.uk',
    'BBCRadio5Live.uk': 'BBC.Radio.5.Live.uk',
    'BBCWorldService.uk': 'BBC.World.Service.uk',
    # Kenya & East Africa
    'AkiliKids.ke': '[311].Akili.Kids.ke',
    'RwandaTV.rw': '[299].Rwanda.TV.ke',
    'TV10Rwanda.rw': '[396].TV10.ke',
    'TraceMziki.ea': '[323].TRACE.Mziki.ke',
    'SABCNews.za': '[404].SABC.News.ke',
    'WildEarth.za': '[183].WildEarth.ke',
    # International & US
    'AlJazeeraEnglish.qa': 'Al.Jazeera.English.uk',
    'BloombergTV.us': 'Bloomberg.HD.uk',
    'CBCNewsNetwork.ca': 'CBC.News.Network.HD.ca',
    'DWEnglish.de': 'DW.English.uk',
    'EuronewsEnglish.fr': 'Euronews.English.uk',
    'France24English.fr': 'France.24.English.uk',
    'TRTWorld.tr': 'TRT.World.HD.uk',
    'NHKWorldJapan.jp': 'NHK.World.Japan.HD.uk',
    'WION.in': 'WION.HD.uk',
    'ESPN.us': 'ESPN.HD.us',
    'ESPN2.us': 'ESPN2.HD.us',
    'ESPNU.us': 'ESPNU.HD.us',
    'TennisChannel.us': 'Tennis.Channel.HD.us',
    'HBO.us': 'HBO.HD.us',
    'HBOHits.us': 'HBO2.HD.us',
    'CinemaxWest.us': 'Cinemax.HD.us',
    'AandE.us': 'A&E.HD.us',
    'CourtTV.us': 'Court.TV.us',
    'NationalGeographicEast.us': 'National.Geographic.HD.us',
    'NatGeoWildEast.us': 'Nat.Geo.Wild.HD.us',
    'AnimalPlanet.us': 'Animal.Planet.HD.us',
    'CartoonNetwork.us': 'Cartoon.Network.HD.us',
    'MTVLive.us': 'MTV.Live.HD.us',
}

CUSTOM_KENYA_SCHEDULES = {
    'InooroTV.ke': [
        ('000000', '050000', 'Nyimbo cia Kiroko & Mugithi Mix', 'Overnight Kikuyu gospel and Mugithi music mix on Inooro TV Kenya.'),
        ('050000', '060000', 'Ihoya ria Kiroko (Morning Devotion)', 'Early morning prayer and gospel devotion.'),
        ('060000', '100000', 'Inooro Ruci-ini', 'Live morning breakfast show with news, newspaper review, and current affairs in Kenya.'),
        ('100000', '130000', 'Amukira Ngatho', 'Mid-morning inspirational music and viewer requests.'),
        ('130000', '140000', 'Mohoro Gitau-ini (1 PM News)', 'Live lunchtime news bulletin from Nairobi.'),
        ('140000', '160000', 'Inooro Miaraho', 'Afternoon lifestyle, culture, and entertainment magazine.'),
        ('160000', '190000', 'Rurumuka', 'High-energy evening drive music and youth entertainment show.'),
        ('190000', '200000', 'Mohoro (7 PM Prime News)', 'Prime time evening news bulletin from Royal Media Services Nairobi.'),
        ('200000', '210000', 'Mother-in-Law / Local Drama', 'Kenyan family drama and comedy.'),
        ('210000', '223000', 'Mohoro & Kiririmbi', 'Late night comprehensive news and political talk show.'),
        ('223000', '240000', 'Mugithi Night Live', 'Late evening acoustic Kikuyu music and cultural showcase.'),
    ],
    'RamogiTV.ke': [
        ('000000', '050000', 'Thumbe Luo Overnight (Ohangla & Benga)', 'Non-stop Luo Benga, Rhumba, and Ohangla music from Kenya.'),
        ('050000', '060000', 'Lamo Mar Okinyi', 'Morning devotion and gospel music.'),
        ('060000', '100000', 'Piny Ruuru (Ramogi Breakfast)', 'Live morning show covering Kenyan news, politics, and Lake Region updates.'),
        ('100000', '130000', "Ong'eche Mag Ngima", 'Mid-morning health, family, and community discussion.'),
        ('130000', '140000', 'Weche Mago (1 PM News)', 'Live midday news bulletin from Royal Media Services.'),
        ('140000', '160000', "wang'eng'o", 'Afternoon cultural heritage and music programme.'),
        ('160000', '190000', 'Thumbe Luo Drive', 'Evening drive show featuring top Benga and Ohangla hits.'),
        ('190000', '200000', 'Weche Mago (7 PM Prime News)', 'Prime time news bulletin from Nairobi and Kisumu.'),
        ('200000', '210000', 'Duol Mar Ramogi', 'Current affairs and community leadership panel.'),
        ('210000', '223000', 'Weche Mago & Baraza', 'Late evening news roundup and political analysis.'),
        ('223000', '240000', 'Rhumba & Benga Classics', 'Late night classic Kenyan and Congolese Rhumba.'),
    ],
    'Hot96FM.ke': [
        ('000000', '060000', 'Hot 96 Overnight Mix', 'Non-stop R&B, Soul, Reggae, and Kenyan hits live from Nairobi.'),
        ('060000', '100000', 'Jeff & Nick in the Morning', "Kenya's premier English breakfast show on Hot 96 FM."),
        ('100000', '140000', 'Mid-Morning on Hot 96', 'Workday hits, lifestyle stories, and Nairobi updates.'),
        ('140000', '160000', 'The Drop Zone', 'Afternoon reggae, dancehall, and urban throwbacks.'),
        ('160000', '200000', 'Hot 96 Drive', 'Nairobi rush-hour drive show with news, traffic, and big tunes.'),
        ('200000', '240000', 'The Rhythm (Late Night R&B)', 'Smooth R&B and slow jams live from Nairobi.'),
    ]
}

FALLBACK_ROTATIONS = {
    'TopGear.uk': ['Top Gear Special: UK Roadtrip', 'Top Gear: Supercars Across Europe', 'Top Gear: Affordable Classics Challenge', 'Top Gear: Star in a Reasonably Priced Car'],
    'GrahamNorton.uk': ['The Graham Norton Show: Best of the Red Chair', 'The Graham Norton Show: Hollywood Stars Special', 'The Graham Norton Show: Music & Comedy Highlights'],
    'MrBean.uk': ['Mr Bean: Do-It-Yourself Bean', 'Mr Bean: The Trouble with Mr Bean', 'Mr Bean: Back to School Mr Bean', 'Mr Bean: Hair by Mr Bean of London'],
    'HistoryHit.uk': ["Dan Snow's History Hit: Battlefields of Britain", 'Castles of the Realm', 'History Hit: Roman Britain Unearthed', 'History Hit: Secrets of the Blitz'],
    'MorningCloudTV.ke': ['Morning Cloud Sunrise News', 'Nairobi Express: Metro Life', 'Morning Cloud Gospel Hour', 'Cloud Prime Live from Nairobi'],
    'CapuchinTV.ke': ['Holy Mass & Rosary from Nairobi', 'Capuchin Faith & Life', 'Voices of Mercy Africa', 'Evening Reflections'],
    'GreatCommission.ke': ['Great Commission Morning Fellowship', 'Living Word Africa', 'Hope for the Nations', 'African Gospel Praise'],
    'YOUNIBMedia.ke': ['YOUNIB Youth Today', 'Campus Vibes Nairobi', 'Afrobeat Countdown', 'YOUNIB Evening Talk'],
    'WanLuoTV.ea': ['Wan Luo Morning Express', 'Lake Victoria News', 'Benga & Luo Cultural Heritage', 'Wan Luo Prime News'],
    'TBC2.tz': ['TBC 2 Habari Asubuhi', 'Dar es Salaam Leo', 'Muziki wa Bongo & Taarab', 'TBC 2 Habari za Saa'],
    'BukeddeTV1.ug': ['Agataliiko Nfuufu (Morning News)', 'Bukedde Express', "Emikolo n'Embaga", 'Agataliiko Nfuufu (Prime News)'],
    'BukeddeTV2.ug': ['Ugandan Music Nonstop', 'Kadongo Kamu Hits', 'Bukedde Sports Update', 'Late Night Rhumba'],
    'TVWest.ug': ["Ag'obutatsyoka (Western News)", "Eby'obuhingi (Farming Focus)", 'Runyankole Cultural Showcase', "Ag'obutatsyoka (Prime)"],
    'TV1Rwanda.rw': ['Amakuru kuri TV1 (Morning News)', 'Rwanda Yacu Magazine', 'Kigali Live Express', 'Amakuru Mashya (Prime News)'],
    'FuboSportsNetwork.us': ['No Chill with Gilbert Arenas', 'The Cooligans Soccer Show', 'Fubo Live: Game Day Highlights', 'Pani & Ro Fight Night Preview'],
    'CricketGold.us': ['Classic Ashes Encounters', 'World Cup Iconic Matches: 1999-2019', 'Greatest Test Centuries', 'Masterclass: Spin & Fast Bowling'],
    'CNAInternational.sg': ['Asia First: Live Singapore', 'East Asia Tonight', 'CNA Correspondent Special', 'Asia Now: Market & Tech Update'],
    'NickelodeonGlobal.us': ['SpongeBob SquarePants Marathon', 'The Loud House', 'Teenage Mutant Ninja Turtles', 'The Patrick Star Show'],
}

def escape_xml(text):
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def parse_m3u():
    channels = []
    with open(M3U_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                m_tvg = re.search(r'tvg-id="([^"]*)"', line)
                if m_tvg:
                    tvg_id = m_tvg.group(1)
                    comma_idx = line.rfind(',')
                    name = line[comma_idx + 1:].strip() if comma_idx != -1 else tvg_id
                    if '|' in name:
                        name = name.split('|', 1)[1].strip()
                    channels.append({'tvg_id': tvg_id, 'name': name})
    return channels

def download_feeds():
    os.makedirs(TEMP_DIR, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0'}
    for fname, url in FEEDS:
        dest = os.path.join(TEMP_DIR, fname)
        print(f"Downloading {fname}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp, open(dest, 'wb') as out_f:
                shutil.copyfileobj(resp, out_f)
            print(f"Saved {fname} ({os.path.getsize(dest)} bytes)")
        except Exception as e:
            print(f"Warning: Failed downloading {fname}: {e}")

def main():
    print(f"1. Parsing channels from {M3U_PATH}...")
    channels = parse_m3u()
    print(f"Loaded {len(channels)} channels.")

    target_tvg_set = {ch['tvg_id'] for ch in channels}
    up_to_tvg = {}
    for tvg, up in DIRECT_MAP.items():
        if tvg in target_tvg_set:
            up_to_tvg.setdefault(up, []).append(tvg)

    download_feeds()

    now_utc = datetime.now(timezone.utc)
    min_time = (now_utc - timedelta(hours=12)).strftime('%Y%m%d%H%M%S')
    max_time = (now_utc + timedelta(days=7)).strftime('%Y%m%d%H%M%S')

    programmes_by_tvg = {ch['tvg_id']: [] for ch in channels}

    print("2. Parsing upstream XMLTV programmes...")
    prog_tag_re = re.compile(rb'<programme\s+start="([^"]+)"\s+stop="([^"]+)"\s+channel="([^"]+)"(.*?)>(.*?)</programme>', re.DOTALL)
    cat_strip_re = re.compile(rb'<category[^>]*>.*?</category>', re.DOTALL)

    for fname, _ in FEEDS:
        fpath = os.path.join(TEMP_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        print(f"Scanning {fname}...")
        try:
            with gzip.open(fpath, 'rb') as gz:
                content = gz.read()
                for m in prog_tag_re.finditer(content):
                    start = m.group(1).decode('utf-8', errors='ignore')
                    stop = m.group(2).decode('utf-8', errors='ignore')
                    up_channel = m.group(3).decode('utf-8', errors='ignore')
                    extra_attrs = m.group(4).decode('utf-8', errors='ignore')
                    body_bytes = cat_strip_re.sub(b'', m.group(5))
                    body = body_bytes.decode('utf-8', errors='ignore').strip()

                    if up_channel in up_to_tvg:
                        clean_start = re.sub(r'[^0-9]', '', start).ljust(14, '0')[:14]
                        if min_time <= clean_start <= max_time:
                            for target_tvg in up_to_tvg[up_channel]:
                                prog_xml = f'  <programme start="{start}" stop="{stop}" channel="{target_tvg}"{extra_attrs}>\n    {body}\n  </programme>'
                                programmes_by_tvg[target_tvg].append(prog_xml)
        except Exception as e:
            print(f"Error parsing {fname}: {e}")

    # 3. Add Custom Kenya schedules
    print("3. Generating Kenya regional schedules for 7 days ahead...")
    base_date = (now_utc - timedelta(days=1)).date()
    for d in range(9):
        day = base_date + timedelta(days=d)
        next_day = day + timedelta(days=1)
        day_str = day.strftime('%Y%m%d')
        next_day_str = next_day.strftime('%Y%m%d')

        for tvg_id, sched in CUSTOM_KENYA_SCHEDULES.items():
            if tvg_id not in target_tvg_set:
                continue
            for s_time, e_time, title, desc in sched:
                start_str = f"{day_str}{s_time} +0300"
                stop_str = f"{next_day_str}000000 +0300" if e_time == '240000' else f"{day_str}{e_time} +0300"
                prog_xml = (
                    f'  <programme start="{start_str}" stop="{stop_str}" channel="{tvg_id}">\n'
                    f'    <title lang="en">{escape_xml(title)}</title>\n'
                    f'    <desc lang="en">{escape_xml(desc)}</desc>\n'
                    f'  </programme>'
                )
                programmes_by_tvg[tvg_id].append(prog_xml)

    # 4. Fallback rotations for channels with 0 programmes
    print("4. Applying fallback rotation blocks for remaining channels...")
    for tvg_id, prog_list in programmes_by_tvg.items():
        if len(prog_list) == 0:
            titles = FALLBACK_ROTATIONS.get(tvg_id, [f"{tvg_id.split('.')[0]} Broadcast"])
            ch_name = next((ch['name'] for ch in channels if ch['tvg_id'] == tvg_id), tvg_id)
            for d in range(8):
                day = base_date + timedelta(days=d)
                for hour_slot in range(0, 24, 3):
                    slot_title = titles[(d * 8 + hour_slot // 3) % len(titles)]
                    s_dt = datetime(day.year, day.month, day.day, hour_slot, 0, 0, tzinfo=timezone.utc)
                    e_dt = s_dt + timedelta(hours=3)
                    start_str = s_dt.strftime('%Y%m%d%H%M%S +0000')
                    stop_str = e_dt.strftime('%Y%m%d%H%M%S +0000')
                    prog_xml = (
                        f'  <programme start="{start_str}" stop="{stop_str}" channel="{tvg_id}">\n'
                        f'    <title lang="en">{escape_xml(slot_title)}</title>\n'
                        f'    <desc lang="en">{escape_xml(ch_name)} continuous high-definition stream.</desc>\n'
                        f'  </programme>'
                    )
                    prog_list.append(prog_xml)

    # 5. Output compressed XMLTV
    print(f"5. Writing output to {OUTPUT_GZ}...")
    total_programmes = sum(len(p) for p in programmes_by_tvg.values())
    with gzip.open(OUTPUT_GZ, 'wt', encoding='utf-8') as out_f:
        out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out_f.write('<tv generator-info-name="LiveChannelsEPG" generator-info-url="https://github.com/earlcr/live-channels-epg">\n')
        for ch in channels:
            tid = ch['tvg_id']
            cname = escape_xml(ch['name'])
            out_f.write(f'  <channel id="{tid}">\n    <display-name>{cname}</display-name>\n  </channel>\n')
        for tvg_id in sorted(programmes_by_tvg.keys()):
            for prog in programmes_by_tvg[tvg_id]:
                out_f.write(prog + '\n')
        out_f.write('</tv>\n')

    gz_size = os.path.getsize(OUTPUT_GZ)
    print(f"SUCCESS: Built {OUTPUT_GZ} with {len(channels)} channels and {total_programmes} programmes ({gz_size} bytes).")

    # Cleanup temp
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

if __name__ == '__main__':
    main()
