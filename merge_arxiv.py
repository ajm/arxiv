from sys import exit, stderr
from glob import glob
from xml.sax.saxutils import escape
import xml.sax

article_titles = set()

class Article(object) :
    def __init__(self) :
        self.id = None
        self.title = None
        self.author = None
        self.abstract = None
        self.venue = None
        self.url = None
        self.identity = None

    def __str__(self) :
        s = '<article><id>%s</id><title>%s</title><author>%s</author><abstract>%s</abstract><venue>%s</venue><url>%s</url></article>' % (self.id, self.title, self.author, self.abstract, 'arXiv', self.url)
        return s

class ArticleParser(xml.sax.ContentHandler) :
    def __init__(self) :
        self.identity = None
        self.content = None
        self.article = None

    def cleaned(self) :
        s = self.content.replace('\n', ' ').strip()
        s = escape(s)
        return s.encode('utf-8')

    def startElement(self, name, attrs) :
        self.content = ""

        if name == 'article' :
            self.article = Article()

    def characters(self, c) :
        self.content += c

    def endElement(self, name) :
        global article_titles

        if name == 'article' :
            if self.article :
                if self.article.title not in article_titles :
                    s = str(self.article)
                    print s
                    article_titles.add(self.article.title)
                
                self.article = None

        elif name == 'title'    : self.article.title = self.cleaned()
        elif name == 'author'   : self.article.author = self.cleaned()
        elif name == 'abstract' : self.article.abstract = self.cleaned()
        elif name == 'venue'    : self.article.venue = self.cleaned()
        elif name == 'url'      : self.article.url = self.cleaned()
        elif name == 'id'       : self.article.id = self.cleaned()
        else : pass

def main() :
    global article_titles

    print '<?xml version="1.0" encoding="UTF-8" ?>'
    print "<articles>"

    parser = xml.sax.make_parser()
    parser.setContentHandler(ArticleParser())

    for xmlfile in glob('*.xml') :
        print >> stderr, "reading %s ..." % xmlfile

        try :
            parser.parse(open(xmlfile))

        except IOError, ioe :
            print >> stderr, str(ioe)
            return 1

        except xml.sax.SAXParseException, spe :
            print >> stderr, str(spe)
            return 1

    print "</articles>"
    print >> stderr, "written %d articles" % len(article_titles)

    return 0

if __name__ == '__main__' :
    try :
        exit(main())

    except KeyboardInterrupt :
        print >> stderr, "Killed by user..."
        exit(1)
