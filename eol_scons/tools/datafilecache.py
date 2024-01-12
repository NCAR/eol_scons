"""
A SCons tool which adds a DataFileCache instance to an Environment and
integrates it with SCons builders to download data files and create
dependencies on the cached copies.

These are the methods added to the Environment:

  DataFileCache(): Return an instance of DataFileCache attached to the
  environment instance, creating it first if necessary.

  DownloadDataFile(): Register a cache file by its relative path, and
  return a SCons Node for the local cache path to that file.  The node is
  the target of a builder which runs DataFileCache.download() to
  synchronize the local file.

If a cached data file is a dependency of a scons target being built, and it
does not already exist in the cache, then the file will be downloaded with
rsync from the remote specifier.  Once a file has been downloaded to the
cache, it will not be synchronized with the remote source again.  The cache
can be updated using the 'datasync' alias described below.

This tool adds a scons variable called 'download', with one of three settings:
*force*, *auto*, and *off*.  The default setting is *auto*.

**force**:
  Files will be explicitly synchronized whenever required for a dependency,
  even if they already exist in the cache.

**off**:
  Files will never be synchronized.  This can be helpful if the local cache is
  already current, but the scons dependency cache has not been updated.  For
  example, to prevent downloads in a fresh working tree or after cleaning the
  scons cache files, run

      scons download=off <targets>

  The local cache files will be used as is without attempting to synchronizing
  them.  If a local cache file is needed for a dependency but does not exist,
  and 'download' is disabled, then the build will fail.

**auto**:
  File synchronization follows scons dependency tracking.  If a file already
  exists locally and the scons dependency info is up-to-date, then no
  synchronization is run.  If the dependency info is not up-to-date, then the
  file will be synchronized even if it already exists locally, because scons
  has no record that the target file is current.

Each cached data file is added to the 'datasync' alias.  Run `scons datasync`
to build all the cached data file targets, and set the 'download' option to
choose whether the files should be synchronized.  For example, this will
update all the data files in the cache:

    scons download=force datasync

This command will just check that all the files exist in the cache and fail
if any do not:

    scons download=off datasync
"""

import SCons
from SCons.Variables import EnumVariable

def _sync_file(target, source, env):
    dfcache = env.DataFileCache()
    if dfcache.download(str(source[0])):
        return None
    msg = "datasync failed."
    if not dfcache.downloadEnabled():
        msg = "datasync failed, download disabled."
    raise SCons.Errors.StopError(msg)

def _sync_file_message(target, source, env):
    return "Downloading %s to %s:" % (str(source[0]), str(target[0]))

def _download_data_file(env, filepath):
    # Create a scons builder which downloads the source file into the cache.
    dfcache = env.DataFileCache()
    dfcache.enableDownload(env.get('download', 'auto') in ['auto', 'force'])
    syncfile = env.Action(_sync_file, _sync_file_message)
    target = env.Command(dfcache.getFile(filepath),
                         env.Value(filepath), syncfile)
    if env.get('download', 'auto') == 'force':
        env.AlwaysBuild(target)
    # Do not allow scons to erase the data file before re-synchronizing it,
    # nor remove the file when cleaning.
    env.Precious(target)
    env.NoClean(target)
    env.LogDebug("created command builder to download %s to %s" %
                 (filepath, target[0].abspath))
    # Add the target to the datasync alias, so one alias can be used to
    # update all the cache files and also the scons dependencies cache.
    # However, the syncs do not happen if the file already appears updated,
    # so we have to kludge it a little bit.  If datasync is one of the
    # targets to be built, then the datafile targets themselves need to be
    # forced with AlwaysBuild().  Rather than force it here, rely on the
    # download setting above to force downloads.
    env.AlwaysBuild(env.Alias('datasync', target))
    if False and 'datasync' in SCons.Script.BUILD_TARGETS:
        env.AlwaysBuild(target)
    # Return just the single node rather than the list that a builder would
    # actually return, so it can be substitued easily for a file path.
    return target[0]

def _get_cache_instance(env):
    import eol_scons.datafilecache as datafilecache
    import os
    dfcache = env.get('DATA_FILE_CACHE')
    if not dfcache:
        path = str(env.Dir('#/DataCache'))
        # I don't think it's necessary to create the directory.  DataFileCache
        # will create it if it is needed.
        #
        #if not os.path.isdir(path):
        #    os.makedirs(path)
        dfcache = datafilecache.DataFileCache()
        # Provide fallback cache directory for scons environments.
        dfcache.appendCachePath(path)
        env['DATA_FILE_CACHE'] = dfcache
        # No point downloading anything for clean and help options.
        if env.GetOption('clean') or env.GetOption('help'):
            dfcache.enableDownload(False)
    return dfcache

_options = None

def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add(EnumVariable('download',
                                  "Set whether data file downloading is forced, "
                                  "automatic, or completely disabled.", 'auto',
                                  allowed_values=('force', 'auto', 'off'),
                                  ignorecase=2))
    _options.Update(env)
    env.AddMethod(_get_cache_instance, "DataFileCache")
    env.AddMethod(_download_data_file, "DownloadDataFile")

def exists(env):
    return True


