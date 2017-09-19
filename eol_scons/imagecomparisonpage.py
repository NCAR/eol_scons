# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"Module for the ImageComparisonPage class."

try:
    from StringIO import StringIO
except:
    from io import StringIO

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

    def writePage(self, page, images=None, outs=None):
        if not self.pagetitle:
            self.pagetitle = page
        out = outs
        if outs is None:
            out = open(page, 'wb')
        out.write(self.header % self.__dict__)
        if images is None:
            images = self.images
        for image in images:
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
        if outs is None:
            out.close()
        return None

    def resolvePath(self, page, image):
        # Assume if parameters are not strings then they are SCons Nodes.
        if not isinstance(page, str) and not isinstance(image, str):
            return image.get_path(page.dir)
        return image

    def contents(self, env, page):
        """
        Generate HTML contents with links relative to SCons node page.
        """
        pagepath = page.get_path()
        # Resolve all the image paths relative to the page path.
        resolved = []
        for image in self.images:
            rimage = {}
            rimage.update(image)
            for key in ['before', 'after', 'srcbefore', 'srcafter']:
                rimage[key] = self.resolvePath(page, image[key])
            resolved.append(rimage)
        out = StringIO()
        self.writePage(pagepath, resolved, out)
        return out.getvalue()

    def builder(self, target, source, env):
        page = target[0]
        with open(page.get_path(), 'wb') as out:
            out.write(self.contents(env, page))
        return None

    def beforeImages(self):
        "Return list of paths to all the before images."
        return [image['before'] for image in self.images]

    def afterImages(self):
        "Return list of paths to all the after images."
        return [image['after'] for image in self.images]

    def build(self, env, pagepath, sources=None):
        """
        Instantiate a builder for the given page.  All images are sources
        unless an explicit list is passed in the sources parameter.  The
        file contents are always added as a Value() node dependency, so the
        page will be rewritten if anything in the page would change.
        """
        contents = self.contents(env, env.File(pagepath))
        if sources is None:
            sources = self.beforeImages() + self.afterImages()
        from SCons.Action import Action
        action = Action(self.builder,
                        cmdstr="Generating html comparison page $TARGET")
        page = env.Command(pagepath, [env.Value(contents)] + sources,
                           action)
        return page


