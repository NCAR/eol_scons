import os

def ParseConfigPrefix(env, config_script, search_prefixes,
                      default_prefix = "$OPT_PREFIX"):
    """Search for a config script and parse the output."""
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in filter(lambda y: y, search_prefixes) ]
    prefix = default_prefix
    if env['PLATFORM'] != 'win32':    
        config = env.WhereIs(config_script, search_paths)
        try:
            env.ParseConfig(config + ' --cppflags --ldflags --libs')
            prefix = os.popen(config + ' --prefix').read().strip()
            ldflags = os.popen(config + ' --ldflags').read().split()
            for flag in ldflags:
                if (flag.strip().index('-L') == 0):
                    # remove the -L to get the directory, and make the
                    # resulting path absolute
                    dir = os.path.abspath(flag.replace('-L', ''))
                    env.Append(RPATH=dir)
        except:
            print "Error trying to run %s." % config_script
    return prefix

