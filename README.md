# MxLRC
Command line tool to fetch synced lyrics from [Musixmatch](https://www.musixmatch.com/) and save it as *.lrc file.

## Downloads
Standalone binary https://github.com/fashni/MxLRC/releases

## Usage
```
mxlrc [-h] -s SONG [SONG ...] [-o OUTDIR] [-t WTIME]

optional arguments:
  -h, --help            show this help message and exit
  -s SONG [SONG ...], --song SONG [SONG ...]
                        song information in the format [ artist,title ]
  -o OUTDIR, --out OUTDIR
                        output directory, default: lyrics
  -t WTIME              wait time (seconds) in between request, default: 30
  --token TOKEN         musixmatch token
```

Example:
```
# One song
mxlrc -s adele,hello

# Multiple song and custom output directory
mxlrc -s adele,hello "the killers,mr. brightside" -o some_directory

# With a text file and custom wait time
mxlrc -s example_input.txt -t 20
```
You can also use the Python script directly. Make sure you have Python 3.6+ installed.

## How to get the Musixmatch Token
Follow steps 1 to 5 from the guide [here](https://spicetify.app/docs/faq#sometimes-popup-lyrics-andor-lyrics-plus-seem-to-not-work) to get a new Musixmatch token.

## Credits
* [Spicetify Lyrics Plus](https://github.com/spicetify/spicetify-cli/tree/master/CustomApps/lyrics-plus)
