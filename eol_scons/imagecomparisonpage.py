"Module for the ImageComparisonPage class."


class ImageComparisonPage(object):

    """
    Encapsulate the information and settings needed to generate a HTML page
    for comparing images, such as comparing expected plots against current
    plots.  Each image comparison is a pair of images, one 'before'
    (expected) and one 'after' (latest), each image with its own url
    relative to the page being generated, and with a title for the
    comparison.  These tuples are added to this object with the
    addComparison() method, before generating the page with generatePage().
    """

    _default_header = """<html>
<head>
<title>%(pagetitle)s</title>
<style media="screen" type="text/css">
%(css)s
</style>
</head>
<body>
<table border>
"""

    _default_css = """
table { border-width: 4 }
body { margin: 0 0 0 0 ; padding: 0 0 0 0 }
p { margin: 0 0 0 0 ; padding: 0 0 0 0 }
h1, h2, h3, h4, h5,h6 { margin: 0 0 0 0 ; padding: 0 0 0 0 ; 
			text-align: center }
ul { margin-top: 2px; margin-bottom: 2px }

.titlebox { border: thick groove blue; padding: 5px 5px 5px 5px }
"""

    _default_rowtemplate = """
<tr>
<td colspan='2'><h2>%(title)s</h2></td>
</tr>
<tr>
<td>
<h2>%(before)s</h2><br>
<a href='%(before)s'><img %(width)s %(height)s src='%(srcbefore)s'></a>
</td>
<td>
<h2>%(after)s</h2><br>
<a href='%(after)s'><img %(width)s %(height)s src='%(srcafter)s'></a>
</td>
</tr>
"""

    def __init__(self):
        self.pagetitle = None
        self.images = []
        self.header = self._default_header
        self.rowtemplate = self._default_rowtemplate
        self.css = self._default_css
        # Create the img element with these width and height attributes,
        # or omit the property if it is None.
        self.image_width = 400
        self.image_height = 300

    def setPageTitle(self, pagetitle):
        self.pagetitle = pagetitle

    def addComparison(self, before, after, title=None):
        # If title is None then a default is generated from the image names.
        image = {}
        image['before'] = before
        image['after'] = after
        image['srcbefore'] = before
        image['srcafter'] = after
        if title is None:
            title = "Comparison of %s and %s" % (before, after)
        image['title'] = title
        self.images.append(image)

    def writePage(self, page):
        if not self.pagetitle:
            self.pagetitle = page
        out = open(page, 'wb')
        out.write(self.header % self.__dict__)
        for image in self.images:
            props = {}
            props.update(image)
            if self.image_width is None:
                props['width'] = ""
            else:
                props['width'] = "width=%s" % (self.image_width)
            if self.image_height is None:
                props['height'] = ""
            else:
                props['height'] = "height=%s" % (self.image_height)
            out.write(self.rowtemplate % props)
        out.write("</table>\n")
        out.close()
        return None

    def builder(self, target, source, env):
        pagepath = target[0].get_path()
        return self.writePage(pagepath)

    def build(self, env, pagepath):
        """
        "Instantiate a builder for the given page, with the current
        images as the sources.
        """
        page = env.Command(pagepath, [env.Value(self)] +
                           [image['before'] for image in self.images] +
                           [image['after'] for image in self.images],
                           self.builder)
        return page


