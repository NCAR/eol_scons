#!/bin/sh

dir=$(dirname $0)
script=$(basename $0)

usage() {
    echo $script [-i] [pkg]
    echo "-i: install RPM on EOL yum repository (if accessible)"
    exit 1
}

doinstall=false

case $1 in
-i)
    doinstall=true
    shift
    ;;
esac

topdir=${TOPDIR:-$(rpmbuild --eval %_topdir)}

rroot=unknown
rf=repo_scripts/repo_funcs.sh
[ -f $rf ] || rf=/net/www/docs/software/rpms/scripts/repo_funcs.sh
if [ -f $rf ]; then
    source $rf
    rroot=`get_eol_repo_root`
else
    [ -d /net/www/docs/software/rpms ] && rroot=/net/www/docs/software/rpms
fi

cd $dir
cd ..
pwd

log=/tmp/$script.$$
trap "{ rm -f $log; }" EXIT

set -o pipefail

# Set RPM version and release from output of git describe.
# version is latest tag
# release is number of commits since tag
gitdesc=$(git describe)   # 2.0-14-gabcdef123
version=${gitdesc%%-*}   # 2.0

# check for dash
if [[ $version =~ .+-.+ ]]; then
    release=${gitdesc#*-}   # 14-gabcdef123
    release=${release%-*}   # 14
else
    release=0
fi

[ -d $topdir/SOURCES ] || mkdir -p $topdir/SOURCES

pkg=eol_scons

tar czf ${topdir}/SOURCES/${pkg}-${version}.tar.gz --exclude .svn --exclude ".git*" --exclude "*.swp" --exclude "*.py[oc]" --exclude __pycache__ --exclude .sconf_temp --exclude "*.o" ${pkg}

set -x
rpmbuild -ba --clean \
    --define "_topdir $topdir" --define "debug_package %{nil}" \
    --define "version $version" --define "release $release" \
    scripts/${pkg}.spec | tee -a $log  || exit $?


echo "RPMS:"
grep "^Wrote:" $log
rpms=`grep '^Wrote:' $log | grep /RPMS/ | awk '{print $2}'`

if $doinstall; then
    if [ -d $rroot ]; then
        echo "Moving rpms to $rroot"
        copy_rpms_to_eol_repo $rpms
    else
        echo "$rroot not found. Leaving RPMS in $topdir"
    fi
else
    echo "-i not specified, RPMs will not be installed in $rroot"
fi

