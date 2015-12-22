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

tmplog=$(mktemp /tmp/${script}_XXXXXX.log)
tmpspec=$(mktemp /tmp/${script}_XXXXXX.spec)
awkcom=$(mktemp /tmp/${script}_XXXXXX.awk)
trap "{ rm -f $tmplog $tmpspec $awkcom; }" EXIT

set -o pipefail

pkg=eol_scons

# Set RPM version and release from output of git describe,
# looking for tags starting with "v[0-9]".
# Assuming the latest tag is something like "v2.0", the
# output of git describe will be "v2.0-14-gabcdef123"
# Set the RPM version to the tag value after "v",
# and the RPM release to the number of commits since tag.
#
# This failed once and doing 'git pull --tags origin master' seemed
# solve it, even though --tags seems that it is the default in a pull.

gitdesc=$(git describe --match "v[0-9]*")     # v2.0-14-gabcdef123
gitdesc=${gitdesc%-*}       # v2.0-14
gitdesc=${gitdesc/#v}       # 2.0-14
version=${gitdesc%-*}      # 2.0

release=${gitdesc#*-}       # 14
[ $gitdesc == "$release" ] && release=0 # no dash

# In the RPM changelog, copy up to 100 recent commit
# subject lines since this tag.
sincetag=v2.0

cat << \EOD > $awkcom
/^[0-9a-f]+/ {
    hash = $0
    cmd = "git describe --match '[vV][0-9]*' " hash " 2>/dev/null"
    res = (cmd | getline version)
    close(cmd)
    if (res == 0) {
        version = ""
    }
}
/^\*/ { print $0,version }
/^-/ { print $0 }
/^$/ { print $0 }
EOD

# create change log from git log messages since $sincetag
# Put SHA hash by itself on first line. Above awk script then
# converts it to the output of git describe, and appends it to "*" line.
# Truncate subject line at 60 characters 
# git convention is that the subject line is supposed to be 50 or shorter
git log --max-count=100 --date-order --format="%h%n* %cd %aN%n- %s%n" --date=local ${sincetag}.. | sed -r 's/[0-9]+:[0-9]+:[0-9]+ //' | sed -r 's/(^- .{,60}).*/\1/' | awk -f $awkcom | cat scripts/${pkg}.spec - > $tmpspec

[ -d $topdir/SOURCES ] || mkdir -p $topdir/SOURCES

tar czf ${topdir}/SOURCES/${pkg}-${version}.tar.gz --exclude .svn --exclude ".git*" --exclude "*.swp" --exclude "*.py[oc]" --exclude __pycache__ --exclude .sconf_temp --exclude "*.o" ${pkg}

set -x
rpmbuild -ba --clean \
    --define "_topdir $topdir" --define "debug_package %{nil}" \
    --define "version $version" --define "release $release" \
    $tmpspec | tee -a $tmplog  || exit $?


echo "RPMS:"
grep "^Wrote:" $tmplog
rpms=`grep '^Wrote:' $tmplog | grep /RPMS/ | awk '{print $2}'`

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

