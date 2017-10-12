# -*- python -*-
"""
A scons tool for creating versioning and other metadata
based on a git working branch and its source repository.

This tool creates construction variables derived from a git repository, 
representing characteristics of the repository. These variables can be
accessed directly in the scons environment. It also can generate
a C header file with defines based on the same information.

The git information is based on the most recent annotated git tag 
that can be reached through 'git describe'. This is combined
with the number of commits since that tag to create a distinct
revision number which can be traced to a particular git commit.

Remember: _The tag must be a git annotated tag_

The git describe uses a '--match [vV][0-9]*' argument for a
file-glob style match on possible tags, looking for one that
starts with 'v' or 'V', followed by a number, followed by anything.

Example usage:
env = Environment(tools = ['default', gitinfo'])
repoinfo = env.GitInfo('repoInfo.h', '#/')
env.Default(repoinfo)
 
Example variable assigments:
env['REPO_TAG']       V3.2
env['REPO_COMMITS']   26
env['REPO_REVISION']  V3.2-26
env['REPO_DATE']      Wed Dec 3 13:45:13 2014 -0700
env['REPO_BRANCH']    develop
env['REPO_WORKDIR']   /Users/martinc/git/aspen
env['REPO_URL']       https://github.com/ncareol/aspen.git
env['REPO_EXTERNALS'] unknown
env['REPO_HASH']      6badaf8a78527b248adcda4a88c0579dcb90198a

Example generated header file text:
/*  */
#ifndef GITINFOINC
#define GITINFOINC

#define REPO_REVISION  "V3.2-26"
#define REPO_EXTERNALS "unknown"
#define REPO_DATE      "Wed Dec 3 13:45:13 2014 -0700"
#define REPO_WORKDIR   "/Users/martinc/git/aspen"
#define REPO_URL       "https://github.com/ncareol/aspen.git"
#define REPO_HASH      "6badaf8a78527b248adcda4a88c0579dcb90198a"
#define REPO_COMMITS   "26"
#define REPO_TAG       "V3.2"
#define REPO_BRANCH    "develop"

#endif

Notes:
Git commands are used to extract the information.

Useful hint: If a scons tool such as this (i.e contains exists() and
generate()) is not located in the site_tools directory,
just add a toolpath to locate it. E.g:
env = Environment(tools = ['default', 'gitinfo'], toolpath=['#/'])

There are two parts to the source code for this tool. 
1) The GitInfo class manages the collection of git information. 
2) The collection of global functions provides the framework of the scons tool.

Just specifying gitinfo as a tool causes the repository variables to be
added to the environment. These variables are accessed as env['REPO_REVISION'],
env['REPO_TAG'], as shown above. See the GitInfo class below for the full list.

The tool adds a builder named GitInfo (same name as the helper class) to
the environment, which is used to create a file containing the C header
text.

This code is adapted from the svninfo.py tool, which provides similar
functionality for a subversion based source tree.

The scons builder takes a working directory as the source argument
(e.g. env.GitInfo('repoInfo.h', '#/').  A new GitInfo instance is created
and cached for each working directory that is specified. However, GitInfo
does not currently use the source directory in any way. It was useful for
the earlier svninfo tool, since subversion versioning information is
dependent upon the directory that svn info is applied to. The convention
has been retained in gitinfo, as there may be a need for this later.
"""
from __future__ import print_function

import os
import re
import string
from subprocess import *

# Set to 1 to enable debugging output
_debug = 0

# Debugging print
def pdebug(msg):
    if _debug: print(msg)

