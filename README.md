# lrc-generator
Fetch synced lyrics from Musixmatch and save it as *.lrc file

# Usage
```
python3 lrc_gen.py [-h] -s SONG [SONG ...] [-o OUTDIR] [-t WTIME]

optional arguments:
  -h, --help            show this help message and exit
  -s SONG [SONG ...], --song SONG [SONG ...]
                        song information in the format [ artist,title ]
  -o OUTDIR, --out OUTDIR
                        output directory, default: lyrics
  -t WTIME              wait time (seconds) in between request, default: 1
  --token TOKEN         musixmatch token
```

Example:
```
# One song
python3 lrc_gen.py -s adele,hello

# Multiple song and custom output directory
python3 lrc_gen.py -s adele,hello radiohead,creep -o some_directory

# With a text file and longer wait time (recommended)
python3 lrc_gen.py -s example_input.txt -t 10
```

# Musixmatch Token
Follow the guide [here](https://spicetify.app/docs/faq#sometimes-popup-lyrics-andor-lyrics-plus-seem-to-not-work) to get a new Musixmatch token.

# Credits
* [Spicetify Lyrics Plus](https://github.com/spicetify/spicetify-cli/tree/master/CustomApps/lyrics-plus)
