# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Transparently cache data files within a pool of local directories and
synchronize them from a master remote location as needed.

There are two parts to caching data files: the local directory in which the
data files are cached, and the remote directory specifier from which data
files can be synchronized.  There is a seach path of local directories
which is searched first.  If a requested data file is not found in the
cache, then it can be downloaded from the remote specifier.  It will be
downloaded into the first directory in the search path which exists on the
local system, or else the last directory on the search path will be created
and used, if needed.

The data cache needs to make sure exactly the right data file is found, and
that the local copy matches the remote master copy.  Matching by filename
is not enough, since for example there are multiple RAF netcdf files with
the same name on the server.  Therefore, data files are identified by their
path relative to a remote prefix, where the remote prefix typically
includes a host specifier.  It is up to the caller to make sure the
relative paths of all files are unique.  The concatenation of a local cache
directory and the relative data file path identify exactly the full path to
a locally cached data file.  The relative data file path is used to
uniquely identify the file in the cache and sync it when necessary.

Typically, the remote prefix includes a remote host specifier and a directory,
such as 'barolo:/scr/raf_data'.  Clients request data files from the cache
using a relative path like 'HIPPO/prod_data/HIPPO-2rf06.nc'.  The data file is
stored locally in the cache by its relative path,
_datacache_/HIPPO/prod_data/HIPPO-2rf06.nc, and it is synchronized from its
fully qualified remote specifier:
'barolo:/scr/raf_data/HIPPO/prod_data/HIPPO-2rf06.nc'.

The hostname portion of the master file path just makes it convenient to
use the path with rsync, using ssh for the remote connection.  However,
rather than use the exact host name like barolo, use something that must be
added to the ssh config but that does not collide with hostnames that may
already have configurations.  This entry in .ssh/config defines a ssh host
alias called rafdata:

   Host rafdata
   HostName barolo.eol.ucar.edu

