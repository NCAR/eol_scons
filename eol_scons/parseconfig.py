import os

def ParseConfigPrefix(env, config_script, search_prefixes,
                      default_prefix = "$OPT_PREFIX", apply_config = False):
    """Search for a config script and parse the output."""
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in [ y for y in search_prefixes if y ] ]
    prefix = default_prefix
    if env['PLATFORM'] != 'win32':    
        env.LogDebug("Checking for %s in %s" % 
                     (config_script, ",".join(search_paths)))
        config = env.WhereIs(config_script, search_paths)
        env.LogDebug("Found: %s" % config)
        prefix = os.popen(config + ' --prefix').read().strip()
        if apply_config:
            env.ParseConfig(config + ' --cppflags --ldflags --libs')
            ldflags = os.popen(config + ' --ldflags').read().split()
            for flag in ldflags:
                if (flag.strip().index('-L') == 0):
                    # remove the -L to get the directory, and make the
                    # resulting path absolute
                    dir = os.path.abspath(flag.replace('-L', ''))
                    env.Append(RPATH=dir)
    return prefix


def PkgConfigPrefix(env, pkg_name, default_prefix = "$OPT_PREFIX"):
    """Search for a config script and parse the output."""
    search_prefixes = ['/usr']
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in filter(lambda y: y, search_prefixes) ]
    prefix = None
    if env['PLATFORM'] != 'win32':    
        config = env.WhereIs('pkg-config', search_paths)
        prefix = os.popen(config + ' --variable=prefix ' +
                          pkg_name).read().strip()
    if not prefix:
        prefix = default_prefix
    return prefix
