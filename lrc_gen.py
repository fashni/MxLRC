import argparse
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class Musixmatch:
  base_url = "https://apic-desktop.musixmatch.com/ws/1.1/macro.subtitles.get?format=json&namespace=lyrics_richsynched&subtitle_format=mxm&app_id=web-desktop-app-v1.0&"
  headers = {"authority": "apic-desktop.musixmatch.com", "cookie": "x-mxm-token-guid="}

  def __init__(self, token=None):
    self.set_token(token)

  def set_token(self, token):
    self.token = token

  def find_lyrics(self, song):
    durr = song.duration/1000 if song.duration else ""
    params = {
      "q_album": song.album,
      "q_artist": song.artist,
      "q_artists": song.artist,
      "q_track": song.title,
      "track_spotify_id": song.uri,
      "q_duration": durr,
      "f_subtitle_length": math.floor(durr) if durr else "",
      "usertoken": self.token,
    }

    req = urllib.request.Request(self.base_url + urllib.parse.urlencode(params, quote_via=urllib.parse.quote), headers=self.headers)
    try:
      response = urllib.request.urlopen(req).read()
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
      print(repr(e))
      return
    body = json.loads(response.decode())["message"]["body"]["macro_calls"]
    # print(body)

    if body["matcher.track.get"]["message"]["header"]["status_code"]!=200:
      print(f"Requested error: {body['matcher.track.get']['message']['header']}")
      return
    elif isinstance(body["track.lyrics.get"]["message"]["body"], dict):
      if body["track.lyrics.get"]["message"]["body"]["lyrics"]["restricted"]:
        print("Restricted")
        return
    return body

  def get_unsynced(self, song, body):
    if song.is_instrumental:
      lines = [{"text": "♪ Instrumental ♪"}]
    elif song.has_unsynced:
      lyrics = body["track.lyrics.get"]["message"]["body"]["lyrics"]["lyrics_body"] #if isinstance(body["track.lyrics.get"]["message"]["body"], dict) else ""
      if lyrics:
        lines = [{"text": line} for line in list(filter(None, lyrics.split('\n')))]
      else:
        lines = [{"text": ""}]
    else:
      lines = [{"text": ""}]
    song.lyrics = lines
    return song

  def get_synced(self, song, body):
    if song.is_instrumental:
      lines = [{"text": "♪ Instrumental ♪", "minutes": 0, "seconds": 0, "hundredths": 0}]
    elif song.has_synced:
      subtitle = body["track.subtitles.get"]["message"]["body"]["subtitle_list"][0]["subtitle"]
      if subtitle:
        lines = [{"text": line["text"] or "♪", "minutes": line["time"]["minutes"], "seconds": line["time"]["seconds"], "hundredths": line["time"]["hundredths"]} for line in json.loads(subtitle["subtitle_body"])]
      else:
        lines = [{"text": "", "minutes": 0, "seconds": 0, "hundredths": 0}]
    else:
      lines = [{"text": "", "minutes": 0, "seconds": 0, "hundredths": 0}]
    song.subtitles = lines
    return song

  @staticmethod
  def gen_lrc(song, outdir='lyrics'):
    if song.subtitles is None:
      return
    tags = [
      f"[by:fashni]",
      f"[ar:{song.artist}]",
      f"[ti:{song.title}]",
    ]
    if song.album:
      tags.append(f"[al:{song.album}]")
    if song.duration:
      tags.append(f"[length:{int((song.duration/1000)//60):02d}:{int((song.duration/1000)%60):02d}]")

    lrc = [f"[{line['minutes']:02d}:{line['seconds']:02d}.{line['hundredths']:02d}]{line['text']}" for line in song.subtitles]
    lines = tags+lrc

    try:
      os.mkdir(outdir)
    except FileExistsError:
      if not os.path.isdir(outdir):
        outdir += '_dir'
        os.mkdir(outdir)

    filepath = os.path.join(outdir, f"{song}.lrc")
    with open(filepath, "w", encoding="utf-8") as f:
      for line in lines:
        f.write(line + '\n')

    print("Lyrics saved:", filepath)


class Song:
  def __init__(self, artist, title, album="", uri=""):
    self.artist = artist
    self.title = title
    self.album = album
    self.uri = uri
    self.duration = 0
    self.has_synced = False
    self.has_unsynced = False
    self.is_instrumental = False
    self.lyrics = None
    self.subtitles = None
    self.coverart_url = None

  def __str__(self) -> str:
    return self.artist+' - '+self.title

  def update_info(self, body):
    meta = body["matcher.track.get"]["message"]["body"]
    if not meta:
      return
    coverart_sizes = ["100x100", "350x350", "500x500", "800x800"]
    coverart_urls = list(filter(None, [meta["track"][f"album_coverart_{size}"] for size in coverart_sizes]))
    self.coverart_url = coverart_urls[-1] if coverart_urls else None
    self.title = meta["track"]["track_name"]
    self.artist = meta["track"]["artist_name"]
    self.album = meta["track"]["album_name"]
    self.duration = meta["track"]["track_length"]*1000
    self.has_synced = meta["track"]["has_subtitles"]
    self.has_unsynced = meta["track"]["has_lyrics"] #or meta["track"]["has_lyrics_crowd"]
    self.is_instrumental = meta["track"]["instrumental"]


def parse_args():
  parser = argparse.ArgumentParser(description='Fetch synced lyrics (*.lrc file) from Musixmatch')
  parser.add_argument('-s', '--song', dest='song', help='song information in the format [ artist,title ]', nargs='+', required=True)
  parser.add_argument('-o', '--out', dest='outdir', help="output directory, default: lyrics", default="lyrics", action="store", type=str)
  parser.add_argument('-t', dest='wtime', help="wait time (seconds) in between request, default: 1", default=1, action="store", type=float)
  return parser.parse_args()

def get_lrc(mx, song, outdir):
  body = mx.find_lyrics(song)
  if body is None:
    print("Lyrics not found:", song)
    return
  song.update_info(body)
  mx.get_synced(song, body)
  mx.gen_lrc(song, outdir=outdir)

def main(args):
  MX_TOKEN = "2203269256ff7abcb649269df00e14c833dbf4ddfb5b36a1aae8b0"
  mx = Musixmatch(MX_TOKEN)

  if len(args.song)==1 and os.path.isfile(args.song[0]):
    with open(args.song[0], 'r', encoding='utf-8') as f:
      songs = f.readlines()
    songs = [s.replace('\n', '') for s in songs]
  else:
    songs = args.song

  for s in songs:
    try:
      artist, title = s.split(',')
    except ValueError:
      print('Invalid parameter:', s)
      continue

    song = Song(artist or "", title or "")
    get_lrc(mx, song, args.outdir)

    if len(songs)>1:
      time.sleep(args.wtime)


if __name__ == "__main__":
  args = parse_args()
  main(args)