When a DataFileCache is instantiated as part of a SCons Environment (see
the testing.py tool), the constructor sets a default cache directory for
the downloaded data files as #/DataCache.  Otherwise there is no default,
so a local path must be inserted into cachepaths before registering data
files.  It might be nice to share a single DataCache across projects, but
using the local source directory has the advantage that the data files go
away when the source tree is removed.  Other possibilities are to use a
common directory like $HOME/.datafilecache, something more obvious or
conventional like $HOME/Data/cache, or at least allow the cache directory
to be overridden with an environment variable.
"""

import subprocess as sp
import os


class DataFileCache(object):
    """
    Lookup and search for data files on the local filesystem without
    requiring clients to know how they are stored and where.
    """

    def __init__(self, cachepath=None):
        self._cachepaths = []
        self._remote_prefix = None
        if cachepath:
            self._cachepaths = [cachepath]
        self._cached_paths = {}
        self._enable_download = True
        # full rsync command last run
        self.rsync_command = None
        # echo rsync command instead of executing it
        self.echo = False

    def getCachePath(self):
        "Return the current cache path list."
        return self._cachepaths

    def setDataCachePath(self, path):
        """
        Replace the current list of cache paths with a single directory.
        """
        self._cachepaths = [path]

    def insertCachePath(self, path):
        """
        Insert a cache directory at the front of the cache path list.

        This will be the first directory searched for existing copies of
        data files, and if it already exists it will also be the default
        location for newly downloaded copies.
        """
        self._cachepaths.insert(0, path)

    def appendCachePath(self, path):
        "Append a cache directory to the list of cache paths."
        self._cachepaths.append(path)

    def setRemotePrefix(self, prefix):
        """
        Set the prefix for data files to create the remote specifier from which
        local files can be synchronized.
        """
        self._remote_prefix = prefix

    # Backwards compatible but deprecated method.
    setPrefix = setRemotePrefix

    def sync(self):
        """
        Sync all the files known about in the cache map.  Since this is
        typically called as a SCons target, all the data files an
        Environment uses should already have been registered with getFile()
        and added to the map.  So a sync just requires iterating through
        the map and calling rsync on each file.
        """
        ok = True
        for filepath in self._cached_paths.keys():
            if not self.download(filepath):
                ok = False
        return ok

    def enableDownload(self, enable):
        self._enable_download = enable

    def downloadEnabled(self):
        return self._enable_download

    def download(self, filepath):
        """
        Run rsync to download the canonical filepath into the cache.

        If downloading is disabled, then just return true if the file
        already exists, false otherwise.

        If the file exists locally at the master path (ie, with any
        hostname specifier stripped), assume that's the source data file
        and that we're running on the data host itself or else the file is
        mounted here.  If so, symbolically link the file into the cache.
        We want to be careful not to do anything that might expose the data
        file to accidental modification, so that's why it is not just used
        in place.  Actually copying the file into the cache would be safer
        still, but for now I'll consider a link to be safe enough.

        Stripping the hostname when the file already exists locally helps
        the data cache work in batch operations like jenkins when it is not
        authorized to rsync through ssh.
        """
        destpath = self.getFile(filepath)
        destdir = os.path.dirname(destpath)
        if not self._enable_download:
            return os.path.exists(destpath)
        # The prefix is still needed, esp if it specifies the remote host.
        if not self._remote_prefix:
            raise Exception("Need a remote prefix to download data file.")
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        filepath = os.path.join(self._remote_prefix, filepath)
        (host, colon, lpath) = filepath.partition(':')
        if colon and os.path.exists(lpath):
            filepath = lpath
            print("Using local datafile as source: %s" % (filepath))
            colon = None
        # If we are using the hostname specifier (colon is not None), then
        # we must rsync, otherwise we link.  It is also possible there is
        # no host specifier but the source file does not exist, in which
        # case we fail saying just that.
        if colon:
            destpath = self._rsync(filepath, destpath)
        elif not os.path.exists(filepath):
            print("*** Datafile source path does not exist: %s ***"
                  % filepath)
            destpath = None
        else:
            destpath = self._link(filepath, destpath)
        if not destpath and colon:
            print("*** Check that host %s is configured in ssh/config."
                  % (host))
            print("*** Is remote host is accessible. Is VPN enabled?")
        return destpath

    def _rsync(self, filepath, destpath):
        args = ['rsync', '-tv', filepath, destpath]
        self.rsync_command = " ".join(args)
        print(self.rsync_command)
        if not self.echo:
            retcode = sp.call(args, shell=False)
            if retcode == 0 and os.path.isfile(destpath):
                return destpath
            print("*** rsync failed to download: %s" % (filepath))
        return None

    def _link(self, filepath, destpath):
        # See if link exists and is already correct.
        if os.path.islink(destpath):
            if os.path.realpath(destpath) == os.path.realpath(filepath):
                print("Link already exists: %s" % (destpath))
                return destpath
            print("Removing and fixing link: %s" % (destpath))
            os.unlink(destpath)
        elif os.path.exists(destpath):
            # Entry is not a link.  Do not remove it automatically in case
            # it's important.
            print("*** File exists where link needs to be created: %s ***" %
                  (destpath))
            return None
        # Create the link.
        print("ln -s %s %s" % (filepath, destpath))
        os.symlink(filepath, destpath)
        return destpath

    def getFile(self, filepath):
        """
        Convert the canonical filepath to the local cache path, without trying
        to download the file if it's missing.
        """
        return self._registerFile(filepath)

    def localDownloadPath(self):
        """
        Traverse the cachepath directories and use the first that exists, or
        else use the last one.
        """
        cpaths = self.expandedCachePaths()
        for cdir in cpaths:
            if os.path.exists(cdir):
                return cdir
            else:
                print("skipped non-existent local cache dir: %s" % (cdir))
        if not cpaths:
            raise Exception("No local cache paths set in DataFileCache.")
        return cpaths[-1]

    def expandedCachePaths(self):
        dirs = []
        for cdir in self._cachepaths:
            dirs.append(os.path.expandvars(os.path.expanduser(cdir)))
        return dirs

    def _registerFile(self, filepath):
        """
        Resolve the given relative filepath to a local path.  If the file is
        found under one of the local directories on the search path, then
        that local path is registered and returned.  If not, then the file
        is registered with the path under the first local directory which
        exists.  If the file is later downloaded from the remote prefix, it
        will be written to the local path registered here.

        Files are registered using the relative filepath, and that maps to
        the full path within a data file cache directory.
        """
        path = self._cached_paths.get(filepath)
        if not path:
            for cdir in self.expandedCachePaths():
                tpath = os.path.join(cdir, filepath)
                if os.path.exists(tpath):
                    path = tpath
                    break
            if not path:
                path = os.path.join(self.localDownloadPath(), filepath)
            if False:
                print("registering file %s with data cache path: %s" %
                      (filepath, path))
            self._cached_paths[filepath] = path
        return path