#####################################################################
class GitInfo:
    """
    Encapsulate the repository characteristics, making them avaiable via a
    dictionary.
    
    Git commands used to extract the repository information:

    git describe --match [vV][0-9]*:

      Looks for a tag starting with 'v' or 'V' followed by a number
      followed by anything.  Returns string with up to three tokens:
      V3.2-4-g3189d8e.  First token is the last matching tag on the branch.
      Second token is the number of commits since the tag.  Third is the
      abbreviate object name of the last commit.  If the tag points to the
      most recent commit, then commit is '0'.
                  
    git config --get remote.origin.url:

      Get the repository URL that this branch was fetched from.
                  
    git log --pretty=format:"%cd,%H" -1: 

      Get the date and hash of the last commit in a form easily split.

      Wed Nov 26 16:42:30 2014 -0700,3189d8e443a6cf5827fc9617ebe8b95ab83d8eaf
    
    git rev-parse --show-toplevel: 

      Find the top of the working directory: /Users/martinc/git/aspen

    git status --porcelain:

      Get a list of any modified or unknown files in this checkout.  These
      are stored in the REPO_DIRTY key.  If this is not empty, then the git
      revision will have the suffix 'M'.
    """

    # The repository info keys.
    _variable_map = {
        'REPO_REVISION'        : None,
        'REPO_EXTERNALS'       : None,
        'REPO_DATE'            : None,
        'REPO_URL'             : None,
        'REPO_WORKDIR'         : None,
        'REPO_ERROR'           : None,
        'REPO_TAG'             : None,
        'REPO_COMMITS'         : None,
        'REPO_HASH'            : None,
        'REPO_BRANCH'          : None,
        'REPO_DIRTY'           : None
        }

    def __init__(self, env):
        # Specify the git command
        self.gitcmd = env.get('GIT', 'git')
        self.match = env.get('GIT_DESCRIBE_MATCH', '[vV][0-9]*')

        # Initialize the repo values.
        self.values = {}
        for k in self._variable_map.keys():
            self.values[k] = "unknown"
        self.values['REPO_ERROR'] = ""

    def _get_output(self, cmd):
        "Get command output or stderr if it fails"
        output = ""
        try:
            pdebug("gitinfo: running '%s'" % (" ".join(cmd)))
            child = Popen(cmd, stdout=PIPE,stderr=PIPE)
            output = child.communicate()
            pdebug("gitinfo output: %s" % (output[0]))
            pdebug("gitinfo error: %s" % (output[1].strip()))
            pdebug("gitinfo returncode:" + str(child.returncode))
            if child.returncode != 0:
                print("Warning: '%s' failed: %s" % (" ".join(cmd), output[1].strip()))
                return "Git error: " + output[1].strip()
        except OSError(e):
            print("Warning: '%s' failed: %s" % (" ".join(cmd), str(e)))
            return "Git error: " + str(e)
        text = output[0]
        text = text.decode()
        return text.lstrip().rstrip()

    def _cmd_out_ok(self, cmd_out, error):
        """
        See if the commad output contains an error string.
        If no, return true
        If yes, append the string to the error message, and return false.
        
        error may be modified by this function
        """
        
        pdebug('cmd_out: ' + cmd_out)
        if 'Git error:' in cmd_out:
            if len(error) > 0:
                error.append('; ')
            # append the cmd error message
            error.append(cmd_out)
            return False
        
        return True
    
    def _git_info(self):
        """
        Return a dictionary with entries keyed to git revision and repository information.
        
        The following keys will be populated. If the details are not avaiable,
        the value will be "unknown" (except for giterror)
        
        REPO_TAG       = The most recent tag available on the branch. In keeping with 
                         git tagging conventions, it is recomended that the tags on the master branch 
                         follow a dot release format, such as V3.2 or V10.2.a, etc.
        REPO_COMMITS   = Number of commits on this branch since the last tag.
        REPO_REVISION  = REPO_TAG-REPO_COMMITS. Intended to be a friendly, incrementing revision number, 
                         useful for identifying releases.
        REPO_BRANCH    = The branch we are using.
        REPO_EXTERNALS = 'unknown' (future additions may include a list of externals, or perhaps
                         the full GitInfo for all submodules.
        REPO_DATE      = Date of the last commit on this branch.
        REPO_URL       = URL of the origin.
        REPO_WORKDIR   = Working directory of your checked out branch.
        REPO_HASH      = Hash identifier of the last commit on this branch. The unequivocal way to 
                         identify the exact source revision.
        REPO_ERROR     = Error messages encountered while building GitInfo.
        REPO_DIRTY     = List of modified or unknown files in this repo.
        """
        
        objname      = None
        error        = []

        # Use the collected git details to populate the dicitionary items
        gitrevision     = None
        gitexternalrevs = None
        gitdate         = None
        giturl          = None
        gitworkdir      = None
        giterror        = None
        gittag          = None
        gitcommits      = None
        githash         = None
        gitbranch       = None
        
        # Run git describe, and extract the tag, number of commits, and
        # object name.  Extract the hyphenated fields from right to left,
        # in case the tag portion itself contains hyphens. --long ensures
        # that the commits and objname fields are always output, even if
        # the current commit exactly matches a tag.
        cmd_out = self._get_output([self.gitcmd, 'describe', '--long',
                                    '--match', self.match])
        if self._cmd_out_ok(cmd_out, error):
            describe = cmd_out.split('-')
            gittag = '-'.join(describe[0:-2])
            gitcommits = describe[-2]
            objname = describe[-1]

        # Run git config to fetch the URL
        cmd_out = self._get_output([self.gitcmd, 'config', '--get',
                                    'remote.origin.url'])
        if self._cmd_out_ok(cmd_out, error):
            # Normalize URL.
            giturl = cmd_out.replace('\\', '/').strip()

        # Run git log to fetch the date and hash of the last commit
        cmd_out = self._get_output([self.gitcmd, 'log',
                                    '--pretty=format:%cd,%H', '-1'])
        if self._cmd_out_ok(cmd_out, error):
            gitdate, githash = cmd_out.split(',')

        # Run git rev-parse to fetch the top level working directory
        cmd_out = self._get_output([self.gitcmd, 'rev-parse', '--show-toplevel'])
        if self._cmd_out_ok(cmd_out, error):
            # Normalize path.
            gitworkdir = cmd_out.replace('\\', '/').strip()
        
        # Run git rev-parse to fetch the branch
        cmd_out = self._get_output([self.gitcmd, 'rev-parse',
                                    '--abbrev-ref', 'HEAD'])
        if self._cmd_out_ok(cmd_out, error):
            gitbranch = cmd_out.strip()
        
        gitdirty = None
        cmd_out = self._get_output([self.gitcmd, 'status', '--porcelain'])
        if self._cmd_out_ok(cmd_out, error):
            gitdirty = ",".join(cmd_out.splitlines())

        # Derive the revision string which describes the state of the
        # current checkout.  If the current commit exactly matches a tag,
        # then leave off the -0.  If the checkout is not clean, add the
        # 'M' modifier.
        if gittag and gitcommits == '0':
            gitrevision = gittag
        elif gittag and gitcommits:
            gitrevision = gittag + "-" + gitcommits
        if gitrevision and gitdirty:
            gitrevision += "M"

        # populate the dictionary
        git_dict = {}
        git_dict['REPO_REVISION']     = gitrevision or 'unknown'
        git_dict['REPO_EXTERNALS']    = gitexternalrevs or 'unknown'
        git_dict['REPO_DATE']         = gitdate or 'unknown'
        git_dict['REPO_URL']          = giturl or 'unknown'
        git_dict['REPO_WORKDIR']      = gitworkdir or 'unknown'
        git_dict['REPO_ERROR']        = (error and str(error)) or ''
        git_dict['REPO_TAG']          = gittag or 'unknown'
        git_dict['REPO_COMMITS']      = gitcommits or 'unknown'
        git_dict['REPO_HASH']         = githash or 'unknown'
        git_dict['REPO_BRANCH']       = gitbranch or 'unknown'
        git_dict['REPO_DIRTY']        = gitdirty or 'unknown'
        
        pdebug('GitInfo._git_info git_dict:')
        for k, v in git_dict.items():
            pdebug('   k,v:' + ' ' + k + ' ' + v)
       
        # return the dictionary
        return git_dict

    def getRepoInfo(self):
        """
        Determine the various revision attributes, and assign them to 
        self.values. 
        
        Return self
        """
        
        # Fill in the key variables from the git info dictionary, but only
        # if there is a value there.
        gitdict = self._git_info()
        
        pdebug('GitInfo.getRepoInfo self.values:')
        for k,v in self._variable_map.items():
            if gitdict[k]:
                self.values[k] = gitdict[k]
                pdebug('   k,v: ' + k + ' ' + self.values[k])

        return self

    def applyToEnv(self, env):
        "Apply the info values to the environment."

        for k,v in self.values.items():
            env[k] = v

    def generateHeader(self):
        """
        Create C text suitable for a header file, containing the revision attributes
        included as defines.
        
        The self.values dictionary provide the attributes.
        
        Return the text.
        """
        
        githeader = """
/* %(REPO_ERROR)s */
#ifndef GITINFOINC
#define GITINFOINC

#define REPO_REVISION  \"%(REPO_REVISION)s\"
#define REPO_EXTERNALS \"%(REPO_EXTERNALS)s\"
#define REPO_DATE      \"%(REPO_DATE)s\"
#define REPO_WORKDIR   \"%(REPO_WORKDIR)s\"
#define REPO_URL       \"%(REPO_URL)s\"
#define REPO_HASH      \"%(REPO_HASH)s\"
#define REPO_COMMITS   \"%(REPO_COMMITS)s\"
#define REPO_TAG       \"%(REPO_TAG)s\"
#define REPO_BRANCH    \"%(REPO_BRANCH)s\"

#endif
"""
        githeader = githeader % self.values
        pdebug(githeader)
        return githeader

