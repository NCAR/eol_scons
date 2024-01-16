# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
This tool creates construction variables derived from a git repository,
representing characteristics of the repository. These variables can be
accessed directly in the scons environment. It also can generate a C header
file with defines based on the same information.

See the eol_scons.gitinfo.GitInfo class for information on how the git repo
information is collected.

Example usage:

    env = Environment(tools = ['default', gitinfo'])
    repoinfo = env.GitInfo('repoInfo.h', '#/')
    env.Default(repoinfo)

Useful hint: If a scons tool such as this (i.e contains exists() and
generate()) is not located in the site_tools directory,
just add a toolpath to locate it. E.g:

    env = Environment(tools = ['default', 'gitinfo'], toolpath=['#/'])

There are two parts to the source code for this tool.
1. The GitInfo class manages the collection of git information.
2. The collection of global functions provides the framework of the scons tool.

Just specifying gitinfo as a tool causes the repository variables to be
added to the environment. These variables are accessed as env['REPO_REVISION'],
env['REPO_TAG'], as shown above. See the GitInfo class below for the full list.

The tool adds a builder named GitInfo (same name as the helper class) to
the environment, which is used to create a file containing the C header
text.

This code is adapted from the svninfo.py tool, which provides similar
functionality for a subversion based source tree.

The scons builder takes a working directory as the source argument, e.g.

    env.GitInfo('repoInfo.h', '#/')

A new GitInfo instance is created and cached for each working directory that
is specified. However, GitInfo does not currently use the source directory in
any way. It was useful for the earlier svninfo tool, since subversion
versioning information is dependent upon the directory that svn info is
applied to. The convention has been retained in gitinfo, as there may be a
need for this later.
"""

import os

from SCons.Builder import Builder
from SCons.Script import BoolVariable
from SCons.Script import COMMAND_LINE_TARGETS
from SCons.Action import Action
from SCons.Node import FS
from SCons.Node.Python import Value
import SCons.Warnings
from eol_scons.gitinfo import GitInfo

# Set to 1 to enable debugging output
_debug = 0


# Debugging print
def pdebug(msg):
    if _debug:
        print(msg)


def _get_workdir(env, source):
    """
    Normalize the directory of source (or source[0]).

    If source is a list, use the first item in the list as the source.
    If source is file name, return the containing directory.
    If source is a directory, return that as the working directory.
    If source is .git or _git directory, return the containing directory.
    """

    pdebug("_get_workdir source=" + str(['%s' % d for d in source]))
    workdir = source
    if isinstance(source, str):
        workdir = env.Dir(source)
    elif isinstance(source, list):
        workdir = source[0]
    if workdir.isfile():
        workdir = workdir.get_dir()
    if workdir.name in ['.git', '_git']:
        workdir = workdir.get_dir()
    pdebug("get_workdir(%s) ==> %s" % (str(source[0]), workdir.get_abspath()))
    return workdir.get_abspath()


# A dictionary used to cache a GitInfo instance for a given working directory.
_gitinfomap = {}


def _create_gitinfo(env, workdir) -> GitInfo:
    "Create a new GitInfo instance, for this workdir."
    global _gitinfomap
    pdebug("_create_gitinfo(%s): creating gitinfo" % (workdir))
    ginfo = GitInfo(env)
    _gitinfomap[workdir] = ginfo

    # Wherever gitinfo is loaded, create an alias to dump it.  This is could
    # cause surprising behavior for projects without any Default() targets,
    # since they will automatically build this target and print the repo info,
    # so only do this if a gitdump target appears explicitly in the
    # command-line targets.  The intention is to make it easy for other
    # scripts, especially packaging scripts, to query for the same version
    # information as the build is using.  However, that same information can
    # also be parsed from generated header files, and the output in the header
    # files could even be extended to make it easier to parse.  So it's not
    # clear yet if this will be useful.
    if any(['gitdump' in target for target in COMMAND_LINE_TARGETS]):
        def gitdump(target, source, env):
            ginfo.dump()
        gitdump = env.Command('%s/gitdump' % (workdir), None,
                              Action(gitdump, cmdstr=None))
        env.Alias('gitdump', gitdump)
        pdebug('gitinfo: created target %s' % (str(gitdump[0])))
    return ginfo


def _load_gitinfo(env, workdir, target=None):
    """
    Return an instance of GitInfo for the specified directory.

    Cache the results in the _gitinfomap dictionary.
    """
    global _gitinfomap
    if workdir in _gitinfomap:
        # Result already cached for this workdir
        pdebug("_load_gitinfo: using cached gitinfo for %s" % (workdir))
        ginfo = _gitinfomap[workdir]
    else:
        ginfo = _create_gitinfo(env, workdir)

    # if gitinfo is enabled, load the repo info from git,
    # otherwise load it from target if available.
    if ginfo.repopath:
        pdebug("...repo info already loaded...")
    elif env.get("gitinfo", True):
        pdebug('...loading repo info with git...')
        ginfo.getRepoInfo(workdir)
    elif target:
        path = str(target[0])
        print("Loading repo info from header: %s" % (path))
        ginfo.loadFromHeader(path)

    # always make sure any updates are applied to the environment.
    pdebug("gitinfo: applying gitinfo to env")
    ginfo.applyToEnv(env)
    return ginfo


def gitinfo_emitter_value(target, source, env):
    """
    Given an argument for git info in the first source, replace that source
    with a Value() node with the git info contents.
    """
    pdebug("gitinfo_emitter_value(%s,%s,%s)..." %
           (str(target[0]), str(source[0]), str(env.Dir('.'))))
    workdir = _get_workdir(env, source)
    gitinfo = _load_gitinfo(env, workdir, target)
    # If the git info command fails with an error, don't update the target if
    # it already exists.  That is perhaps misleading, since the file could
    # have outdated information.  Perhaps the build should actually fail,
    # especially now that source builds can set gitinfo=off to disable git
    # calls and explicitly accept the existing files as correct.
    #
    # Mark the target as Precious so that scons doesn't delete it before the
    # check for existence in the action.  Add an alias to generate version
    # files for any project, regardless of how they are named, such as before
    # assembling a source archive.
    env.Precious(target)
    env.Alias('versionfiles', target)
    return target, [Value(gitinfo.generateHeader())]


def gitinfo_do_update_target(target, source):
    # If a git error, don't overwrite existing file
    text = source[0].get_text_contents()
    return text.find("Git error:") < 0 or not os.path.exists(target[0].path)


def gitinfo_action_print(target, source, env):
    if not env.get("gitinfo", True):
        return "gitinfo disabled, not generating %s" % (target[0])
    if gitinfo_do_update_target(target, source):
        return "Generating %s" % target[0]
    return "Not updating %s" % target[0] + " due to git error"


def gitinfo_build_value(env, target, source):
    """
    Build header based on contents in the source.  If gitinfo has been
    disabled, then this does nothing.
    """
    pdebug("gitinfo_build_value()...")
    if not env.get("gitinfo", True):
        return
    if gitinfo_do_update_target(target, source):
        out = open(target[0].path, "w")
        text = source[0].get_text_contents()
        out.write(text)
        out.write("\n")
        out.close()


class GitInfoWarning(SCons.Warnings.WarningOnByDefault):
    pass


def generate(env):
    """
    Add git info and version for the top directory to the environment, and
    provide a builder for generating a header file with the definitions.
    """
    # We need the most current git info at this point to add it to the
    # environment.  We cannot rely on a regular builder to generate the
    # information by running git later, because by then it is too late.  To
    # cache the version info between runs and between applications of the
    # gitinfo tool, we use a single implicit builder for a top-level header
    # file.

    pdebug("gitinfo: generate()")
    variables = env.GlobalVariables()
    if 'gitinfo' not in variables.keys():
        variables.Add(BoolVariable("gitinfo", help="When off, "
                  "do not run any git tools or update any version "
                  "headers.  "
                  "This is useful for building from source distributions "
                  "which already contain generated version files.",
                  default=True))
    variables.Update(env)

    gitinfobuilder = Builder(
        action=Action(gitinfo_build_value, gitinfo_action_print),
        source_factory=FS.default_fs.Entry,
        emitter=gitinfo_emitter_value)
    env['BUILDERS']['GitInfo'] = gitinfobuilder
    env['GIT'] = "git"
    if env['PLATFORM'] == 'win32':
        gitbin = r'c:\Tools\git\bin'
        env.PrependENVPath('PATH', gitbin)

    env.AddMethod(LoadGitInfo, "LoadGitInfo")
    env.LoadGitInfo('#')


def LoadGitInfo(env, source, target=None):
    """
    Get the git info for the source directory, parsing the output from git
    tools if the info has not already been cached, and set the repo info
    variables in the environment.  If gitinfo is disabled and a header file
    target has been given, then try to parse the git info from the target
    instead.
    """
    workdir = _get_workdir(env, source)
    gitinfo = _load_gitinfo(env, workdir, target)


def exists(env):
    git = env.WhereIs('git')
    if not git:
        SCons.Warnings.warn(
            GitInfoWarning,
            "Could not find git program. gitinfo tool not available.")
        return False
    return True
