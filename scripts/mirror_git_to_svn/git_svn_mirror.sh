#!/bin/sh

svnurl=http://svn.eol.ucar.edu/svn/eol/common/trunk/site_scons

if ! [ -f .git/config ] || ! grep -F -q svn-remote .git/config; then
    cat << EOD >> .git/config
[svn-remote "svn"]
    url = $svnurl
    fetch = :refs/remotes/git-svn
EOD
fi

# fetch from above svn-remote named "svn"
# takes a long time the first time it is run from a large repo
git svn fetch svn 

# create master branch if needed
git show-ref --verify --quiet refs/heads/master || git branch master origin/master

# create svn branch if it doesn't exist, tracking git-svn remote
# must be done after above git svn fetch
git show-ref --verify --quiet refs/heads/svn || git branch svn git-svn

# master becomes a series of commits after HEAD of svn
# takes a long time the first time it is run on a large repo
git rebase svn master

git checkout svn

# fast-forward merge the new commits on master to svn
git merge --ff-only master

# push new commits to subversion
git svn dcommit

# set master back to origin/master
git rebase origin/master master

