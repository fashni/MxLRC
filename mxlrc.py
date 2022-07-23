import argparse
import json
import logging
import math
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from tinytag import TinyTag


class Musixmatch:
  base_url = "https://apic-desktop.musixmatch.com/ws/1.1/macro.subtitles.get?format=json&namespace=lyrics_richsynched&subtitle_format=mxm&app_id=web-desktop-app-v1.0&"
  headers = {"authority": "apic-desktop.musixmatch.com", "cookie": "x-mxm-token-guid="}

  def __init__(self, token=None):
    self.set_token(token)

  def set_token(self, token):
    self.token = token

  def find_lyrics(self, song):
    durr = song.duration / 1000 if song.duration else ""
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
    except (urllib.error.HTTPError, urllib.error.URLError, ConnectionResetError) as e:
      logging.error(repr(e))
      return

    r = json.loads(response.decode())
    if r['message']['header']['status_code'] != 200 and r['message']['header'].get('hint') == 'renew':
      logging.error("Invalid token")
      return
    body = r["message"]["body"]["macro_calls"]

    if body["matcher.track.get"]["message"]["header"]["status_code"] != 200:
      if body["matcher.track.get"]["message"]["header"]["status_code"] == 404:
        logging.info('Song not found.')
      elif body["matcher.track.get"]["message"]["header"]["status_code"] == 401:
        logging.warning('Timed out. Change the token or wait a few minutes before trying again.')
      else:
        logging.error(f'Requested error: {body["matcher.track.get"]["message"]["header"]}')
      return
    elif isinstance(body["track.lyrics.get"]["message"].get("body"), dict):
      if body["track.lyrics.get"]["message"]["body"]["lyrics"]["restricted"]:
        logging.info("Restricted lyrics.")
        return
    return body

  @staticmethod
  def get_unsynced(song, body):
    if song.is_instrumental:
      lines = [{"text": "♪ Instrumental ♪", "minutes": 0, "seconds": 0, "hundredths": 0}]
    elif song.has_unsynced:
      lyrics_body = body["track.lyrics.get"]["message"].get("body")
      if lyrics_body is None:
        return False
      lyrics = lyrics_body["lyrics"]["lyrics_body"]
      if lyrics:
        lines = [{"text": line, "minutes": 0, "seconds": 0, "hundredths": 0} for line in list(filter(None, lyrics.split('\n')))]
      else:
        lines = [{"text": "", "minutes": 0, "seconds": 0, "hundredths": 0}]
    else:
      lines = None
    song.lyrics = lines
    return True

  @staticmethod
  def get_synced(song, body):
    if song.is_instrumental:
      lines = [{"text": "♪ Instrumental ♪", "minutes": 0, "seconds": 0, "hundredths": 0}]
    elif song.has_synced:
      subtitle_body = body["track.subtitles.get"]["message"].get("body")
      if subtitle_body is None:
        return False
      subtitle = subtitle_body["subtitle_list"][0]["subtitle"]
      if subtitle:
        lines = [{"text": line["text"] or "♪", "minutes": line["time"]["minutes"], "seconds": line["time"]["seconds"], "hundredths": line["time"]["hundredths"]} for line in json.loads(subtitle["subtitle_body"])]
      else:
        lines = [{"text": "", "minutes": 0, "seconds": 0, "hundredths": 0}]
    else:
      lines = None
    song.subtitles = lines
    return True

  @staticmethod
  def gen_lrc(song, outdir='', filename=''):
    lyrics = song.subtitles
    if lyrics is None:
      logging.warning("Synced lyrics not found, using unsynced lyrics...")
      lyrics = song.lyrics
      if lyrics is None:
        logging.warning("Unsynced lyrics not found")
        return False
    logging.info("Formatting lyrics")
    tags = [
      "[by:fashni]\n",
      f"[ar:{song.artist}]\n",
      f"[ti:{song.title}]\n",
    ]
    if song.album:
      tags.append(f"[al:{song.album}]\n")
    if song.duration:
      tags.append(f"[length:{int((song.duration/1000)//60):02d}:{int((song.duration/1000)%60):02d}]\n")

    lrc = [f"[{line['minutes']:02d}:{line['seconds']:02d}.{line['hundredths']:02d}]{line['text']}\n" for line in lyrics]
    lines = tags + lrc

    fn = filename or slugify(f"{song}")
    filepath = os.path.join(outdir, fn) + ".lrc"
    with open(filepath, "w", encoding="utf-8") as f:
      f.writelines(lines)
    print(f"Lyrics saved: {filepath}")
    return True


