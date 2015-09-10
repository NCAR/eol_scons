# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
API for transparently downloading and caching remote data files.

The data cache needs to make sure exactly the right data file is found, and
that the local copy matches the remote master copy.  Matching by filename
is not enough, since for example there are multiple RAF netcdf files with
the same name on the server.  Therefore, identify exactly the full path on
the server, and use that to uniquely identify the file in the cache and
sync it when necessary.  So the cache API requires data file identifiers
like 'barolo:/scr/raf_data/HIPPO/prod_data/HIPPO-2rf06.nc'.

We want the file name to stay the same, since it may affect how further
file names are derived, so the cache maintains the whole master path.
There is no harm in that, and it makes checking for the cached file
straightforward, since the local path is just the remote path appended to
the cache directory: $DATACACHE/barolo:/scr/raf_data/HIPPO/prod_data/.

The hostname portion of the master file path just makes it convenient to
use the path with rsync, using ssh for the remote connection.  However,
rather than use the exact host name like barolo, use something that must be
added to the ssh config but that does not collide with hostnames that may
already have configurations, eg, rafdata.  This entry in .ssh/config
defines a ssh host alias called rafdata:

   Host rafdata
   HostName barolo.eol.ucar.edu

By default the data files are cached in #/DataCache.  It might be nice to
share a single DataCache across projects, but using the local source
directory has the advantage that the data files go away when the source
tree is removed.  Other possibilities are to use a common directory like
$HOME/.datafilecache, something more obvious or conventional like
$HOME/Data/cache, or at least allow the cache directory to be overridden
with an environment variable.
"""

import subprocess as sp
import os

class DataFileCache(object):
    """
    Provide an API to lookup and search for test data files on the local
    filesystem without requiring tests to know how they are stored and
    where.  Someday eventually this can include the ability to fetch data
    files remotely and cache them on the local filesystem.
    """

    def __init__(self, cachepath=None):
        self.datacachepath = cachepath
        self.cached_paths = {}
        self.prefix = None
        self.enable_download = True

    def setDataCachePath(self, path):
        self.datacachepath = path

    def setPrefix(self, prefix):
        self.prefix = prefix

    def sync(self):
        """
        Sync all the files known about in the cache map.  Since this is
        typically called as a SCons target, all the data files an
        Environment uses should already have been fetched with getFile()
        and added to the map.  So a sync just requires iterating through
        the map and calling rsync on each file.
        """
        ok = True
        for filepath in self.cached_paths.keys():
            if not self.download(filepath):
                ok = False
        return ok

    def enableDownload(self, enable):
        self.enable_download = enable

    def download(self, filepath):
        """
        Run rsync to download the filepath into the cache.  As an optimization,
        see if the file exists locally at the master path, meaning we're
        running on the data server, and if so the hostname specifier can be
        stripped.
        """
        (host, colon, lpath) = filepath.partition(':')
        if colon:
            if os.path.exists(lpath):
                filepath = lpath
        destpath = os.path.join(self.datacachepath, filepath)
        destdir = os.path.dirname(destpath)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        args = ['rsync', '-v', filepath, destdir]
        print(" ".join(args))
        retcode = sp.call(args, shell=False)
        if retcode == 0 and os.path.isfile(destpath):
            return destpath
        print("*** rsync failed to download: %s" % (filepath))
        if host:
            print("*** Check that host %s is configured in ssh/config." % (host))
        print("*** Check that remote host is accessible. Is VPN enabled?")
        return None

    def getFile(self, filepath):
        if self.prefix:
            filepath = os.path.join(self.prefix, filepath)
        path = self.cached_paths.get(filepath)
        if not path:
            # Look for it in the cache and download it if not there.
            tpath = os.path.join(self.datacachepath, filepath)
            if os.path.exists(tpath):
                path = tpath
            elif self.enable_download:
                path = self.download(filepath)
            else:
                print("===> Download disabled for data file: %s" % (filepath))
            if path:
                print("found %s" % (path))
                self.cached_paths[filepath] = path
        return path


def test_get():
    dfcache = DataFileCache("/tmp")
    dfcache.setPrefix('rafdata:/scr/raf_data')
    if os.path.exists("/tmp/rafdata:"):
        import shutil
        shutil.rmtree("/tmp/rafdata:")
    target = 'HIPPO/HIPPO-5rf06.kml'
    hippopath = dfcache.getFile(target)
    xpath = "/tmp/rafdata:/scr/raf_data/" + target
    assert(hippopath == xpath)
    assert(os.path.exists(xpath))
    assert(dfcache.getFile(target) == xpath)

    dfcache = DataFileCache("/tmp")
    dfcache.setPrefix('rafdata:/scr/raf_data')
    assert(dfcache.getFile(target) == xpath)
    
    
