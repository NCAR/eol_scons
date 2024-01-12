# -*- python -*-
"""
GitInfo collects versioning and other metadata from a git repository.

The git information is based on the most recent annotated git tag 
that can be reached through 'git describe'. This is combined
with the number of commits since that tag to create a distinct
revision number which can be traced to a particular git commit.

Remember: _The tag must be a git annotated tag_

The git describe uses a '--match [vV][0-9]*' argument for a
file-glob style match on possible tags, looking for one that
starts with 'v' or 'V', followed by a number, followed by anything.

Example variable assigments:

    env['REPO_TAG']       V3.2
    env['REPO_COMMITS']   26
    env['REPO_REVISION']  V3.2-26
    env['REPO_DATE']      Wed Dec 3 13:45:13 2014 -0700
    env['REPO_BRANCH']    develop
    env['REPO_WORKDIR']   /Users/martinc/git/aspen
    env['REPO_URL']       https://github.com/ncar/aspen.git
    env['REPO_HASH']      6badaf8a78527b248adcda4a88c0579dcb90198a

Example generated header file text:

    /*  */
    #ifndef GITINFOINC
    #define GITINFOINC

    #define REPO_REVISION  "V3.2-26"
    #define REPO_DATE      "Wed Dec 3 13:45:13 2014 -0700"
    #define REPO_WORKDIR   "/Users/martinc/git/aspen"
    #define REPO_URL       "https://github.com/ncar/aspen.git"
    #define REPO_HASH      "6badaf8a78527b248adcda4a88c0579dcb90198a"
    #define REPO_COMMITS   "26"
    #define REPO_TAG       "V3.2"
    #define REPO_BRANCH    "develop"

    #endif

Notes:
Git commands are used to extract the information.
"""

import re
import subprocess as sp
from pathlib import Path

# Set to 1 to enable debugging output
_debug = 0

# Debugging print
def pdebug(msg):
    if _debug:
        print(msg)


