"""
There was a time when importing eol_scons did not seem to work,
especially when trying to use an alternate location for site_scons.  For
example, aircraft_nc_utils can use vardb/site_scons under the vardb
submodule, or nimbus might use the site_scons from the parent raf
directory.  Basically, any time we want to supply a backup site_scons
location in case it is not found in the usual path: ~/.scons/site_scons,
#/site_scons, and so on.  This module provides some code to detect when
eol_scons is not available, and if not, then restart scons with the right
--site-dir option to find the backup location.

It turns out it still works to just add the backup site_scons location to
the python system path.  So this is all that is needed in the SConstruct:

    sys.path.append(os.path.abspath('vardb/site_scons'))

When eol_scons is imported as a package, it takes care of adding to the
scons tool path and inserting all the hooks it needs.

However, should anything fancier ever be needed, this code could be useful.
These are the intended uses for this module in the SConstruct file:

    sys.path.append('vardb/site_scons')
    import eol_scons.sitedir as sitedir
    sitedir.rerunIfToolsMissing()
    import eol_scons

Or here is the basic idea without using a module and some extra checks.  I
can't remember if this approach worked; it may have been susceptible to
infinite recursion.

    try:
        import eol_scons
    except ImportError:
        if "--site-dir" not in sys.argv:
            print("restarting scons with default site-dir")
            os.execv(sys.argv[0], sys.argv + ['--site-dir', 'vardb/site_scons'])
        raise

This was an approach which requires a sitedir.py module in the top
directory, but obviously it makes more sense to have a single copy in
eol_scons, and import it from the backup location:

    import sitedir
    sitedir.rerunWithSiteDir(["vardb"])
    import eol_scons
"""


import os
import sys

from SCons.Tool import DefaultToolpath
from SCons.Script import AddOption
from SCons.Script import GetOption

print("loading sitedir.py")

def execWithSiteDir(site_dir):
    # Exec scons again, but this time with site-dir set.
    _scons_command = sys.argv[:]
    # Assume at this point that scons has already set the current working
    # directory to the top of tree, and that the site dir paths are
    # relative to that directory, so absolute paths would just make things
    # more verbose.
    #
    # site_dir = os.path.abspath(site_dir)
    _scons_command.extend(['--site-dir='+site_dir])
    _scons_command = [arg for arg in _scons_command
                      if arg != "--search-site-dir"]
    print("Restarting scons with --site-dir=%s" % (site_dir))
    print(" ".join(_scons_command))
    os.execv(_scons_command[0], _scons_command)
    # It's very important here that this not recurse.  Since --site-dir is
    # being passed on the command line, then when this function is called
    # again it should just return.


def rerunIfToolsMissing():
    """
    Assuming this module was loaded from inside the eol_scons package, then
    either the eol_scons tools directory is already in the DefaultToolPath,
    or we need to re-run scons with this directory as the site-directory.
    """
    thisdir = os.path.dirname(__file__)
    tooldir = os.path.abspath(os.path.join(thisdir, "tools"))
    sitedir = os.path.abspath(os.path.dirname(thisdir))
    print("tooldir=%s" % (tooldir))
    print("toolpath=%s" % (":".join(DefaultToolpath)))
    if tooldir not in DefaultToolpath:
        execWithSiteDir(sitedir)


def rerunWithSiteDir(site_dir_path):
    """
    If no site-dir has been set explicitly and eol_scons cannot be
    imported, then look for the first site_scons directory found in the
    directories in list site_dir_path.
    """
    AddOption('--search-site-dir', action='store_true',
              dest='search_site_dir', default=False)
    no_site_dir = GetOption('no_site_dir')
    site_dir = GetOption('site_dir')
    # Pass search-site-dir to force the path search, even if
    # a site_scons exists on the default SCons path
    search_site_dir = GetOption('search_site_dir')
    if not search_site_dir and (site_dir or no_site_dir):
        print("--site-dir or --no-site-dir passed, and not overridden "
              "with --search-site-dir, so rerunWithSiteDir() just "
              "returning.")
        return
    # This assumes eol_scons has not been added to the path manually
    # somewhere, because we're using it to test whether scons has already
    # found it and added it to the python path.
    if not search_site_dir:
        try:
            # This assumes eol_scons has not been added to the path manually
            # somewhere.
            import eol_scons
            return
        except ImportError:
            pass
    # Reset site_dir since we're going to search for it, perhaps because
    # search_site_dir is enabled.
    site_dir = None
    for path in site_dir_path:
        test_path = os.path.join(path, "site_scons")
        if os.path.exists(test_path):
            site_dir = test_path
            break
    if not site_dir:
        print("--site-dir not set, and none could be found in the \n"
              "alternate paths:\n"
              ":".join(site_dir_path))
        return
    execWithSiteDir(site_dir)
