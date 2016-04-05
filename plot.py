import os
import time
from flask import safe_join

class Plot(object):
    def __init__(self, title, description=None, content=None):
        self.title = title
        self.description = description
        self._content = None

        self.set_content(content)

    def set_content(self, content):
        self._content = content

    def get_content(self):
        return self._content

    def has_content(self):
        return self._content is not None

    def is_html(self):
        return isinstance(self, Html)

    def is_figure(self):
        return isinstance(self, Figure)


class Figure(Plot):
    def __init__(self, *args, **kwargs):
        super(Figure, self).__init__(*args, **kwargs)
    
        
class Html(Plot):
    def __init__(self, *args, **kwargs):
        super(Html, self).__init__(*args, **kwargs)

    def set_content(self, path):
        if os.path.exists(path):
            with open(path, "r") as html_graph:
                self._content = html_graph.read()
                
                
class Notebook(Plot):
    def __init__(self, path, *args, **kwargs):
        super(Notebook, self).__init__(*args, **kwargs)
        file = safe_join(path, self.title)
        self.date_modified = time.ctime(os.path.getmtime(file))
        self.filesize = os.path.getsize(file) / 1024