import logging

import requests
import urllib.parse
import os
import zipfile


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MEDIA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "all")


def max_if_negative(x):
    return 99999 if x < 0 else x


def redirect2url(loc: str):
    u = urllib.parse.urlparse(loc)
    if not u.query.startswith("u="):
        print("No u= at the beginning")
    link = urllib.parse.unquote(u.query[2:])
    sep = min(max_if_negative(link.find('&')), max_if_negative(link.find('?')))
    sep = sep if sep < len(link) else -1
    ttt = link[sep+1:]
    link = link[:sep]
    print("{}: {}".format(ttt, link))
    return link


def download(url, index):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
    }

    r = requests.get(url, headers=headers, allow_redirects=False)
    if r.status_code != 302:
        return False
    direct_url = redirect2url(r.headers['location'])
    r.close()

    r = requests.get(direct_url, headers=headers)
    name = str(index) + '_' + direct_url[direct_url.rfind('/')+1:].replace(':', '_')
    file = os.path.join(MEDIA_DIR, name)
    with open(file, 'wb') as f:
        f.write(r.content)
    r.close()

    if name.endswith(".zip"):
        try:
            with zipfile.ZipFile(file, 'r') as z:
                z.extractall(MEDIA_DIR)
        except:
            logging.exception("Error occured while unzipping {}".format(name))

    return True


def main():
    if not os.path.exists(MEDIA_DIR):
        os.mkdir(MEDIA_DIR)

    bads = []
    for i in range(14280, pow(16, 6)):
        url = "http://gs.3g.cn/D/{}/w".format(hex(i)[2:])
        print("{}: {}".format(i, url))
        if not download(url, i):
            bads.append(i)
    print(bads)


if __name__ == "__main__":
    main()
