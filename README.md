# MxLRC
Command line tool to fetch synced lyrics from [Musixmatch](https://www.musixmatch.com/) and save it as *.lrc file.

---

## Downloads
### Standalone binary
Download from [Release page](https://github.com/fashni/MxLRC/releases)
### Python script
Required Python 3.6+
- Clone/download this repo
- Install dependancy with pip
```
pip install -r requirements.txt
```

---

## Usage
```
mxlrc [-h] -s SONG [SONG ...] [-o OUTDIR] [-t WTIME]

optional arguments:
  -h, --help            show this help message and exit
  -s SONG [SONG ...], --song SONG [SONG ...]
                        song information in the format [ artist,title ], a
                        text file containing list of songs, or a folder
                        containing the song files
  -o OUTDIR, --out OUTDIR
                        output directory, default: lyrics
  -t SLEEP, --sleep SLEEP
                        sleep time (seconds) in between request, default: 30
  --token TOKEN         musixmatch token
```

## Example:
### One song
```
mxlrc -s adele,hello
```
### Multiple song and custom output directory
```
mxlrc -s adele,hello "the killers,mr. brightside" -o some_directory
```
### With a text file and custom sleep time
```
mxlrc -s example_input.txt -t 20
```
### With a directory containing music files
```
mxlrc -s "Dream Theater/Images and Words (1992)" -t 20
```
> **_This option overrides the `-o/--outdir` argument which means the lyrics will be saved in the same directory as the given input._**

---

## How to get the Musixmatch Token
Follow steps 1 to 5 from the guide [here](https://spicetify.app/docs/faq#sometimes-popup-lyrics-andor-lyrics-plus-seem-to-not-work) to get a new Musixmatch token.

## To Do
- [x] Directory containing music files as input

## Credits
* [Spicetify Lyrics Plus](https://github.com/spicetify/spicetify-cli/tree/master/CustomApps/lyrics-plus)
