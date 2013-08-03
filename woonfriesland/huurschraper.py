#!/usr/bin/python

__author__ = 'Joost Molenaar <j.j.molenaar@gmail.com>'

#! www.makelaardijhoekstra.nl
#! www.beter-wonen.nl
#  www.hypodomus.nl
#  www.bosmadewitte.nl
#X www.elkien.nl
#X mijn.woonfriesland.nl
#  www.ldfaber.nl
#  www.woonaccent.nl
#  www.hellema.nl
#  www.makelaardij-friesland.nl
#! www.estatia.nl
#X www.funda.nl

import lxml
import lxml.etree
import time
import urllib2
import traceback
import sys

EMAILS = ['j.j.molenaar@gmail.com', 'geexpook@gmail.com']
INTERVAL = 20 # m

class Schraper(object):
    def __init__(self):
        self.known = {}
    @staticmethod
    def _log(sender, message):
        print '{0} | {1} | {2}'.format(time.asctime(), sender, message)
	sys.stdout.flush()
    def log(self, message):
        Schraper._log(type(self).__name__, message)
    def get_opener(self):
        return urllib2.build_opener()
    def get_url(self, page=1):
        return self.url.format(page)
    def get_data(self, page=1):
        url = self.get_url(page)
        self.log(url)
        result = self.opener.open(url)
        #for k,v in result.headers.dict.items():
        #    self.log('--> {0}: {1}'.format(k, v))
        return result
    def get_html(self, data):
        return lxml.etree.parse(data, lxml.etree.HTMLParser())
    def get_items(self, html):
        assert False, 'virtual'
    def get_page_count(self, html):
        return 1
    def has_more_pages(self, html, page):
        return False
    def get_all_items(self):
        page = 1
        while True:
            data = self.get_data(page)
            html = self.get_html(data)
            items = self.get_items(html)
            for item in items:
                yield item
            if not self.has_more(html, page):
                break
            page += 1    
    def find_new_items(self, all_items):
        for item in all_items:
            key = item['adres1']
            if key not in self.known:
                yield item
                self.known[key] = item
            self.known[key]['gonecount'] = 9
    def find_old_items(self, all_items):
        goners = [ key 
                   for key in self.known 
                   if not any(item['adres1'] == key for item in all_items) ]
        for key in goners:
            self.known[key]['gonecount'] -= 1
            if self.known[key]['gonecount'] == 0:
                yield self.known[key]
                del self.known[key]
    def __call__(self):
        self.opener = self.get_opener()
        all_items = list(self.get_all_items())
        new_items = list(self.find_new_items(all_items))
        old_items = list(self.find_old_items(all_items))
        self.log('{0} total, {1} new, {2} goners'.format(len(all_items), len(new_items), len(old_items)))
        return new_items, old_items

class WoonFriesland(Schraper):
    url_1 = 'http://mijn.woonfriesland.nl/aanbod/huuraanbod/resultaat?filter=region&filtervalue=5'
    url_2 = 'http://mijn.woonfriesland.nl/aanbod/huuraanbod/resultaat?page={0}'
    def get_opener(self):
        return urllib2.build_opener(urllib2.HTTPCookieProcessor())
    def get_url(self, page=1):
        return self.url_1 if page == 1 else self.url_2.format(page)
    def get_items(self, html):
        for dwellingItem in html.xpath('//*[@class="dwellingItem"]'):
            info = dwellingItem.xpath('*[@class="dwellingItemInfo"]/ul/li')
            more = ', '.join(
                ''.join(m.itertext()).strip() 
                for m 
                in dwellingItem.xpath('*[@class="dwellingItemInfoMore"]/ul/li'))
            yield {
                'site'  : 'WoonFriesland',
                'url'   : 'http://mijn.woonfriesland.nl' + info[0].xpath('.//a/@href')[0],
                'adres1': info[0].xpath('.//a/text()')[0].strip(),
                'adres2': ''.join(info[1].itertext()).strip(),
                'soort' : info[2].text.strip(),
                'prijs' : info[-1].text.strip(),
                'info'  : more
            }
    def has_more(self, html, page):
        count = len(html.xpath('//ul[@class="paginationControl"]/li[@class="currentPage"]'))
        return page < count
        
