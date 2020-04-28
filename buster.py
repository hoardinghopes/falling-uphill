"""Ghost Buster. Static site generator for Ghost.

Usage:
  buster.py generate [--domain=<local-address>] [--dir=<path>]
  buster.py deploy [--dir=<path>]
  buster.py (-h | --help)
  buster.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --dir=<path>              Absolute path of directory to store static pages.
  --domain=<local-address>  Address of local ghost installation [default: localhost:2368].
"""

import os
import re
import sys
import fnmatch
import shutil
import SocketServer
import SimpleHTTPServer
from docopt import docopt
from time import gmtime, strftime
from git import Repo
from pyquery import PyQuery
import fileinput

LOCAL_GHOST = 'http://localhost:2368'
REMOTE_DOMAIN = 'https://hoardinghopes.github.io'
REMOTE_PATH = REMOTE_DOMAIN + '/falling-uphill'


def main():
    arguments = docopt(__doc__, version='0.1.3')
    if arguments['--dir'] is not None:
        static_path = arguments['--dir']
    else:
        static_path = os.path.join(os.getcwd(), 'static')

    if arguments['generate']:
        command = ("wget "
                   "--recursive "             # follow links to download entire site
                   #"--convert-links "         # make links relative
                   "--page-requisites "       # grab everything: css / inlined images
                   "--no-parent "             # don't go to parent level
                   "--directory-prefix {1} "  # download contents to static/ folder
                   "--no-host-directories "   # don't create domain named folder
                   "--restrict-file-name=unix "  # don't escape query string
                   "--base=" + REMOTE_DOMAIN + " "
                   "{0}").format(arguments['--domain'], static_path)
        os.system(command)

        # remove query string since Ghost 0.4
        file_regex = re.compile(r'.*?(\?.*)')
        for root, dirs, filenames in os.walk(static_path):
            for filename in filenames:
                if file_regex.match(filename):
                    newname = re.sub(r'\?.*', '', filename)
                    print "Rename", filename, "=>", newname
                    os.rename(os.path.join(root, filename), os.path.join(root, newname))


        abs_url_regex = re.compile(r'^(?:[a-z]+:)?//', flags=re.IGNORECASE)
        # remove superfluous "index.html" from relative hyperlinks found in text
        def fixHrefLinks(text, parser, page_slug):
            d = PyQuery(bytes(bytearray(text, encoding='utf-8')), parser=parser)
            page_slug = find_page_slug(d)
            for element in d('a'):
                e = PyQuery(element)
                href = e.attr('href')
                print "\thref", href
                if href is not None: #no href means it's a named anchor in the text
                    if not abs_url_regex.search(href):
                        new_href = re.sub(r'rss/index\.html$', 'rss/index.rss', href)
                        new_href = re.sub(r'/index\.html$', '/', new_href)

                        if new_href.find('#') > -1:
                            print "\t\tfound an internal link: ", new_href
                            new_href = page_slug + new_href
                        e.attr('href', REMOTE_PATH + new_href)
                        print "\t", href, "=>", e.attr('href')
            if parser == 'html':
                return d.html(method='html').encode('utf8')
            return d.__unicode__().encode('utf8')




        # fix links in all html files
        for root, dirs, filenames in os.walk(static_path):
            for filename in fnmatch.filter(filenames, "*.html"):
                filepath = os.path.join(root, filename)
                parser = 'html'
                if root.endswith("/rss"):  # rename rss index.html to index.rss
                    parser = 'xml'
                    newfilepath = os.path.join(root, os.path.splitext(filename)[0] + ".rss")
                    os.rename(filepath, newfilepath)
                    filepath = newfilepath
                with open(filepath) as f:
                    filetext = f.read().decode('utf8')
                    print "fixing hrefs in ", filepath
                    newtext = fixHrefLinks(filetext, parser, filename)
                with open(filepath, 'w') as f:
                    f.write(newtext)

                with open(filepath) as fi:
                    filetext = fi.read().replace(LOCAL_GHOST, REMOTE_PATH)
                    print "fixing localhosts in ", filepath
                with open(filepath, "w") as fo:
                    fo.write(filetext)

                with open(filepath) as fi:
                    filetext = fi.read().replace('/content',  REMOTE_PATH + '/content')
                    print "fixing images in ", filepath
                with open(filepath, "w") as fo:
                    fo.write(filetext)

                with open(filepath) as fi:
                    filetext = fi.read().replace('/assets', REMOTE_PATH + '/assets')
                    print "fixing assets in ", filepath
                with open(filepath, "w") as fo:
                    fo.write(filetext)

                with open(filepath) as fi:
                    filetext = fi.read().replace(REMOTE_PATH + REMOTE_PATH, REMOTE_PATH)
                    print "fixing doubled-up REMOTE_PATHs in ", filepath
                with open(filepath, "w") as fo:
                    fo.write(filetext)




    elif arguments['deploy']:
        repo = Repo(static_path)
        repo.git.add('.')

        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        repo.index.commit('Blog update at {}'.format(current_time))

        origin = repo.remotes.origin
        repo.git.execute(['git', 'push', '-u', origin.name,
                         repo.active_branch.name])
        print "Good job! Deployed to Github Pages."

    else:
        print __doc__


def find_page_slug(d):
    for element in d('link'):
        e = PyQuery(element)
        r = e.attr('rel')
        if r is not None:
            if r.find('canonical') > -1:
                print "canoncial: ", r

                link = e.attr('href')
                # slug_regex = re.compile(r'(/[a-z-]*/)$')
                m = re.search(r'(/[a-z-]*/)$', link)
                if m:
                    print "slug_regex: " , m.group(0)
                    return m.group(0)
                return ""




if __name__ == '__main__':
    main()
