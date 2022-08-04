# MxLRC
Command line tool to fetch synced lyrics from [Musixmatch](https://www.musixmatch.com/) and save it as *.lrc file.

---

## Go version
I'm currently learning Go and I cannot think of a project to start with. So I decided to rewrite this script in Go.

[Check it out here](https://github.com/fashni/mxlrc-go)

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
usage: mxlrc.py [-h] -s SONG [SONG ...] [-o OUTDIR] [-t SLEEP] [-d DEPTH] [-u]
                [--bfs] [-q] [--token TOKEN]

Fetch synced lyrics (*.lrc file) from Musixmatch

optional arguments:
  -h, --help              show this help message and exit
  -s SONG [SONG ...], --song SONG [SONG ...]
                          song information in the format [ artist,title ], a
                          text file containing list of songs, or a directory
                          containing the song files
  -o OUTDIR, --out OUTDIR output directory to save the .lrc file(s), default:
                          lyrics
  -t SLEEP, --sleep SLEEP sleep time (seconds) in between request, default: 30
  -d DEPTH, --depth DEPTH (directory mode) maximum recursion depth, default: 100
  -u, --update            (directory mode) rewrite existing .lrc files inside the
                          output directory
  --bfs                   (directory mode) use breadth first search for scanning
                          directory
  -q, --quiet             suppress logging output
  --token TOKEN           musixmatch token
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
### Directory Mode (recursive)
```
mxlrc -s "Dream Theater"
```
> **_This option overrides the `-o/--outdir` argument which means the lyrics will be saved in the same directory as the given input._**

> **_The `-d/--depth` argument limit the depth of subdirectory to scan. Use `-d 0` or `--depth 0` to only scan the specified directory._**

---

## How to get the Musixmatch Token
Follow steps 1 to 5 from the guide [here](https://spicetify.app/docs/faq#sometimes-popup-lyrics-andor-lyrics-plus-seem-to-not-work) to get a new Musixmatch token.

## Credits
* [Spicetify Lyrics Plus](https://github.com/spicetify/spicetify-cli/tree/master/CustomApps/lyrics-plus)