class Song(object):
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
    return self.artist + ' - ' + self.title

  @property
  def info(self):
    return self.__dict__

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
    self.duration = meta["track"]["track_length"] * 1000
    self.has_synced = meta["track"]["has_subtitles"]
    self.has_unsynced = meta["track"]["has_lyrics"]  # or meta["track"]["has_lyrics_crowd"]
    self.is_instrumental = meta["track"]["instrumental"]


def parse_args():
  parser = argparse.ArgumentParser(description='Fetch synced lyrics (*.lrc file) from Musixmatch')
  parser.add_argument('-s', '--song', dest='song', help='song information in the format [ artist,title ], a text file containing list of songs, or a directory containing the song files', nargs='+', required=True)
  parser.add_argument('-o', '--out', dest='outdir', help="output directory to save the .lrc file(s), default: lyrics", default="lyrics", action="store", type=str)
  parser.add_argument('-t', '--sleep', dest='sleep', help="sleep time (seconds) in between request, default: 30", default=30, action="store", type=int)
  parser.add_argument('-d', '--depth', dest='depth', help="(directory mode) maximum recursion depth, default: 100", default=100, type=int)
  parser.add_argument('-u', '--update', dest='update', help="(directory mode) rewrite existing .lrc files inside the output directory", action="store_true")
  parser.add_argument('--bfs', dest='bfs', help='(directory mode) use breadth first search for scanning directory', action="store_true")
  parser.add_argument('-q', '--quiet', dest='quiet', help="suppress logging output", action="store_true")
  parser.add_argument('--token', dest='token', help="musixmatch token", type=str)
  parser.add_argument('--debug', dest='debug', help=argparse.SUPPRESS, action="store_true")
  return parser.parse_args()


def init_args(args):
  args.songs, args.mode = parse_input(args)
  if args.songs['count'] == 0:
    logging.warning("No valid input provided, exiting...")
    return

  if args.mode == 'dir':
    args.outdir = ''
  else:
    try:
      os.mkdir(args.outdir)
    except FileExistsError:
      if not os.path.isdir(args.outdir):
        args.outdir += "_dir"
        os.mkdir(args.outdir)
  return args


def parse_input(args, update=False, depth_limit=100, bfs=False):
  def get_song_dir(directory, songs=None, update=False, depth_limit=100, depth=0, bfs=False):
    logging.info(f"Scanning directory: {directory}")
    logging.debug(f"Max depth: {depth_limit} - Current depth: {depth}")
    files = sorted([f for f in os.scandir(directory)], key=lambda x: x.is_dir() if bfs else x.is_file())
    if songs is None:
      songs = {'paths': [], 'filenames': [], 'artists': [], 'titles': [], 'count': 0}

    for f in files:
      if os.path.splitext(f.path)[-1].lower() == '.lrc':
        continue
      if f.is_dir():
        if depth < depth_limit:
          songs = get_song_dir(f.path, songs, update, depth_limit, depth + 1, bfs)
        continue
      if not TinyTag.is_supported(f.path):
        logging.debug(f'Skipping {f.name}. File not supported.')
        continue

      song_file = TinyTag.get(f.path)
      if not (song_file.artist and song_file.title):
        logging.warning(f'Skipping {f.name}. Cannot parse song info')
        continue
      if os.path.exists(os.path.splitext(f.path)[0] + '.lrc') and not update:
        logging.info(f"Skipping {f.name}. Lyrics file exists")
        continue

      logging.info(f"Adding {f.name}")
      songs['paths'].append(directory)
      songs['filenames'].append(os.path.splitext(f.name)[0])
      songs['artists'].append(song_file.artist)
      songs['titles'].append(song_file.title)
      songs['count'] += 1
    return songs

  def get_song_txt(txt, save_path=""):
    with open(txt, 'r', encoding='utf-8') as f:
      song_list = [s.replace('\n', '') for s in f.readlines()]
    return get_song_multi(song_list, save_path)

  def get_song_multi(song_list, save_path=""):
    songs = {'paths': [], 'filenames': [], 'artists': [], 'titles': [], 'count': 0}
    for song in song_list:
      artist, title = validate_input(song)
      if artist is None or title is None:
        continue
      songs['paths'].append(save_path)
      songs['filenames'].append('')
      songs['artists'].append(artist)
      songs['titles'].append(title)
      songs['count'] += 1
    return songs

  def validate_input(inp):
    try:
      artist, title = inp.split(',')
    except ValueError:
      logging.error(f"Invalid input: {inp}")
      return None, None
    return artist, title

  if len(args.song) == 1:
    if os.path.isdir(args.song[0]):
      logging.debug('Mode: Directory')
      return get_song_dir(args.song[0], update=args.update, depth_limit=args.depth, bfs=args.bfs), "dir"
    if os.path.isfile(args.song[0]):
      logging.debug('Mode: Text')
      return get_song_txt(args.song[0], args.outdir), "text"
  logging.debug('Mode: CLI')
  return get_song_multi(args.song, args.outdir), "cli"


