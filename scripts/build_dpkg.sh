#!/bin/bash

sdir=$(dirname $0)
dir=$sdir/..
pushd $dir > /dev/null

repobase=/net/ftp/pub/archive/software/debian

usage() {
    echo "Usage ${0##*/} [-i repository ] [-I codename] [dest]
    -i: install packages with reprepro to the repository
    -I: install packages to $repobase/codename-<codename>
    dest: destination if not installing with reprepro, default is $PWD
    For example to put packages on EOL Ubuntu bionic repository:
    $0 -I bionic"
    exit 1
}

dest=$PWD

while [ $# -gt 0 ]; do
    case $1 in
    -i)
        [ $# -lt 1 ] && usage
        shift
        repo=$1
        ;;
    -I)
        [ $# -lt 1 ] && usage
        shift
        repo=$repobase/codename-$1
        ;;
    -h)
        usage
        ;;
    *)
        dest=$1
        [ -d $dest ] || mkdir -p $dest || exit 1
        ;;
    esac
    shift
done

pkg=eol-scons

gitdesc=$(git describe --match "v[0-9]*")     # v2.0-14-gabcdef123
gitdesc=${gitdesc%-*}       # v2.0-14
gitdesc=${gitdesc/#v}       # 2.0-14
gitdesc=${gitdesc/-/.}       # 2.0.14

tmpdir=$(mktemp -d /tmp/${0##*/}_XXXXXX)
trap "{ rm -rf $tmpdir; }" EXIT
pkgdir=$tmpdir/$pkg
mkdir -p $pkgdir

rsync --exclude=.git -a --no-perms --no-owner --chmod=g-w --no-owner DEBIAN $pkgdir

sed -ri "s/^Version:.*/Version: $gitdesc/" $pkgdir/DEBIAN/control

ddir=$pkgdir/usr/share/scons/site_scons/eol_scons
mkdir -p $ddir

rsync __init__.py $ddir
rsync --exclude=.git --exclude=.sconf_temp --exclude="*.pyc" \
    --exclude=__pycache__ \
    -a --no-perms --no-owner --chmod=g-w eol_scons $ddir

# cd $ddir
# python << EOD
# import compileall
# compileall.compile_dir("eol_scons", force=1)
# EOD

ddir=$pkgdir/usr/share/doc/eol-scons
mkdir -p $ddir

cp copyright $ddir

scripts/deb_changelog.sh | gzip -9 -c > $ddir/changelog.Debian.gz
# cp $ddir/changelog.Debian.gz /tmp

cat << EOD | gzip -9 -c > $ddir/changelog.gz
eol-scons Debian maintainer and upstream author are identical.
Therefore also see normal changelog file for Debian changes.
EOD

cd $pkgdir

chmod -R g-ws DEBIAN
chmod -R g-w .

cd ..
fakeroot dpkg-deb --build  $pkg

# dpkg-name: info: moved 'eol-scons.deb' to './eol-scons_2.0-56_all.deb'
newname=$(dpkg-name $pkg.deb | sed -r "s/^[^']+'[^']+' to '([^']+).*/\1/")
newname=${newname##*/}

lintian $newname

if [ -n "$repo" ]; then
    # allow group write
    umask 0002
    distconf=$repo/conf/distributions
    if [ -r $distconf ]; then
        codename=$(fgrep Codename: $distconf | cut -d : -f 2)
    fi

    if [ -z "$codename" ]; then
        echo "Cannot determine codename of repository at $repo"
        exit 1
    fi
    export GPG_TTY=$(tty)

    flock $repo sh -c "
        reprepro -V -b $repo remove $codename $pkg
        reprepro -V -b $repo deleteunreferenced
        reprepro -V -b $repo includedeb $codename $newname"
fi

popd > /dev/null

if [ -n "$dest" ]; then
    cp $tmpdir/$newname $dest && echo "$dest/$newname is ready"
fi
