#!/bin/sh

svnurl=http://svn.eol.ucar.edu/svn/eol/common/trunk/site_scons

# For testing outside of jenkins
if ! [ $JENKINS_HOME ]; then

    repo=eol_scons

    JENKINS_HOME=/tmp/${repo}_jenkins
    [ -d $JENKINS_HOME ] || mkdir $JENKINS_HOME
    cd $JENKINS_HOME

    giturl=https://github.com/ncar/${repo}.git

    # emulate how jenkins sets up the working tree
    # jenkins works in a "detached head" state, with no current
    # branch, doing a checkout on a specific commit

    git rev-parse --is-inside-work-tree || git init
    git config remote.origin.url $giturl
    git -c core.askpass=true fetch --tags --progress $giturl '+refs/heads/*:refs/remotes/origin/*'

    GIT_COMMIT=$(git rev-parse origin/master^{commit})
    git checkout -f $GIT_COMMIT

fi

git status

# setup svn-remote configuration
if ! git config --get-regexp svn-remote.svn > /dev/null; then
    git config svn-remote.svn.url $svnurl
    git config svn-remote.svn.fetch ":refs/remotes/git-svn"
fi

# fetch from svn-remote named "svn"
# takes a long time the first time it is run from a large repo
git svn fetch svn 

# create svn branch if it doesn't exist, tracking git-svn remote
# must be done after above git svn fetch
git show-ref --verify --quiet refs/heads/svn || git branch svn git-svn

# create new tmp-master branch pointing at latest commit
git show-ref --verify --quiet refs/heads/tmp-master && git branch -D tmp-master
git branch tmp-master $GIT_COMMIT
git checkout tmp-master

# rebase tmp-master so it becomes a series of commits after HEAD of svn
# takes a long time the first time it is run on a large repo
git rebase svn

# fast-forward merge the new commits to the svn branch
git checkout svn
git merge --ff-only tmp-master

# push new commits to subversion
git svn dcommit

# reset working tree, quietly, to suppress the "detached head" warning
git checkout -f -q $GIT_COMMIT

# delete temporary branch
git branch -D tmp-master

git status

