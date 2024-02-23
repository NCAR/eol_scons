# SCons tool to add builders for rendering and publishing docbook files.
#
# A couple options have been used over the years.  One is the jw package
# based on Jade and OpenJade and DSSSL (.dsl) style sheets, whose entry
# points are scripts like docbook2pdf (db2pdf) and docbook2html (db2html).
# The other option is xmlto and XSL stylesheets.  On Fedora, there are
# three xmlto packages to install.
#
# xmlto
# xmlto-xhtml
# xmlto-tex
#
# xmlto-xhtml may not be required for pdf and html output, but it's included
# for good measure.

import os
from SCons.Script import Builder


def xmltohtml_emitter(target, source, env):
    outputdir = str(target[0].get_dir())
    # target = [ env.Dir (os.path.join(outputdir,"html")) ]
    target = [env.File(os.path.join(outputdir, "html", "index.html"))]
    # print "emitter returning ", str(target[0]), str(source[0])
    return target, source


# def make_dtd_link(target, source, env):
#   xlink = str(target[0])
#   dirs = glob.glob(str(source[0])+"/xml-dtd-4.2*")
#   dirs.sort()
#   if len(dirs) == 0:
#       raise "Could not find an xml-dtd installation in %s" % str(source[0])
#   print "Linking %s to %s" % (dirs[0], xlink)
#   try:
#       os.unlink (xlink)
#   except:
#       pass
#   os.symlink (dirs[0], xlink)
#   return None


db2pdf = Builder(action='$DOCBOOK2PDF $SOURCE',
                 suffix='.pdf',
                 src_suffix='.xml')
xmltopdf = Builder(action='$XMLTO pdf -o $TARGET.dir $XMLTOFLAGS $SOURCE',
                   suffix='.pdf',
                   src_suffix='.xml')
xmltohtml = Builder(action='$XMLTO html-nochunks -o $TARGET.dir $XMLTOFLAGS $SOURCE',
                    suffix='.html',
                    src_suffix='.xml')
xmltohtmlchunks = Builder(action='$XMLTO html -o $TARGET.dir $XMLTOFLAGS $SOURCE',
                          emitter=xmltohtml_emitter,
                          src_suffix='.xml')


def publish_docbook(env, name, pubdir):
    html1 = env.DocbookHtml([name])
    html = env.DocbookHtmlChunks([name])
    env.Clean(html, [env.Dir("html")])
    pdf = env.DocbookPdf([name])
    htmlinstall = env.Install(os.path.join(pubdir, "html"), html)
    env.AddPostAction(htmlinstall, "cp -r $SOURCE.dir/. $TARGET.dir")
    pdfinstall = env.Install(pubdir, pdf)
    html1install = env.Install(pubdir, html1)
    return [pdfinstall, htmlinstall, html1install]


def generate(env):
    env.SetDefault(XMLTO='xmlto')
    env.SetDefault(XMLTOFLAGS='')
    env.SetDefault(DOCBOOK2PDF='docbook2pdf')
    env['BUILDERS']['DocbookHtml'] = xmltohtml
    env['BUILDERS']['DocbookHtmlChunks'] = xmltohtmlchunks
    env['BUILDERS']['DocbookPdf'] = xmltopdf
    env.AddMethod(publish_docbook, 'PublishDocbook')


def exists(env):
    return env.Detect('xmlto')
