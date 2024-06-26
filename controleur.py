import operator, os, pickle, sys
import cherrypy

import logging
from formencode import Invalid
from model import Link, Comment
from form import LinkForm, CommentForm
from lib import template, ajax

from genshi.input import HTML
from genshi.filters import HTMLFormFiller, HTMLSanitizer



class Root(object):

    def __init__(self, data):
        self.data = data

    """ @cherrypy.expose
    def index(self):
        return 'Geddit'
    
    @cherrypy.expose
    def index(self):
        tmpl = loader.load('index.html')
        return tmpl.generate(title='Geddit').render('html', doctype='html') """
    @cherrypy.expose
    @template.output('index.html')
    def index(self):
        links = sorted(self.data.values(), key=operator.attrgetter('time'))
        return template.render(links=links)
    
    @cherrypy.expose
    @template.output('submit.html')
    def submit(self, cancel=False, **data):
        if cherrypy.request.method == 'POST':
            if cancel:
                raise cherrypy.HTTPRedirect('/')
            form = LinkForm()
            try:
                data = form.to_python(data)
                link = Link(**data)
                self.data[link.id] = link
                raise cherrypy.HTTPRedirect('/')
            except Invalid as e:
                errors = e.unpack_errors()
        else:
            errors = {}

        return template.render(errors=errors) | HTMLFormFiller(data=data)
    
    @cherrypy.expose
    @template.output('info.html')
    def info(self, id):
        link = self.data.get(id)
        if not link:
            raise cherrypy.NotFound()
        return template.render(link=link)
    
    @cherrypy.expose
    @template.output('comment.html')
    def comment(self, id, cancel=False, **data):
        link = self.data.get(id)
        if not link:
            raise cherrypy.NotFound()
        if cherrypy.request.method == 'POST':
            if cancel:
                raise cherrypy.HTTPRedirect('/info/%s' % link.id)
            form = CommentForm()
            try:
                data = form.to_python(data)
                markup = HTML(data['content']) | HTMLSanitizer()
                data['content'] = markup.render('xhtml')
                comment = link.add_comment(**data)
                if not ajax.is_xhr():
                    raise cherrypy.HTTPRedirect('/info/%s' % link.id)
                return template.render('_comment.html', comment=comment,
                                       num=len(link.comments))
            except Invalid as e:
                errors = e.unpack_errors()
        else:
            errors = {}

        if ajax.is_xhr():
            stream = template.render('_form.html', link=link, errors=errors)
        else:
            stream = template.render(link=link, comment=None, errors=errors)
        return stream | HTMLFormFiller(data=data)



    """ @cherrypy.expose
    @template.output('comment.html')
    def comment(self, id, cancel=False, **data):
        link = self.data.get(id)
        if not link:
            raise cherrypy.NotFound()
        if cherrypy.request.method == 'POST':
            if cancel:
                raise cherrypy.HTTPRedirect('/info/%s' % link.id)
            form = CommentForm()
            try:
                data = form.to_python(data)
                comment = link.add_comment(**data)
                raise cherrypy.HTTPRedirect('/info/%s' % link.id)
            except Invalid as e:
                errors = e.unpack_errors()
        else:
            errors = {}

        return template.render(link=link, comment=None,
                               errors=errors) | HTMLFormFiller(data=data)
     """

    @cherrypy.expose
    @template.output('index.xml', method='xml')
    def feed(self, id=None):
        if id:
            link = self.data.get(id)
            if not link:
                raise cherrypy.NotFound()
            return template.render('info.xml', link=link)
        else:
            links = sorted(self.data.values(), key=operator.attrgetter('time'))
            return template.render(links=links)


    

def main(filename):
    # load data from the pickle file, or initialize it to an empty list
    if os.path.exists(filename):
        with open(filename, 'rb') as fileobj:
            data = pickle.load(fileobj)
    else:

        data = {}

    def _save_data():
        # save data back to the pickle file
        fileobj = open(filename, 'wb')
        try:
            pickle.dump(data, fileobj)
        finally:
            fileobj.close()
    if hasattr(cherrypy.engine, 'subscribe'): # CherryPy >= 3.1
        cherrypy.engine.subscribe('stop', _save_data)
    else:
        cherrypy.engine.on_stop_engine_list.append(_save_data)





if __name__ == '__main__':
    data = {}  # Ou toute autre initialisation que vous avez besoin
    main(sys.argv[1])

    cherrypy.log.screen = True
    cherrypy.log.error_log.setLevel(logging.DEBUG)

    

    cherrypy.quickstart(Root(data), '/', {
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    })


""" def main(filename):
    data = {} # We'll replace this later

    # Some global configuration; note that this could be moved into a
    # configuration file
    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })

    cherrypy.quickstart(Root(data), '/', {
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    }) """