class Funda(Schraper):
    url = 'http://www.funda.nl/huur/leeuwarden/300+/p{0}/'
    def get_items(self, html):
        for item in html.xpath('//table[@id="listing-sr"]//tr'):
            if item.attrib.get('class') in ['listing-sort', 'ad']:
                continue
            specs = item.xpath('td/p[@class="specs"]')[0]
            s_woonopp = specs.xpath('span[@title="Woonoppervlakte"]/text()')
            s_kamers  = specs.xpath('span[@title="Aantal kamers"]/text()')
            s_wachttd = specs.xpath('span[@title="Wachttijd"]/text()')
            makelaar = item.xpath('td/p[@class="rel"]/a')
            if makelaar:
                makelaar = makelaar[0]
                makelaar.attrib['href'] = 'http://www.funda.nl' + makelaar.attrib['href']
                makelaar = lxml.etree.tostring(makelaar)
            yield {
                'site'     : 'Funda',
                'url'      : 'http://www.funda.nl' + item.xpath('td/p/a[@class="item"]/@href')[0],
                'adres1'   : item.xpath('td/p/a[@class="item"]/text()')[0].strip(),
                'adres2'   : specs.xpath('span[position()=1]/text()')[0].strip()
                             + ' ' 
                             + specs.xpath('span[position()=2]/text()')[0].strip(),
                'woonopp.' : s_woonopp[0].strip() if s_woonopp else '?',
                'kamers'   : s_kamers[0].strip() if s_kamers else '?',
                'wachttijd': s_wachttd[0].strip() if s_wachttd else '?',
                'prijs'    : ' '.join(item.xpath('.//span[@class="price-wrapper"]')[0].itertext()),
                'makelaar' : makelaar or '?'
            }
    def has_more(self, html, page):
        count = len(html.xpath('//li[@class="nav-pg-nr"]/a'))-1
        return page < count

class Elkien(Schraper):
    url = 'http://www.elkien.nl/aanbodmodel.aspx?steID=2&catID=493&page={0}'
    def get_items(self, html):
        for item in html.xpath('//div[@class="optieModel"]'):
            self.item = item
            yield {
                'site'      : 'Elkien',
                'url'       : 'http://www.elkien.nl/' + item.xpath('.//div[@class="nav"]//a')[0].attrib['href'],
                'adres1'    : item.xpath('.//div[@class="left"]//img')[0].attrib['alt'].strip(),
                'adres2'    : 'Leeuwarden',
                'info'      : ', '.join(' '.join(t.strip() for t in i.itertext()) 
                                        for i in item.xpath('.//table[@class="optiemodel"]/tr'))
            }
    def has_more(self, html, page):
        paging = html.xpath('//div[@class="paging"]')
        if paging:
            next = paging.xpath('a[@class="last disabled"]')
            return not bool(next)
        return False

def run(cmd, stdin=None):
	import subprocess
	if stdin:
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		p.stdin.write(stdin)
		p.stdin.close()
	else:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)	
	return p.stdout.read()
    
def send_mail(address, text, **headers):
    stdin = '\n'.join('{0}: {1}'.format(k, v) for (k, v) in headers.items())
    stdin += '\n\n'
    stdin += text if isinstance(text, basestring) else '\n'.join(text)
    run('sendmail {0}'.format(address), stdin=stdin.encode('utf8'))

def escape(s):
    return s.replace('&','&amp;') \
            .replace('<','&lt;') \
            .replace('>','&gt;') \
            .replace('"','&quot;')
    
def send_report(new_items, old_items, address):
    Schraper._log('Main', 'sending mail: +{0}/-{1} items to {2}'.format(len(new_items), len(old_items), address))

    new_fmt = u'{site}: <a href="{url}">{adres1}</a> ' \
            + u'(<a href="http://maps.google.com/maps?q={adres1}, {adres2}">plattegrond</a>)<br>\n'
    old_fmt = u'Verdwenen op {site}: <a href="{url}">{adres1}</a><hr>\n'

    body = '<html>'
    for addr in new_items:
        addr = dict((k, escape(unicode(v))) for (k, v) in addr.items())
        body += new_fmt.format(**addr)
        body += '\n'.join(u'<b>{0}:</b> {1}<br>'.format(k, addr[k]) 
                          for k in sorted(addr.keys())
                          if k not in ['url','site','gonecount'])
        body += u'<hr>\n'
    for item in old_items:
        body += old_fmt.format(**item)
    body += '</html>'
    
    send_mail(address, body, 
        **{'To': address,
           'Subject': '[huurschraper] +{0}/-{1} adressen'.format(len(new_items), len(old_items)),
           'Content-Type': 'text/html; charset=UTF8'})
        
def send_exception_report(e):
    Schraper._log('Main', 'Exception: ' + type(e).__name__)
    body = traceback.format_exc()
    print body
    for email in EMAILS:
        send_mail(email, body, 
            **{'To': email,
               'Subject': '[huurschraper] {0}'.format(type(e).__name__),
               'Content-Type': 'text/plain'})

def process(schrapers):
    new_items = []
    old_items = []
    for schraper in schrapers:
        new, old = schraper()
        new_items += new
        old_items += old
    if new_items or old_items:
        for email in EMAILS:
            send_report(new_items, old_items, email)
    #else:
    #   Schraper._log('Main', 'nothing')

if 1:        
    Schraper._log('Main', 'huurschraper up and running')
    schrapers = [WoonFriesland(), Funda(), Elkien()]
    earth_destroyed = False
    while not earth_destroyed:
        try:
            process(schrapers)
        except KeyboardInterrupt:
            print
        except Exception as e:
            send_exception_report(e)

        try:
            time.sleep(INTERVAL * 60)
        except KeyboardInterrupt:
            print
            Schraper._log('Main', 'quick! this is your chance! press ^C again to quit')
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                print
                break
else:
    #w = WoonFriesland()
    #print w()

    #f = Funda()
    #print f()

    e = Elkien()
    print e()
