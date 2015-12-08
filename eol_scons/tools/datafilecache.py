"""
A SCons tool which adds a DataFileCache instance to an environment and
integrates with SCons builders to download data files and create
dependencies on the cached copies.
"""

def _sync_cache(target, source, env):
    dfcache = env.DataFileCache()
    if dfcache.sync():
        return None
    raise SCons.Errors.StopError("datasync failed.")

def _sync_file(target, source, env):
    dfcache = env.DataFileCache()
    if dfcache.download(str(source[0])):
        return None
    raise SCons.Errors.StopError("datasync failed.")

def _download_data_file(env, filepath):
    # Create a scons builder which downloads the source file into the cache.
    dfcache = env.DataFileCache()
    target = env.Command(dfcache.getFile(filepath),
                         env.Value(filepath), _sync_file)
    # Do not allow scons to erase the data file before re-synchronizing it.
    env.Precious(target)
    print("created command builder to download %s to %s" %
          (filepath, target[0].abspath))
    return target[0].abspath

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
        dfcache.cachepaths.append(path)
        env['DATA_FILE_CACHE'] = dfcache
        # No point downloading anything for clean and help options.
        if env.GetOption('clean') or env.GetOption('help'):
            dfcache.enableDownload(False)
    return dfcache


def generate(env):
    env.AddMethod(_get_cache_instance, "DataFileCache")
    env.AddMethod(_download_data_file, "DownloadDataFile")
    # Automatically provide a datasync alias for now, but this may be
    # better off deferred to an explicit request to create the alias.  If
    # this is deferred until after all the cache files are registered, then
    # the targets of this alias can be the actual cached files built by the
    # download builders, and the separate _sync_cache function would be
    # unnecessary.
    env.AlwaysBuild(env.Alias('datasync', None, _sync_cache))

def exists(env):
    return True


