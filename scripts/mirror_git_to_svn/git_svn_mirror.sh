#!/bin/sh

if ! [ $JENKINS_HOME ]; then
    set -x
    set -e
    cd /tmp


    if [ ! -d eol_scons ]; then
        git clone http://github.com/ncareol/eol_scons eol_scons
    fi

    cd eol_scons

fi

# url = file:///scr/tmp/maclean/svn_mirror/eol_svn_repo/common/trunk/site_scons
if ! [ -f .git/config ] || ! grep -F -q svn-remote .git/config; then
    cat << EOD >> .git/config
[svn-remote "svn"]
    url = http://svn.eol.ucar.edu/svn/eol/common/trunk/site_scons
    fetch = :refs/remotes/git-svn
EOD
fi

# takes a long time the first time it is run
git svn fetch svn 

# check if branch "svn" exists
git show-ref --verify --quiet refs/heads/svn || git branch svn git-svn
# git checkout svn

# get origin master, with original SHA1
git show-ref --verify --quiet refs/heads/tmp-master || git branch tmp-master origin/master
git checkout tmp-master
git pull origin master

# merge in new master, then rebase on to SVN
git checkout master
git pull origin master
git merge --ff-only tmp-master

# If original fetch is done on "-r HEAD" then this step
# takes a long time. No getting around it.
git rebase svn

git checkout svn
git merge --ff-only master

git svn dcommit

git checkout master
# rebase master back to original SHA1
git rebase tmp-master

git branch -D tmp-master
# git branch -D svn


