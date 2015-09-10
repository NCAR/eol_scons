"""
A Download builder which pulls files, usually package archives, from a URL.

The source node is a URLNode, subclassed from the Python.Value node, since
URLs are not files or directories in the local filesystem.  URLNode has a
target_from_source() method which generates a default local file to which
the URL is downloaded.  The default target is the last component of the
URL, in the top directory of the source tree.

Downloads use the urlretrieve() method of the standard urllib module.

The source for the Download builder can be just a package file name, with
no slashes in it, in which case it is concatenated with the URL in the
DOWNLOAD_DIRECTORY construction variable.  Otherwise the source is expected
to be a full URL.

"""

import sys
import urllib
import SCons
import os


class URLNode(SCons.Node.Python.Value):

    def __init__ (self, url):
        SCons.Node.Python.Value.__init__(self, url)
        
    def target_from_source(self, pre, suf, splitext):
        env = SCons.Defaults.DefaultEnvironment()
        return env.File("#"+os.path.basename(str(self).strip("'")))
    

def download_emitter (target, source, env):
    "Add the download URL to the package file if necessary."
    url = str(source[0]).strip("'")
    if not "/" in url:
        url = '$DOWNLOAD_DIRECTORY/%s' % url
    source = [URLNode(env.subst(url))]
    if env.get('eolsconsdebug'):
        print "download_emitter returning ([%s],[%s])" % \
              (",".join(map(str, target)),",".join(map(str, source)))
    return target, source


def download(target, source, env):

    def download_report(blocks, blocksize, totalsize):
        sys.stdout.write("\r%s/%s" %((blocks*blocksize),totalsize))

    url = str(source[0]).strip("'")
    file = target[0].get_abspath()
    print "Downloading ", url
    (filename, headers) = urllib.urlretrieve (url, file, download_report)
    print "\nDownloaded ", filename


download_action = SCons.Action.Action(download, None)
download_builder = SCons.Builder.Builder(action = download_action,
                                         emitter = download_emitter,
                                         single_source = True,
                                         source_factory = URLNode)


def generate(env):
    key = 'DOWNLOAD_DIRECTORY'
    if not env.has_key(key):
        env[key] = 'ftp://ftp.atd.ucar.edu/pub/archive/aeros/packages'
    env['BUILDERS']['Download'] = download_builder
    env.fs.URLNode = URLNode


def exists(env):
    return True

