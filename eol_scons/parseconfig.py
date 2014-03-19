import os
import re

from subprocess import *

_debug = False

def _extract_results(text):
    # The string result and integer returncode are coded in the cached
    # string as '<returncode>,<resultstring>'.  Sometimes the result
    # strings have more than one line, so we must be careful to extract the
    # rest of the string, including any newlines.
    m = re.match(r"^([-+]?\d+),", text)
    if m:
        return (int(m.group(1)), text[m.end():])
    else:
        return (-1, text)


def _get_config(env, search_paths, config_script, args):
    """Return a (result, returncode) tuple for a call to @p config_script."""

    result = None
    if _debug: print("_get_config(%s,%s): " % (config_script, ",".join(args)))
    # See if the output for this config script call has already been cached.
    name = re.sub(r'[^\w]', '_', config_script + " ".join(args))
    cache = env.CacheVariables()
    result = cache.lookup(env, name)
    if result:
        if _debug: print("  cached: %s" % (result))
        return _extract_results(result)
    if not result:
        if search_paths:
            search_paths = [ p for p in search_paths if os.path.exists(p) ]
            env.LogDebug("Checking for %s in %s" % 
                         (config_script, ",".join(search_paths)))
            config = env.WhereIs(config_script, search_paths)
        else:
            config = config_script
        env.LogDebug("Found: %s" % config)
    if not result and config:
        child = Popen([config] + args, stdout=PIPE)
        result = child.communicate()[0].strip()
        cache.store(env, name, "%s,%s" % (child.returncode, result))
        result = (child.returncode, result)
    if not result:
        result = (-1, "")
    if _debug: print("   command: %s" % (str(result)))
    return result


def RunConfig(env, command):
    args = command.split()
    config_script = args[0]
    args = args[1:]
    return _get_config(env, None, config_script, args)[1]


def CheckConfig(env, command):
    "Return the return code from a pkg-config-like command."
    args = command.split()
    config_script = args[0]
    args = args[1:]
    return _get_config(env, None, config_script, args)[0]


def _filter_ldflags(flags):
    "Fix ldflags from config scripts which return standard library dirs."
    fields = flags.split()
    fields = [ f for f in fields if not re.match(r'^-L/usr/lib(64)?$', f) ]
    flags = " ".join(fields)
    return flags


def ParseConfigPrefix(env, config_script, search_prefixes,
                      default_prefix = "$OPT_PREFIX", apply_config = False):
    """Search for a config script and parse the output."""
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in [ y for y in search_prefixes if y ] ]
    if search_paths:
        search_paths = [ p for p in search_paths if os.path.exists(p) ]
    prefix = default_prefix
    if env['PLATFORM'] == 'win32':    
        return prefix

    prefix = _get_config(env, search_paths, config_script, ['--prefix'])[1]
    if apply_config:
        flags = _get_config(env, search_paths, config_script,
                            ['--cppflags', '--ldflags', '--libs'])[1]
        if flags:
            if _debug: print("Merging " + flags)
            flags = _filter_ldflags(flags)
            env.MergeFlags(flags)
        else:
            if _debug: print("No flags from %s" % (config_script))
        ldflags = _get_config(env, search_paths, config_script,
                              ['--ldflags'])[1]
        ldflags = _filter_ldflags(ldflags)
                              
        if ldflags:
            ldflags = ldflags.split()
            for flag in ldflags:
                if flag.find('-L') != -1:
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
        prefix = _get_config(env, search_paths, 'pkg-config',
                             ["--variable=prefix", pkg_name])[1]
    if not prefix:
        prefix = default_prefix
    return prefix


