# Live Channels EPG & Playlist (Android TV)

Automated 7-day Electronic Programme Guide (EPG) and curated 75-channel IPTV playlist optimized for **Live Channels** (`com.google.android.tv`) and **TVirl** (`by.stari4ek.tvirl`).

## Quick Setup (TVirl)

| Resource | Direct Raw URL |
| :--- | :--- |
| **Playlist (M3U)** | `https://raw.githubusercontent.com/earlcr/live-channels-epg/main/working_channels.m3u` |
| **EPG Guide (XMLTV)** | `https://raw.githubusercontent.com/earlcr/live-channels-epg/main/guide.xml.gz` |

### Channel Structure (75 Essential Channels)
1. **UK (Channels 1–28):** BBC One–Four, BBC Scotland, BBC Alba, S4C, BBC News, BBC Parliament, GB News, TalkTV, CNBC Europe, GREAT! movies/romance, TRUE CRIME, CBBC, CBeebies, MUTV, talkSPORT, BBC Radios 1–5 Live & World Service, Top Gear, Graham Norton, Mr Bean, History Hit.
2. **Kenya & East Africa (Channels 29–48):** Inooro TV, Ramogi TV, Akili Kids, Morning Cloud TV, Capuchin TV, Great Commission TV, YOUNIB Media, Wan Luo TV, Rwanda TV, TV10 Rwanda, TV1 Rwanda, Bukedde TV 1 & 2, TV West, TBC 2, Trace Mziki, SABC News, WildEarth, Hot 96 FM.
3. **International News & Entertainment (Channels 49–75):** Al Jazeera, Bloomberg, CBC News, DW English, Euronews, France 24, TRT World, NHK World-Japan, WION, CNA, ESPN, ESPN2, ESPNU, Tennis Channel, Fubo Sports, Cricket Gold, HBO, HBO Hits, Cinemax, A&E, Court TV, National Geographic, Nat Geo Wild, Animal Planet, Cartoon Network, Nickelodeon, MTV Live.

## Automated Updates
A daily GitHub Actions workflow (`.github/workflows/update_epg.yml`) runs at 03:00 UTC to fetch fresh schedules, compile 7 days of upcoming programming, and update `guide.xml.gz`.
