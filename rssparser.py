#!/usr/bin/python
"""Ultra-liberal RSS parser

Handles RSS 0.9x and RSS 1.0 feeds

RSS 0.9x elements:
- title, link, description, webMaster, managingEditor, language
  copyright, lastBuildDate, pubDate

RSS 1.0 elements:
- dc:rights, dc:language, dc:creator, dc:date, dc:subject,
  content:encoded

Things it handles that choke other RSS parsers:
- bastard combinations of RSS 0.9x and RSS 1.0 (most Movable Type feeds)
- illegal XML characters (most Radio feeds)
- naked and/or invalid HTML in description (The Register)
- content:encoded in item element (Aaron Swartz)
- guid in item element (Scripting News)
- fullitem in item element (Jon Udell)
- non-standard namespaces (BitWorking)

Requires Python 2.2 or later
"""

__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__copyright__ = "Copyright 2002, Mark Pilgrim"
__license__ = "GPL"
__history__ = """
1.0 - 9/27/2002 - MAP - fixed namespace processing on prefixed RSS 2.0 elements,
  added Simon Fell's test suite
1.1 - 9/29/2002 - MAP - fixed infinite loop on incomplete CDATA sections
"""

try:
    import timeoutsocket # http://www.timo-tasi.org/python/timeoutsocket.py
    timeoutsocket.setDefaultSocketTimeout(10)
except ImportError:
    pass

import sgmllib, re, cgi, string
sgmllib.tagfind = re.compile('[a-zA-Z][-_.:a-zA-Z0-9]*')
import urllib
entityRe = re.compile('&#(\d+);')

def _convertEntity(match):
    #convert d to a real char
    d = match.group(1)
    return chr(int(d))

def decodeEntities(data):
    data = data or ''
    data = entityRe.sub(_convertEntity, data)
    #data = urllib.unquote_plus(data)
    data = data.replace('&lt;', '<')
    data = data.replace('&gt;', '>')
    data = data.replace('&quot;', '"')
    data = data.replace('&apos;', "'")
    data = data.replace('&amp;', '&')
    return data

