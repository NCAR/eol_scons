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
# change the svnversion output.  svnverion can be slow to run since it must
# scan the whole source tree for svn version info and modified versioned
# files.  Since the version settings need to be applied to the environment
# when this tool is applied, and since other scons targets rely on those
# settings being current, this tool actually runs the SCons Taskmaster to
# update the implicit header node once it has been defined.  SCons seems to
# be able to detect whether svnversion needs to be updated faster than
# running svnversion by default.

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

import os
import re
import SCons
import traceback
import sys

from SCons.Builder import Builder
from SCons.Action import Action
from SCons.Node import FS
from SCons.Node.Python import Value
from subprocess import *

_debug = 0

def _find_svn_files(path):
    found = []
    for root, dirs, files in os.walk(path):
        # Look for the svn subdir first.
        svndirs = [ d for d in dirs if d in ['.svn', '_svn'] ]
        for d in svndirs:
            dirs.remove(d)
            for f in [ 'entries', 'all-wcprops' ]:
                path = os.path.normpath(os.path.join(root, d, f))
                if os.path.exists(path):
                    found.append(path)
    return found


def _get_workdir(source):
    workdir = source[0]
    if workdir.isfile():
        workdir = workdir.get_dir()
    if workdir.name in ['.svn', '_svn']:
        workdir = workdir.get_dir()
    if _debug: 
        print ("get_workdir(%s) ==> %s" % 
               (str(source[0]), workdir.get_abspath()))
    return workdir.get_abspath()

# Return a list of svn:externals subdirectories relative to the given working
# directory
def _getExternals(env, workdir):
    svncmd = [env.subst("$SVN"), 'status', workdir]
    child = Popen(svncmd, stdout=PIPE)
    svnstatus = child.communicate()[0].split('\n')
    externals = []
    for line in svnstatus:
        # 'svn status' lines which start with 'X' are externals
        if re.match('^X', line):
            subdir = re.sub('^X +', '', line)
            # remove the working directory from the subdir
            relativeSubdir = subdir.replace(workdir, '', 1)
            # then remove leading directory separator character, if any
            relativeSubdir = re.sub('^\\' + os.sep, '', relativeSubdir)
            externals += [relativeSubdir]
    print externals
    return externals

def svninfo_emitter_svnfiles(target, source, env):
    """
    Given an argument for svn info in the first source, return the svn
    admin files as sources, so that svn info and svnversion do not need to
    be run unless something in the svn admin files has changed.
    """
    workdir = _get_workdir(source)
    cache = env.CacheVariables()
    key = "svninfo_files" + re.sub(r'[^\w]', '_', workdir)
    svnfiles = cache.lookup(env, key)
    if not svnfiles:
        svnfiles = _find_svn_files(workdir)
        cache.store(env, key, "\n".join(svnfiles))
    else:
        svnfiles = svnfiles.split("\n")
    if _debug:
        print("svninfo_emitter: found %d svn admin files" % (len(svnfiles)))
    if _debug: sys.stdout.writelines(traceback.format_stack())
    return target, svnfiles


def _generateHeader(env, workdir):
    """Run svn info and svnversion to generate the header text."""
    if _debug: print("_generateHeader()")
    svncmd = [ env.subst("$SVN"), "info", workdir ]
    svndict = { "Revision":None, "Last Changed Date":None, "URL":None, 
               "ExternalRevs":None }
    svndict.update ( {"Working Directory":"Working Directory: %s" % workdir} )
    if _debug: print " ".join(svncmd)
    child = Popen(svncmd, stdout=PIPE)
    svninfo = child.communicate()[0]
    if _debug: print svninfo
    
    svnversioncmd = [ env.subst("$SVNVERSION"), "-n", workdir ]
    if _debug: print " ".join(svnversioncmd)
    child = Popen(svnversioncmd, stdout=PIPE)
    svnversion = child.communicate()[0]
    if _debug: print svnversion
    for k in svndict.keys():
        match = re.search(r"^%s: .*$" % (k), svninfo, re.M)
        if (match):
            svndict[k] = match.group()
    svndict.update ( {'workdir':workdir} )
    svndict['Revision'] = svnversion
    
    externals = _getExternals(env, workdir)
    svnExternRevs = ""
    for subdir in externals:
        subdirPath = os.path.join(workdir, subdir)
        svnversioncmd = [ env.subst("$SVNVERSION"), "-n", subdirPath ]
        child = Popen(svnversioncmd, stdout=PIPE)
        svnversion = child.communicate()[0]
        if subdir != externals[0]:
            svnExternRevs += ","
        svnExternRevs += subdir + ":" + svnversion
        if _debug: print svnExternRevs
    svndict['ExternalRevs'] = svnExternRevs
    
    for k, v in svndict.items():
        svndict[k] = v.replace('\\', '/').strip()
    svnheader = """
#ifndef SVNINFOINC
#define SVNINFOINC
#define SVNREVISION \"%(Revision)s\"
#define SVNEXTERNALREVS \"%(ExternalRevs)s\"
#define SVNLASTCHANGEDDATE \"%(Last Changed Date)s\"
#define SVNURL \"%(URL)s\"
#define SVNWORKDIRSPEC \"%(Working Directory)s\"
#define SVNWORKDIR \"%(workdir)s\"
#endif
""" % svndict
    if _debug: print svnheader
    return svnheader