#####################################################################
#
# Stand alone test of GitInfo
#
if __name__ == "__main__":

    env = {}
    gitinfo = GitInfo(env)
    gitinfo.getRepoInfo()
    gitinfo.applyToEnv(env)
    for k,v in env.items():
        print((k, v))
    headertxt = gitinfo.generateHeader()
    print('')
    print(headertxt)
    
        
else:
#####################################################################
# Assume we are in the scons environment

    from SCons.Builder import Builder
    from SCons.Action import Action
    from SCons.Node import FS
    from SCons.Node.Python import Value
    import SCons.Warnings

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
        if type(source) == type(""):
            workdir = env.Dir(source)
        elif type(source) == type([]):
            workdir = source[0]
        if workdir.isfile():
            workdir = workdir.get_dir()
        if workdir.name in ['.git', '_git']:
            workdir = workdir.get_dir()
        pdebug("get_workdir(%s) ==> %s" % (str(source[0]), workdir.get_abspath()))
        return workdir.get_abspath()
    
    # A dictionary used to cache a GitInfo instance for a given working directory.
    _gitinfomap = {}
    
    def _load_gitinfo(env, workdir):
        """
        Return an instance of GitInfo for the specified directory.
        
        Cache the results in the _gitinfomap dictionary.
        """
        global _gitinfomap
        if workdir in _gitinfomap:
            # Result already cached for this workdir
            pdebug("_load_gitinfo: returning cached gitinfo for %s" % (workdir))
            return _gitinfomap[workdir]
        
        # Create a new GitInfo instance, for this workdir
        pdebug("_load_gitinfo(%s): creating gitinfo" % (workdir))
        ginfo = GitInfo(env)
        _gitinfomap[workdir] = ginfo.getRepoInfo()
        
        return ginfo
    
    
    def gitinfo_emitter_value(target, source, env):
        """Given an argument for git info in the first source, replace that
        source with a Value() node with the git info contents."""
        workdir = _get_workdir(env, source)
        gitinfo = _load_gitinfo(env, workdir)
        # If the git info command fails with an error, we don't
        # update the target it if exists.  Have to mark the
        # target as Precious so that scons doesn't delete it 
        # before the check for existence in the action.
        # I suppose the correct thing to do if subversion fails
        # and the file exists, is to return a source Value
        # equal to the current contents of the target. Nah
        env.Precious(target)
        return target, [Value(gitinfo.generateHeader())]
    
    def gitinfo_do_update_target(target, source):
        # If a git error, don't overwrite existing file
        text = source[0].get_text_contents()
        return text.find("Git error:") < 0 or not os.path.exists(target[0].path)
    
    def gitinfo_action_print(target, source, env):
        if gitinfo_do_update_target(target,source):
            return "Generating %s" % target[0]
        else:
            return "Not updating %s" % target[0] + " due to git error"
    
    def gitinfo_build_value(env, target, source):
        "Build header based on contents in the source."
        if gitinfo_do_update_target(target, source):
            out = open(target[0].path, "w")
            text = source[0].get_text_contents()
            out.write(text)
            out.write("\n")
            out.close()
    
    gitinfobuilder = Builder(
        action = Action(gitinfo_build_value, gitinfo_action_print),
        source_factory = FS.default_fs.Entry,
        emitter = gitinfo_emitter_value)
    
    
    class GitInfoWarning(SCons.Warnings.Warning):
        pass
    
    def generate(env):
        """
        Add git info and version for the top directory to the environment, and
        provide a builder for generating a header file with the definitions.
        """
        # We need the most current git info at this point to add it to the
        # environment.  We cannot rely on a regular builder to generate the
        # information by running gitversion later, because by then it is too
        # late.  To cache the version info between runs and between
        # applications of the gitinfo tool, we use a single implicit builder
        # for a top-level header file.
    
        pdebug("gitinfo: generate()")
        env['BUILDERS']['GitInfo'] = gitinfobuilder
        env['GIT'] = "git"
        env['GITVERSION'] = "gitversion"
        # Use the default location for the subversion Windows installer.
        if env['PLATFORM'] == 'win32':
            gitbin=r'c:\Tools\git\bin'
            env.PrependENVPath('PATH', gitbin)
            # env['GIT'] = os.path.join(gitbin, "git")
            # env['GITVERSION'] = os.path.join(gitbin, "gitversion")
    
        env.AddMethod(LoadGitInfo, "LoadGitInfo")
        env.LoadGitInfo('#')
    
    
    def LoadGitInfo(env, source):
        workdir = _get_workdir(env, source)
        gitinfo = _load_gitinfo(env, workdir)
        gitinfo.applyToEnv(env)
    
    
    def exists(env):
        git = env.WhereIs('git')
        if not git:
            SCons.Warnings.warn(
                GitInfoWarning,
                "Could not find git program. gitinfo tool not available.")
            return False
        return True
