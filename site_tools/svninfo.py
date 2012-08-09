# -*- python -*-
"""
Provide Subversion construction variables derived from 'svnversion' and
'svn info', and provide a builder wrapper for generating a header file
with definitions for those values.
"""

# This tool works by first creating a default, top-level header target
# which contains the version settings and depends upon key svn
# administration files in the source tree.  The point is to avoid running
# 'svn info' and 'svnversion' unless something has changed which would
# change the svnversion output.  svnversion can be slow to run since it
# must scan the whole source tree for svn version info and modified
# versioned files.  Since the version settings need to be applied to the
# environment when this tool is applied, and since other scons targets rely
# on those settings being current, this tool actually runs the SCons
# Taskmaster to update the implicit header node once it has been defined.
# SCons seems to be able to detect whether svnversion needs to be updated
# faster than running svnversion by default.

# NOTE: The svn admin files change if there is an svn operation like update,
# commit, add, or delete.  However, after an update or commit to a clean
# checkout, the svnversion is R, unmodified.  Then a file is modified
# outside of svn, making the svnversion Rm, but svnversion will not be
# re-run because none of the svn admin files changed.  All the svn-versioned
# files in the tree could be added as dependencies of svninfo, similar to
# the svn admin dependencies, or perhaps even in place of the svnadmin
# dependencies.  However, then svnversion gets rerun each time any file
# changes, even though the version output won't actually change.  It's like
# the dependencies need to be different if the tree is 'clean' or not.  If
# it's clean, the dependencies are all the source files.  If not, the
# dependencies are all the svn admin files.

# August 8, 2012
#
# The caching has been abandoned, and SVN 1.7 no longer keeps .svn admin
# directories throughout the tree, and the .svn dependency was not
# completely correct anyway as mentioned above, so revert to always
# retrieving the svn version information.  It is retrieved when this tool
# is loaded so that the version information is available in the environment
# construction variables.  The version information is also cached in this
# module by working directory, to optimize the case where the SConscript
# which loads the svninfo tool is in the working directory as a target
# header file.  There is no point in caching the info between scons runs
# because there is no way to tell if it needs to be updated or not, thus it
# needs to be refreshed each time.  However, any nodes which depend on the
# version information, such as header files, should not be rebuilt unless
# the version information this run is different than the last run.  For
# that we rely on scons caching of Value nodes whose content is the header
# file.
#
# Some source trees (aeros) use the revision value from the environment
# even if a header is not generated, thus the version info must be
# retrieved and loaded into the environment even if there is not a header
# target.  The source for this version information is implicitly the
# directory of the SConscript file.

import os
import re

from SCons.Builder import Builder
from SCons.Action import Action
from SCons.Node import FS
from SCons.Node.Python import Value
from subprocess import *
import SCons.Warnings

_debug = 0

def pdebug(msg):
    if _debug: print(msg)

class SubversionInfo:

    # Map construction variable name to the svn info keys.
    _variable_map = {
        'SVNREVISION' : "Revision",
        'SVNEXTERNALREVS' : "ExternalRevs",
        'SVNLASTCHANGEDDATE' : "Last Changed Date",
        'SVNURL' : "URL",
        'SVNWORKDIRSPEC' : "Working Directory",
        'SVNWORKDIR' : "workdir"
        }

    def __init__(self, env, workdir):
        self.workdir = workdir
        self.values = {}
        self.svncmd = env.subst("$SVN")
        self.svnversioncmd = env.subst("$SVNVERSION")
        for k in self._variable_map.keys():
            self.values[k] = "unknown"

    def _get_output(self, cmd):
        "Get command output, or an empty string if the command fails."
        output = ""
        try:
            pdebug("svninfo: running '%s'" % (" ".join(cmd)))
            child = Popen(cmd, stdout=PIPE)
            output = child.communicate()[0]
            pdebug("svninfo output: %s" % (output))
        except OSError, e:
            print("Warning: svn info '%s' failed: %s" % (" ".join(cmd), str(e)))
        return output

    def getExternals(self):
        """
        Return a list of svn:externals subdirectories relative to the given
        working directory.
        """
        workdir = self.workdir
        svncmd = [self.svncmd, 'status', workdir]
        svnstatus = self._get_output(svncmd).split('\n')
        externals = []
        for line in svnstatus:
            # 'svn status' lines which start with 'X' are externals
            if re.match('^X', line):
                subdir = re.sub('^X +', '', line)
                # remove the working directory from the subdir
                relativeSubdir = subdir.replace(workdir, '', 1)
                # remove the trailing cr, found on windows systems
                relativeSubdir = re.sub('\r','',relativeSubdir)
                # then remove leading directory separator character, if any
                relativeSubdir = re.sub('^\\' + os.sep, '', relativeSubdir)
                externals += [relativeSubdir]
        return externals

    def loadInfo(self):
        workdir = self.workdir
        svncmd = [ self.svncmd, "info", workdir ]
        svndict = { "Revision":None, "Last Changed Date":None, "URL":None, 
                   "ExternalRevs":None }
        svndict.update ( {"Working Directory":"Working Directory: %s" % workdir} )
        svninfo = self._get_output(svncmd)
        svnversioncmd = [ self.svnversioncmd, "-n", workdir ]
        svnversion = self._get_output(svnversioncmd)
        for k in svndict.keys():
            match = re.search(r"^%s: .*$" % (k), svninfo, re.M)
            if (match):
                svndict[k] = match.group()
        svndict.update ( {'workdir':workdir} )
        svndict['Revision'] = svnversion

        externals = self.getExternals()
        svnExternRevs = ""
        for subdir in externals:
            subdirPath = os.path.join(workdir, subdir)
            svnversioncmd = [ self.svnversioncmd, "-n", subdirPath ]
            svnversion = self._get_output(svnversioncmd)
            if subdir != externals[0]:
                svnExternRevs += ","
            svnExternRevs += subdir + ":" + svnversion
            pdebug(svnExternRevs)
        svndict['ExternalRevs'] = svnExternRevs

        # Normalize paths and urls.
        for k, v in svndict.items():
            if v:
                svndict[k] = v.replace('\\', '/').strip()

        # Fill in the key variables from the svn info dictionary, but only
        # if there is a value there.
        for k,v in self._variable_map.items():
            if svndict[v]:
                self.values[k] = svndict[v]
        return self

    def applyInfo(self, env):
        "Apply info values to the environment."
        pdebug("Applying svn info from %s..." % (self.workdir))
        for k,v in self.values.items():
            env[k] = v

    def generateHeader(self):
        svnheader = """
#ifndef SVNINFOINC
#define SVNINFOINC
#define SVNREVISION \"%(SVNREVISION)s\"
#define SVNEXTERNALREVS \"%(SVNEXTERNALREVS)s\"
#define SVNLASTCHANGEDDATE \"%(SVNLASTCHANGEDDATE)s\"
#define SVNURL \"%(SVNURL)s\"
#define SVNWORKDIRSPEC \"%(SVNWORKDIRSPEC)s\"
#define SVNWORKDIR \"%(SVNWORKDIR)s\"
#endif
"""
        svnheader = svnheader % self.values
        pdebug(svnheader)
        return svnheader