def _apply_header(env, header):
    "Apply settings in the header to the environment."
    print("Applying svn variables from %s" % (header))
    hin = open(header, "r")
    lines = hin.readlines()
    hin.close()
    for line in lines:
        match = re.search(r"^#define (\w+) \"(.*)\"$", line)
        if (match):
            k = match.group(1)
            v = match.group(2)
            env[k] = v
            if _debug: print("  %s = %s" % (k, v))


def svninfo_emitter_value(target, source, env):
    """Given an argument for svn info in the first source, replace that
    source with a Value() node with the svn info contents."""
    workdir = _get_workdir(source)
    return target, [Value(_generateHeader(env, workdir))]

def svninfo_build_value(env, target, source):
    "Build header based on contents in the source."
    out = open(target[0].path, "w")
    out.write(source[0].get_contents())
    out.write("\n")
    out.close()

def svninfo_build_svnfiles(env, target, source):
    "Build header by generating it now."
    out = open(target[0].get_abspath(), "w")
    workdir = _get_workdir(source)
    out.write(_generateHeader(env, workdir))
    out.write("\n")
    out.close()

# svninfobuilder = Builder(
#     action = Action(svninfo_build_value, lambda t,s,e: "Generating %s"%t[0]),
#     source_factory = FS.default_fs.Entry,
#     emitter = svninfo_emitter_value)


svninfobuilder = Builder(
    action = Action(svninfo_build_svnfiles,
                    lambda t,s,e: "Generating %s"%t[0]),
    source_factory = FS.default_fs.Entry,
    emitter = svninfo_emitter_svnfiles)


class SvnInfoWarning(SCons.Warnings.Warning):
    pass


_svninfonode = None


def SvnInfo(env, target, source):
    """Wrapper method to create a builder for the target header."""
    # A top-level svnInfo.h file is generated implicitly by the svninfo
    # tool, and usually this is enough.  Call this builder from a
    # SConscript file to create additional header files which perhaps
    # depend only upon a subdirectory of the project.  However, to set
    # those variables correctly, the header file must be generated
    # immediately in case svnversion and svn info need to be run.  All this
    # is to avoid running 'svn info' and 'svnversion' unless really
    # necessary.
    #
    # As a special porting case, ignore any explicit requests to build the
    # same file as the implicit header.
    global _svninfonode
    if _debug: print("SvnInfo(%s,%s)" % (str(target), str(source)))
    if _debug:
        print("target=%s, svninfonode=%s" % (str(target), str(_svninfonode)))
    if _debug: sys.stdout.writelines(traceback.format_stack())
    if _svninfonode and str(target) == str(_svninfonode):
        print("SvnInfo: %s is already an implicit target." % str(target))
        return [_svninfonode]
    node = env.SvnInfoBuilder(target, source)[0]
    # In building this node, scons calls
    # SCons.Defaults.DefaultEnvironment(), which creates a default
    # Environment, which recursively enters eol_scons._generate() and may
    # require this module again.  Therefore we need to guard against that
    # by updating _svninfonode here, before running the build.
    if not _svninfonode:
        _svninfonode = node
    tm = SCons.Taskmaster.Taskmaster([node], SCons.Script.Main.BuildTask)
    SCons.Script.Main.BuildTask.options = SCons.Script.Main.OptionsParser.values
    jobs = SCons.Job.Jobs(1, tm)
    jobs.run()
    # node.make_ready()
    # if node.changed():
    #     print("%s needs to be rebuilt..." % (node.get_abspath()))
    #     print(node.explain())
    #     node.prepare()
    #     node.build()
    #     node.built()
    # else:
    #     print("%s has no changes" % (str(node)))

    # Now update the environment with whatever settings are in that header
    # file.
    _apply_header(env, node.get_abspath())
    return [node]


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

    if _debug: print("svninfo: generate()")
    env['BUILDERS']['SvnInfoBuilder'] = svninfobuilder
    env['SVN'] = "svn"
    env['SVNVERSION'] = "svnversion"
    # Use the default location for the subversion Windows installer.
    if env['PLATFORM'] == 'win32':
        svnbin=r'c:\Program Files\Svn'
        env['SVN'] = os.path.join(svnbin, "svn")
        env['SVNVERSION'] = os.path.join(svnbin, "svnversion")
    env.AddMethod(SvnInfo, 'SvnInfo')

    global _svninfonode
    if _svninfonode == None:
        if _debug: print("svninfo: creating implicit svnInfo.h")
        _svninfonode = env.SvnInfo('svnInfo.h', '#')[0]

    else:
        if _debug: print("svninfo: applying existing svnInfo.h")
        # The header has already been created and updated,
        # so just update the environment with the settings.
        _apply_header(env, _svninfonode.get_abspath())


def exists(env):
    svn = env.WhereIs('svn')
    if not svn:
        SCons.Warnings.warn(
            SvnInfoWarning,
            "Could not find svn program.  svninfo tool not available.")
        return False
    return True