class GitInfo:
    """
    Encapsulate the repository characteristics, making them available via a
    dictionary.
    
    Git commands used to extract the repository information:

    git describe --match [vV][0-9]*:

      Looks for a tag starting with 'v' or 'V' followed by a number followed
      by anything.  Returns string with up to three tokens: V3.2-4-g3189d8e.
      First token is the last matching tag on the branch.  Second token is the
      number of commits since the tag.  Third is the abbreviate object name of
      the last commit.  If the tag points to the most recent commit, then
      commit is '0'.
                  
    git config --get remote.origin.url:

      Get the repository URL that this branch was fetched from.
                  
    git log --pretty=format:"%cd,%H" -1: 

      Get the date and hash of the last commit in a form easily split.

      Wed Nov 26 16:42:30 2014 -0700,3189d8e443a6cf5827fc9617ebe8b95ab83d8eaf
    
    git rev-parse --show-toplevel: 

      Find the top of the working directory: /Users/martinc/git/aspen

    git status --porcelain:

      Get a list of any modified or unknown files in this checkout.  These are
      stored in the REPO_DIRTY key.  If this is not empty, then the git
      revision will have the suffix 'M'.

    The following keys are available. If the details are not avaiable, the
    value will be None.  Values of None are translated as 'unknown' in
    generated header files.

    REPO_TAG -
        The most recent tag available on the branch. In keeping with git
        tagging conventions, it is recomended that the tags on the master
        branch follow a dot release format, such as V3.2 or V10.2.a, etc.

    REPO_COMMITS -
        Number of commits on this branch since the last tag.

    REPO_REVISION -
        REPO_TAG-REPO_COMMITS. Intended to be a friendly, incrementing
        revision number, useful for identifying releases.

    REPO_BRANCH -
        The branch currently checked out.

    REPO_EXTERNALS -
        Unused.  Future additions may include a list of externals, or perhaps
        the full GitInfo for all submodules.

    REPO_DATE -
        Date of the last commit on this branch.

    REPO_URL -
        URL of the origin.

    REPO_WORKDIR -
        Absolute path to the top directory of the repository.  This is not
        written to generated files by default.

    REPO_HASH -
        Hash identifier of the last commit on this branch. The unequivocal way
        to identify the exact source revision.

    REPO_DIRTY -
        List of modified or unknown files in this repo.

    REPO_ERROR -
        Error output from any git command that fails.  Empty string if there
        are no errors, None if never set (ie, unknown).
    """

    gitcmd: str
    match: str
    repopath: Path or None
    header: Path or None

    def __init__(self, env=None, repopath=None):
        """
        Initialize a GitInfo object.  env is a dictionary which is checked for
        default values for the git path (GIT) and the regular expression to
        match against annotated tag versions (GIT_DESCRIBE_MATCH).  repopath
        is None until repo info is loaded from a working directory, with
        either getRepoInfo() or loadFromHeader().  Basically repopath is where
        the git commands are run or the header exists, so it effectively is
        the path to the git repo to be queried.  The default is the repo at
        the current working directory.
        """
        # Specify the git command
        if env is None:
            env = {}
        self.gitcmd = env.get('GIT', 'git')
        self.match = env.get('GIT_DESCRIBE_MATCH', '[vV][0-9]*')
        self.repopath = repopath
        # If loaded from a header file, this is the path to that file.
        self.header = None

        # Initialize the repo values.
        self.values = {
            'REPO_REVISION': None,
            'REPO_DATE': None,
            'REPO_URL': None,
            'REPO_WORKDIR': None,
            'REPO_TAG': None,
            'REPO_COMMITS': None,
            'REPO_HASH': None,
            'REPO_BRANCH': None,
            'REPO_DIRTY': None,
            'REPO_ERROR': None
        }

    def _get_output(self, cmd):
        "Get command output or stderr if it fails"
        output = ()
        try:
            pdebug("gitinfo: running '%s'" % (" ".join(cmd)))
            child = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE,
                             cwd=self.repopath)
            output = child.communicate()
            sout = output[0].decode().strip()
            eout = output[1].decode().strip()
            pdebug("gitinfo output: %s" % (sout))
            pdebug("gitinfo error: %s" % (eout))
            pdebug("gitinfo returncode:" + str(child.returncode))
            if child.returncode != 0:
                print("Warning: '%s' failed: %s" % (" ".join(cmd), eout))
                return "Git error: " + eout
        except OSError as e:
            print("Warning: '%s' failed: %s" % (" ".join(cmd), str(e)))
            return "Git error: " + str(e)
        return sout

    def _cmd_out_ok(self, cmd_out, error):
        """
        See if the commad output contains an error string.
        If no, return true
        If yes, append the string to the error message, and return false.

        error may be modified by this function
        """
        pdebug('cmd_out: ' + cmd_out)
        if 'Git error:' in cmd_out:
            # append the cmd error message
            error.append(cmd_out)
            return False
        return True

    def _git_info(self):
        """
        Return a dictionary of repository information.
        """
        error = []

        # Use the collected git details to populate the dicitionary items
        gitrevision     = None
        gitdate         = None
        giturl          = None
        gitworkdir      = None
        gittag          = None
        gitcommits      = None
        githash         = None
        gitbranch       = None
        gitdirty        = None

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
            # objname = describe[-1]

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

        # Derive the revision string which describes the state of the current
        # checkout.  If the current commit exactly matches a tag, then leave
        # off the -0.  If the checkout is not clean, add the 'M' modifier.
        gitrevision = gittag
        if gittag and gitcommits != '0':
            gitrevision = gittag + "-" + gitcommits
        if gitrevision and gitdirty:
            gitrevision += "M"

        git_dict = {
            'REPO_REVISION': gitrevision,
            'REPO_DATE': gitdate,
            'REPO_URL': giturl,
            'REPO_WORKDIR': gitworkdir,
            'REPO_ERROR': str(error) if error else '',
            'REPO_TAG': gittag,
            'REPO_COMMITS': gitcommits,
            'REPO_HASH': githash,
            'REPO_BRANCH': gitbranch,
            'REPO_DIRTY': gitdirty
        }
        return git_dict

    def _set_values(self, gitdict):
        pdebug('GitInfo._set_values:')
        for k in self.values.keys():
            if gitdict.get(k) is not None:
                self.values[k] = gitdict[k]
                pdebug('   k,v: ' + k + ' ' + self.values[k])

    def getRepoInfo(self, repopath=None):
        """
        Determine the various revision attributes for the directory at
        repopath, and assign them to self.values.  If repopath is None, use
        the repopath set when this GitInfo was initialized.

        Return self
        """
        if repopath is not None:
            self.repopath = repopath
        # Fill in the key variables from the git info dictionary, but only
        # if there is a value there that is not None.
        gitdict = self._git_info()
        self._set_values(gitdict)
        return self

    def applyToEnv(self, env):
        "Apply the info values to the environment."
        for k,v in self.values.items():
            env[k] = v

    def loadFromHeader(self, path):
        """
        Given the path to a generated header file, parse the repo info from
        the file instead of calling git tools.
        """
        self.header = Path(path)
        self.repopath = Path(path).parent
        lines = []
        gitdict = {}
        msg = ''
        try:
            with open(path) as fin:
                lines = fin.readlines()
        except Exception as ex:
            msg = ("Could not load repo info from header %s: %s" %
                   (path, str(ex)))
        gitdict['REPO_ERROR'] = msg
        rxp = re.compile(r"^#define\s+(?P<key>REPO_[a-zA-Z_0-9]+)"
                         r"\s+\"(?P<value>.+)\"$")
        for line in lines:
            rx = rxp.match(line)
            if not rx:
                continue
            value = rx.group('value')
            value = None if value in ['unknown', 'None'] else value
            gitdict[rx.group('key')] = value
        self._set_values(gitdict)

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
#define REPO_DATE      \"%(REPO_DATE)s\"
#define REPO_URL       \"%(REPO_URL)s\"
#define REPO_HASH      \"%(REPO_HASH)s\"
#define REPO_COMMITS   \"%(REPO_COMMITS)s\"
#define REPO_TAG       \"%(REPO_TAG)s\"
#define REPO_BRANCH    \"%(REPO_BRANCH)s\"
#define REPO_DIRTY     \"%(REPO_DIRTY)s\"

#endif
"""
        repl = {k:("unknown" if v is None else v)
                for k, v in self.values.items()}
        githeader = githeader % repl
        pdebug(githeader)
        return githeader

    def dump(self):
        for k, v in self.values.items():
            v = v if v is not None else 'unknown'
            print('%s="%s"' % (k, v))


def main():
    import sys
    repopath = None
    if len(sys.argv) > 1:
        repopath = Path(sys.argv[1])
    gitinfo = GitInfo()
    if repopath and repopath.is_file():
        gitinfo.loadFromHeader(repopath)
    else:
        gitinfo.getRepoInfo(repopath)
    gitinfo.dump()
    headertxt = gitinfo.generateHeader()
    print("\n%s" % (headertxt))


#####################################################################
#
# Stand alone test of GitInfo
#
if __name__ == "__main__":
    main()
