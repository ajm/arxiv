# This file is part of get_arxiv.py
#
# get_arxiv.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# get_arxiv.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with get_arxiv.py.  If not, see <http://www.gnu.org/licenses/>.

from sys import stderr, argv, exit, stdout

from xml.dom.minidom import parse
from xml.sax.saxutils import escape
from collections import namedtuple
from os.path import exists

import time
import urllib
import urllib2
import socket


arxiv_url = 'http://export.arxiv.org/oai2?'

Article = namedtuple('Article', ['id', 'title', 'author', 'abstract', 'venue', 'url', 'categories'])

def _build_url(params) :
    global arxiv_url

    return arxiv_url + urllib.urlencode(params)

def start_url(set_name) :
    params = {
        'set' : set_name,
        'verb' : 'ListRecords',
        'metadataPrefix' : 'arXiv'
      }

    return _build_url(params)

def resume_url(token) :
    params = {
        'verb' : 'ListRecords',
        'resumptionToken' : token
      }

    return _build_url(params)

def get_url(set_name, token) :
    return start_url(set_name) if token is None else resume_url(token)

def grab(element, tag) :
    try :
        text = element.getElementsByTagName(tag)[0].childNodes[0].data
        text = ' '.join(text.strip().split())
        text = escape(text)
        return text.encode('utf-8')

    except IndexError :
        return "NA"

id_counter = 0

def download(set_name, description, fp) :
    resume_token = None

    print >> fp, '<?xml version="1.0" encoding="utf-8"?>'
    print >> fp, "<records>"

    while True :
        try :
            f = urllib2.urlopen(get_url(set_name, resume_token))

        except urllib2.HTTPError, he :
            print >> stderr, str(he)
            
            if he.getcode() == 503 :
                print >> stderr, "going to sleep..."
                time.sleep(20)
                continue

            else :
                print >> stderr, "i don't know what to do..."
                exit(1)

        except urllib2.URLError, ue :
            print >> stderr, str(ue)
            time.sleep(20)
            continue

        except socket.error, se :
            print >> stderr, str(se)
            time.sleep(20)
            continue


        dom = parse(f)


        for record in dom.getElementsByTagName("record") :
            print >> fp, record.toxml("utf-8") 


        # <resumptionToken cursor="0" completeListSize="78129">697539|1001</resumptionToken>
        resume_token = grab(dom, "resumptionToken")
        print >> stderr, resume_token

        if resume_token == 'NA' :
            break

        print >> stderr, "sleeping..."
        time.sleep(20)

    print >> fp, "</records>"

def list_sets() :
    global arxiv_url

    try :
        f = urllib2.urlopen(arxiv_url + urllib.urlencode({ 'verb' : 'ListSets' }))
    
    except urllib2.HTTPError, he :
        print >> stderr, str(he)
        exit(1)

    dom = parse(f)

    sets = {}

    set_list = dom.getElementsByTagName("ListSets")[0]

    for record in set_list.getElementsByTagName("set") :
        set_spec = grab(record, "setSpec")
        set_name = grab(record, "setName")

        sets[set_name] = set_spec

    f.close()

    return sets

def main() :
    #download('cs', 'Computer Science', stdout)
    #return 0

    sets = list_sets()

    for name,spec in sets.items() :
        better_name = name

        for bc in ":()-" :
            better_name = better_name.replace(bc, ' ')

        better_name = '_'.join(better_name.split())

        if not exists(better_name + '.xml') :
            print >> stderr, "Downloading %s (%s) to %s ..." % (name, spec, better_name + '.xml')
        else :
            print >> stderr, "Skipping %s ..." % name
            continue

        with open(better_name + '.xml', 'w') as f :
            download(spec, name, f)

    return 0

if __name__ == '__main__' :
    try :
        exit(main())

    except KeyboardInterrupt :
        print >> stderr, "Killed by User..."
        exit(1)

