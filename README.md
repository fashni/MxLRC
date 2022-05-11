# lrc-generator
Fetch synced lyrics from Musixmatch and save it as *.lrc file

# Usage
```
python3 lrc_gen.py [-h] [-o DIR] TITLE ARTIST

positional arguments:
  TITLE                 song title
  ARTIST                artist name

optional arguments:
  -h, --help            show this help message and exit
  -o DIR, --output DIR  output directory
```

eg. `python3 lrc_gen.py "The Cure" "Just Like Heaven"`


# Musixmatch Token
Follow the guide [here](https://spicetify.app/docs/faq#sometimes-popup-lyrics-andor-lyrics-plus-seem-to-not-work) to get the new Musixmatch token, then put the token as `MX_TOKEN` variable in the code.
