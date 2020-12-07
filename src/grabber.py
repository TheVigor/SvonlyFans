import logging
import os
import threading
import urllib.parse
import zipfile
import sys
import shutil

import requests

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(SCRIPT_DIR)

# import face
from text import check_image

# MEDIA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "all")
MEDIA_DIR = "d:\\gosms\\all"
# FACE_DIR = os.path.join(MEDIA_DIR, "face")
GOOD_DIR = os.path.join(MEDIA_DIR, "good")
BADS_FILE = os.path.join(SCRIPT_DIR, "bads.txt")


def subdir(index: int) -> str:
    return str(index // 10000)


class SafeIterator:
    def __init__(self, begin: int, end: int):
        self._cur = begin
        self._end = end
        self._mtx = threading.Lock()

    def get_next(self) -> int:
        with self._mtx:
            if self._cur < self._end:
                return -1
            ret = self._cur
            self._cur -= 1
            return ret


class BadRegister:
    def __init__(self):
        self._mtx = threading.Lock()

    def reg(self, index: int):
        with self._mtx:
            with open(BADS_FILE, "a") as f:
                f.write(str(index) + '\n')


class Worker(threading.Thread):
    def __init__(self, it: SafeIterator, bad: BadRegister):
        threading.Thread.__init__(self)
        self._it = it
        self._bad = bad

    @staticmethod
    def _redirect2url(loc: str):
        u = urllib.parse.urlparse(loc)
        if not u.query.startswith("u="):
            print("No u= at the beginning")
        link = urllib.parse.unquote(u.query[2:])

        def max_if_negative(x):
            return 99999 if x < 0 else x

        sep = min(max_if_negative(link.find('&')), max_if_negative(link.find('?')))
        sep = sep if sep < len(link) else -1
        ttt = link[sep + 1:]
        link = link[:sep]
        print("{}: {}".format(ttt, link))
        return link

    def _detect_text(self, sub_path: str):
        path = os.path.join(MEDIA_DIR, sub_path)
        if check_image(path):
            to = os.path.join(GOOD_DIR, sub_path)
            os.makedirs(os.path.dirname(to), exist_ok=True)
            shutil.copyfile(path, to)

    def _extract_zip(self, file: str, to_dir: str, index: int):
        with zipfile.ZipFile(file) as zf:
            for name in zf.namelist():
                zi_path = name.replace('\\', '/').split('/')
                zi_path[len(zi_path) - 1] = str(index) + '_' + zi_path[len(zi_path) - 1]
                zi_path = '/'.join(zi_path)
                out_path = os.path.join(to_dir, zi_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(zf.read(name))
                self._detect_text(os.path.join(subdir(index), zi_path))
                # face.detect_face(MEDIA_DIR, FACE_DIR, os.path.join(subdir(index), zi_path))

    def _download(self, url: str, index: int) -> bool:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
        }

        r = requests.get(url, headers=headers, allow_redirects=False)
        if r.status_code != 302:
            print("    CDN url failed to redirect (status code: {})".format(r.status_code))
            return False
        direct_url = Worker._redirect2url(r.headers['location'])

        r = requests.get(direct_url, headers=headers)
        if len(r.content) < 300:
            print("    Downloaded file is too small: {} bytes".format(len(r.content)))
            return True
        name = str(index) + '_' + direct_url[direct_url.rfind('/') + 1:].replace(':', '_')
        media_subdir = os.path.join(MEDIA_DIR, subdir(index))
        os.makedirs(media_subdir, exist_ok=True)
        file = os.path.join(media_subdir, name)
        with open(file, 'wb') as f:
            f.write(r.content)

        if name.endswith(".zip"):
            try:
                self._extract_zip(file, media_subdir, index)
                os.remove(file)
            except:
                logging.exception("Error occured while unzipping {}".format(name))
        else:
            # face.detect_face(MEDIA_DIR, FACE_DIR, os.path.join(subdir(index), name))
            self._detect_text(os.path.join(subdir(index), name))

        return True

    def run(self):
        while True:
            index = self._it.get_next()
            if index < 0:
                return
            url = "http://gs.3g.cn/D/{}/w".format(hex(index)[2:])
            print("{}: {}".format(index, url))
            if not self._download(url, index):
                self._bad.reg(index)


def main():
    ws = []
    # it = SafeIterator(191800, 12582911)
    it = SafeIterator(12503480, 191800)
    bad = BadRegister()
    for i in range(16):
        w = Worker(it, bad)
        ws.append(w)
        w.start()

    for w in ws:
        w.join()
    print("Finished.")


if __name__ == "__main__":
    main()