class RSSParser(sgmllib.SGMLParser):
    namespaces = {"http://backend.userland.com/rss": "",
                  "http://backend.userland.com/rss2": "",
                  "http://purl.org/rss/1.0/": "",
                  "http://purl.org/rss/1.0/modules/textinput/": "ti",
                  "http://purl.org/rss/1.0/modules/company/": "co",
                  "http://purl.org/rss/1.0/modules/syndication/": "sy",
                  "http://purl.org/dc/elements/1.1/": "dc"}

    def reset(self):
        self.channel = {}
        self.items = []
        self.currentitem = {}
        self.elementstack = []
        self.initem = 0
        self.namespacemap = {}
        sgmllib.SGMLParser.reset(self)

    def push(self, element, expectingText):
        self.elementstack.append([element, expectingText, []])

    def pop(self, element):
        if not self.elementstack: return
        if self.elementstack[-1][0] != element: return
        element, expectingText, pieces = self.elementstack.pop()
        if not expectingText: return
        output = "".join(pieces)
        output = decodeEntities(output)
        if self.initem:
            self.items[-1][element] = output
        else:
            self.channel[element] = output

    def _addNamespaces(self, attrs):
        for prefix, value in attrs:
            if not prefix.startswith("xmlns:"): continue
            prefix = prefix[6:]
            if self.namespaces.has_key(value):
                self.namespacemap[prefix] = self.namespaces[value]

    def start_item(self, attrs):
        self.push('item', 0)
        self.items.append({})
        self.initem = 1

    def end_item(self):
        self.pop('item')
        self.initem = 0

    ## SYNDICATION HOOKS
    def start_sy_updateperiod(self, attrs):
        self.push('updatePeriod', 1)
    start_updateperiod = start_sy_updateperiod

    def end_sy_updateperiod(self):
        self.pop('updatePeriod')
    end_updateperiod = end_sy_updateperiod

    def start_sy_updatefrequency(self, attrs):
        self.push('updateFrequency', 1)
    start_updatefrequency = start_sy_updatefrequency

    def end_sy_updatefrequency(self):
        self.pop('updateFrequency')
    end_updatefrequency = end_sy_updatefrequency

    def start_sy_updatebase(self, attrs):
        self.push('updateBase', 1)
    start_updatebase = start_sy_updatebase

    def end_sy_updatebase(self):
        self.pop('updateBase')
    end_updatefrequency = end_sy_updatebase

    ## Dublin Core Hooks
    def start_dc_language(self, attrs):
        self.push('language', 1)
    start_language = start_dc_language

    def end_dc_language(self):
        self.pop('language')
    end_language = end_dc_language

    def start_dc_creator(self, attrs):
        self.push('creator', 1)
    start_managingeditor = start_dc_creator
    start_webmaster = start_dc_creator

    def end_dc_creator(self):
        self.pop('creator')
    end_managingeditor = end_dc_creator
    end_webmaster = end_dc_creator

    def start_dc_rights(self, attrs):
        self.push('rights', 1)
    start_copyright = start_dc_rights

    def end_dc_rights(self):
        self.pop('rights')
    end_copyright = end_dc_rights

    def start_dc_date(self, attrs):
        self.push('date', 1)
    start_lastbuilddate = start_dc_date
    start_pubdate = start_dc_date

    def end_dc_date(self):
        self.pop('date')
    end_lastbuilddate = end_dc_date
    end_pubdate = end_dc_date

    def start_dc_subject(self, attrs):
        self.push('category', 1)

    def end_dc_subject(self):
        self.pop('category')


    ## RSS Elements
    def start_link(self, attrs):
        self.push('link', 1)
    start_guid = start_link

    def end_link(self):
        self.pop('link')
    end_guid = end_link

    def start_title(self, attrs):
        self.push('title', 1)

    def start_description(self, attrs):
        self.push('description', 1)

    def start_content_encoded(self, attrs):
        self.push('content_encoded', 1)
    start_fullitem = start_content_encoded

    def end_content_encoded(self):
        self.pop('content_encoded')
    end_fullitem = end_content_encoded

    def unknown_starttag(self, tag, attrs):
        self._addNamespaces(attrs)
        colonpos = tag.find(':')
        if colonpos <> -1:
            prefix = tag[:colonpos]
            suffix = tag[colonpos+1:]
            prefix = self.namespacemap.get(prefix, prefix)
            if prefix:
                prefix = prefix + '_'
            methodname = 'start_' + prefix + suffix
            try:
                method = getattr(self, methodname)
                return method(attrs)
            except AttributeError:
                return self.push(prefix + suffix, 1)
        return self.push(tag, 0)

    def unknown_endtag(self, tag):
        colonpos = tag.find(':')
        if colonpos <> -1:
            prefix = tag[:colonpos]
            suffix = tag[colonpos+1:]
            prefix = self.namespacemap.get(prefix, prefix)
            if prefix:
                prefix = prefix + '_'
            methodname = 'end_' + prefix + suffix
            try:
                method = getattr(self, methodname)
                return method()
            except AttributeError:
                return self.pop(prefix + suffix)
        return self.pop(tag)

    def handle_charref(self, ref):
        # called for each character reference, e.g. for "&#160;", ref will be "160"
        # Reconstruct the original character reference.
        if not self.elementstack: return
        self.elementstack[-1][2].append("&#%(ref)s;" % locals())

    def handle_entityref(self, ref):
        # called for each entity reference, e.g. for "&copy;", ref will be "copy"
        # Reconstruct the original entity reference.
        if not self.elementstack: return
        self.elementstack[-1][2].append("&%(ref)s;" % locals())

    def handle_data(self, text):
        # called for each block of plain text, i.e. outside of any tag and
        # not containing any character or entity references
        if not self.elementstack: return
        self.elementstack[-1][2].append(text)

    def handle_comment(self, text):
        # called for each comment, e.g. <!-- insert message here -->
        pass

    def handle_pi(self, text):
        # called for each processing instruction, e.g. <?instruction>
        pass

    def handle_decl(self, text):
        # called for the DOCTYPE, if present, e.g.
        # <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        #     "http://www.w3.org/TR/html4/loose.dtd">
        pass

    _new_declname_match = re.compile(r'[a-zA-Z][-_.a-zA-Z0-9:]*\s*').match
    def _scan_name(self, i, declstartpos):
        rawdata = self.rawdata
        n = len(rawdata)
        if i == n:
            return None, -1
        m = self._new_declname_match(rawdata, i)
        if m:
            s = m.group()
            name = s.strip()
            if (i + len(s)) == n:
                return None, -1  # end of buffer
            return string.lower(name), m.end()
        else:
            self.updatepos(declstartpos, i)
            self.error("expected name token")

    def parse_declaration(self, i):
        # override internal declaration handler to handle CDATA blocks
        if self.rawdata[i:i+9] == '<![CDATA[':
            k = self.rawdata.find(']]>', i)
            if k == -1: k = len(self.rawdata)
            self.handle_data(cgi.escape(self.rawdata[i+9:k]))
            return k+3
        return sgmllib.SGMLParser.parse_declaration(self, i)

def openAnything(source):
    """URI, filename, or string --> stream

    This function lets you define parsers that take any input source
    (URL, pathname to local or network file, or actual data as a string)
    and deal with it in a uniform manner.  Returned object is guaranteed
    to have all the basic stdio read methods (read, readline, readlines).
    Just .close() the object when you're done with it.
    """

    if hasattr(source, "read"):
        return source

    # try to open with urllib (if source is http, ftp, or file URL)
    import urllib
    return urllib.urlopen(source)


def parse(uri):
    r = RSSParser()
    f = openAnything(uri)
    r.feed(f.read())
    return r.channel, r.items

def parse_all(uris):
    res = {}
    for uri in uris:
        try:
            res[uri] = parse(uri)
        except:
            pass
    return res



TEST_SUITE = ('http://www.pocketsoap.com/rssTests/rss1.0withModules.xml',
              'http://www.pocketsoap.com/rssTests/rss1.0withModulesNoDefNS.xml',
              'http://www.pocketsoap.com/rssTests/rss1.0withModulesNoDefNSLocalNameClash.xml',
              'http://www.pocketsoap.com/rssTests/rss2.0noNSwithModules.xml',
              'http://www.pocketsoap.com/rssTests/rss2.0noNSwithModulesLocalNameClash.xml',
              'http://www.pocketsoap.com/rssTests/rss2.0NSwithModules.xml',
              'http://www.pocketsoap.com/rssTests/rss2.0NSwithModulesNoDefNS.xml',
              'http://www.pocketsoap.com/rssTests/rss2.0NSwithModulesNoDefNSLocalNameClash.xml')

if __name__ == '__main__':
    import sys
    if sys.argv[1:]:
        urls = sys.argv[1:]
    else:
        urls = TEST_SUITE
    from pprint import pprint
    res = parse_all(urls)
    for k, v in res.items():
        print k
        pprint (v[0])
        pprint (v[1])