def get_lrc(mx, song, outdir, fn=''):
  print('')
  logging.info(f"Searching song: {song}")
  body = mx.find_lyrics(song)
  if body is None:
    return False
  song.update_info(body)
  logging.info(f"Song found: {song}")
  logging.info(f"Searching lyrics: {song}")
  mx.get_synced(song, body)
  mx.get_unsynced(song, body)
  status = mx.gen_lrc(song, outdir=outdir, filename=fn)
  return status


def main(args):
  run_time = time.strftime("%Y%m%d_%H%M%S")
  MX_TOKEN = args.token if args.token else "2203269256ff7abcb649269df00e14c833dbf4ddfb5b36a1aae8b0"
  mx = Musixmatch(MX_TOKEN)

  songs = [Song(ar or "", ti or "") for ar, ti in zip(args.songs['artists'], args.songs['titles'])]
  failed = []
  for idx, (song, fn, outdir) in enumerate(zip(songs, args.songs['filenames'], args.songs['paths'])):
    c = idx
    try:
      success = get_lrc(mx, song, outdir, fn)
      if not success:
        failed.append(song)

      if idx + 1 < args.songs['count']:
        c += 1
        for sec in range(args.sleep, -1, -1):
          print(f'    Please wait... {sec}s    ', end='\r')
          time.sleep(1)
        print('')
    except KeyboardInterrupt as e:
      logging.warning(repr(e))
      failed += songs[c:]
      failed = list(dict.fromkeys(failed))
      break

  print('')
  logging.info(f"Succesfully fetch {args.songs['count']-len(failed)} out of {args.songs['count']} lyrics.")
  if failed:
    logging.warning(f"Failed to fetch {len(failed)} lyrics.")
    if args.mode == 'dir':
      logging.warning("You can try again with the same command.")
      return
    logging.warning(f"Saving list of failed items in {run_time}_failed.txt. You can try again using this file as the input")
    with open(f"{run_time}_failed.txt", "w", encoding="utf-8") as f:
      f.writelines([f"{s.artist},{s.title}\n" for s in failed])


def rename_logging_level_names():
  for level in list(logging._levelToName):
    if level == logging.NOTSET:
      name = "[-]"
    elif level == logging.DEBUG:
      name = "[/]"
    elif level == logging.INFO:
      name = "[+]"
    elif level == logging.WARNING:
      name = "[o]"
    elif level == logging.ERROR:
      name = "[X]"
    else:
      name = logging.getLevelName(level).lower()
    logging.addLevelName(level, name)


# https://github.com/django/django/blob/main/django/utils/text.py
def slugify(value):
  value = str(value)
  value = unicodedata.normalize("NFKC", value)
  value = re.sub(r"[^\w\s()'-]", "", value)
  return re.sub(r"[-]+", "-", value).strip("-_")


if __name__ == "__main__":
  rename_logging_level_names()
  args = parse_args()
  logging_level = logging.WARNING if args.quiet else logging.INFO
  logging.basicConfig(format='%(levelname)s %(message)s', level=logging.DEBUG if args.debug else logging_level)
  args = init_args(args)
  if args is not None:
    print(f"\n{args.songs['count']} lyrics to fetch")
    main(args)
