import os


class Plot(object):
    def __init__(self, title, description, content=None):
        self.title = title
        self.set_content(content)
        self.description = description

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