def _get_workdir(source):
    pdebug("_get_workdir source=" + str(['%s' % d for d in source]))
    workdir = source[0]
    if workdir.isfile():
        workdir = workdir.get_dir()
    if workdir.name in ['.svn', '_svn']:
        workdir = workdir.get_dir()
    pdebug("get_workdir(%s) ==> %s" % (str(source[0]), workdir.get_abspath()))
    return workdir.get_abspath()


_svninfomap = {}

def _load_svninfo(env, workdir):
    """Run svn info and svnversion and load the info into a dictionary."""
    global _svninfomap
    if _svninfomap.has_key(workdir):
        pdebug("_load_svninfo: returning cached svninfo for %s" % (workdir))
        return _svninfomap[workdir]
    pdebug("_load_svninfo(%s): creating svninfo" % (workdir))
    sinfo = SubversionInfo(env, workdir)
    _svninfomap[workdir] = sinfo.loadInfo()
    return sinfo


def svninfo_emitter_value(target, source, env):
    """Given an argument for svn info in the first source, replace that
    source with a Value() node with the svn info contents."""
    workdir = _get_workdir(source)
    svninfo = _load_svninfo(env, workdir)
    return target, [Value(svninfo.generateHeader())]

def svninfo_build_value(env, target, source):
    "Build header based on contents in the source."
    out = open(target[0].path, "w")
    out.write(source[0].get_contents())
    out.write("\n")
    out.close()

svninfobuilder = Builder(
    action = Action(svninfo_build_value, lambda t,s,e: "Generating %s" % (t[0])),
    source_factory = FS.default_fs.Entry,
    emitter = svninfo_emitter_value)


class SvnInfoWarning(SCons.Warnings.Warning):
    pass


def generate(env):
    """
    Add svn info and version for the top directory to the environment, and
    provide a builder for generating a header file with the definitions.
    """
    # We need the most current svn info at this point to add it to the
    # environment.  We cannot rely on a regular builder to generate the
    # information by running svnversion later, because by then it is too
    # late.  To cache the version info between runs and between
    # applications of the svninfo tool, we use a single implicit builder
    # for a top-level header file.

    pdebug("svninfo: generate()")
    env['BUILDERS']['SvnInfo'] = svninfobuilder
    env['SVN'] = "svn"
    env['SVNVERSION'] = "svnversion"
    # Use the default location for the subversion Windows installer.
    if env['PLATFORM'] == 'win32':
        svnbin=r'c:\Program Files\Svn'
        env['SVN'] = os.path.join(svnbin, "svn")
        env['SVNVERSION'] = os.path.join(svnbin, "svnversion")

    workdir = env.Dir('.').get_abspath()
    svninfo = _load_svninfo(env, workdir)
    svninfo.applyInfo(env)


def exists(env):
    svn = env.WhereIs('svn')
    if not svn:
        SCons.Warnings.warn(
            SvnInfoWarning,
            "Could not find svn program.  svninfo tool not available.")
        return False
    return True
