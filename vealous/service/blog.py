#-*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache

from utils.render import render
from utils.paginator import Paginator
from service import searchapi
import dbs

import config

def get_path(ua, name):
    ua = ua.lower()
    if ua.find('mobile') != -1 or ua.find('midp') != -1 or ua.find('mini') != -1:
        logging.info('mobile device visited this site --' + ua)
        path = os.path.join(config.ROOT, 'tpl','mobile' , name)
        return path
    path = os.path.join(config.ROOT, 'tpl', config.THEME, name)
    return path

class Index(webapp.RequestHandler):
    def get(self):
        rdic = {}
        rdic['notes'] = dbs.Note.getten()
        rdic['articles'] = dbs.Article.getten()
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['links'] = dbs.Melody.get_all('link')
        ua = self.request.headers.get('User-Agent', 'bot')
        path = get_path(ua, 'index.html')
        self.response.out.write(render(path,rdic))

class Article(webapp.RequestHandler):
    def get(self, slug):
        ua = self.request.headers.get('User-Agent', 'bot')
        rdic = {}
        data = dbs.Article.get(slug)
        if not data:
            logging.info('404 , visite article ' + str(slug))
            path = get_path(ua, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        mode = self.request.get('mode','mark')
        if 'plaintext' == mode:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            html = data.text
            return self.response.out.write(html)
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['data'] = data
        path = get_path(ua, 'article.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Archive(webapp.RequestHandler):
    def get(self):
        rdic = {}
        rdic['navs'] = dbs.Melody.get_all('nav')
        ua = self.request.headers.get('User-Agent', 'bot')
        p = self.request.get('p',1)
        q = dbs.Article.gql("WHERE draft = :1 ORDER BY created DESC", False)
        rdic['mvdata'] = Paginator(q, 10, p)
        path = get_path(ua, 'archive.html')
        self.response.out.write(render(path,rdic))

class Note(webapp.RequestHandler):
    def get(self, slug):
        ua = self.request.headers.get('User-Agent', 'bot')
        rdic = {}
        data = dbs.Note.get(slug)
        if not data:
            logging.info('404 , visite note ' + str(slug))
            path = get_path(ua, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['data'] = data
        path = get_path(ua, 'note.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Keyword(webapp.RequestHandler):
    def get(self, keyword):
        ua = self.request.headers.get('User-Agent', 'bot')
        rdic = {}
        articles = dbs.Article.keyword_article(keyword)
        if not articles:
            logging.info('404 , visite keyword ' + str(keyword))
            path = get_path(ua, '404.html')
            html = render(path, rdic)
            self.response.set_status(404)
        else:
            rdic['articles'] = articles
            rdic['navs'] = dbs.Melody.get_all('nav')
            rdic['links'] = dbs.Melody.get_all('link')
            rdic['keyword'] = keyword
            path = get_path(ua, 'keyword.html')
            html = render(path, rdic)
        self.response.out.write(html)

class S5(webapp.RequestHandler):
    def get(self, slug):
        data = dbs.Melody.get_s5(slug)
        if not data:
            rdic = {}
            logging.info('404 , visite s5 ' + str(slug))
            ua = self.request.headers.get('User-Agent', 'bot')
            path = get_path(ua, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
        else:
            html = data.text
        self.response.out.write(html)

class Search(webapp.RequestHandler):
    def get(self):
        rdic = {}
        rdic['cx'] = cx = self.request.get('cx','017842580319746762888:yjj0ddawsf8')
        rdic['q'] = q = self.request.get('q','Vealous')
        rdic['start'] = start = self.request.get('start', '0')
        try:
            rdic['gres'] = searchapi.gsearch(cx, q, start)
        except:
            rdic['error'] = 'Oops! An Error occured!'
        rdic['navs'] = dbs.Melody.get_all('nav')
        ua = self.request.headers.get('User-Agent', 'bot')
        path = get_path(ua, 'search.html')
        self.response.out.write(render(path,rdic))

class Atom(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$atom')
        if html is None:
            rdic = {}
            rdic['datas'] = dbs.Article.getten()
            path = os.path.join(config.ROOT, 'tpl', 'atom.xml')
            html = render(path, rdic)
            memcache.set('xml$atom', html, 43200) # 12hour
        self.response.out.write(html)

class Rss(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$rss')
        if html is None:
            rdic = {}
            rdic['datas'] = dbs.Article.getten()
            path = os.path.join(config.ROOT, 'tpl', 'rss.xml')
            html = render(path, rdic)
            memcache.set('xml$rss', html, 43200) # 12hour
        self.response.out.write(html)

class Sitemap (webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$sitemap')
        if html is None:
            rdic = {}
            urlset = []
            def addurl(loc, lastmod=None, changefreq=None, priority=None):
                url = {
                    'location': loc,
                    'lastmod': lastmod,
                    'changefreq': changefreq,
                    'priority': priority,
                }
                urlset.append(url)
            articles = dbs.Article.getten()
            for art in articles:
                addurl(art.the_url, art.modified,'weekly',0.5)
            rdic['urlset'] = urlset
            path = os.path.join(config.ROOT, 'tpl', 'sitemap.xml')
            html = render(path, rdic)
            memcache.set('xml$sitemap', html, 21600) # 6hour
        self.response.out.write(html)

class Redirect(webapp.RequestHandler):
    def get(self, path):
        logging.info('redirect from path ' + str(path))
        self.redirect('/' + path)

class Error404(webapp.RequestHandler):
    def get(self):
        logging.info('404')
        rdic = {}
        ua = self.request.headers.get('User-Agent', 'bot')
        path = get_path(ua, '404.html')
        self.response.set_status(404)
        self.response.out.write(render(path,rdic))


apps = webapp.WSGIApplication(
    [
        ('/', Index),
        ('/search', Search),
        ('/archive', Archive),
        ('/a/(.*)', Article),
        ('/k/(.*)', Keyword),
        ('/t/(.*)', Note),
        ('/s5/(.*)', S5),
        ('/feed', Atom),
        ('/feed.atom', Atom),
        ('/feed.rss', Rss),
        ('/sitemap.xml', Sitemap),

        ('/(.*)/', Redirect),
        ('.*', Error404),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
