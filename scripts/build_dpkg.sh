#!/bin/bash

key='<eol-prog@eol.ucar.edu>'

usage() {
    echo "Usage ${0##*/} [-s] [-i repository ] [dest]"
    echo "-s: sign the package files with $key"
    echo "-i: install them with reprepro to the repository"
    echo "dest: destination directory for the .deb file"
    exit 1
}
[ $# -lt 1 ] && usage

sign=false
while [ $# -gt 0 ]; do
    case $1 in
    -s)
        sign=true
        ;;
    -i)
        shift
        repo=$1
        ;;
    *)
        dest=$1
        [ -d $dest ] || mkdir -p $dest || exit 1
        ;;
    esac
    shift
done

pkg=eol-scons

sdir=$(dirname $0)
dir=$sdir/..

pushd $dir > /dev/null


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

ddir=$pkgdir/usr/share/scons/site_scons
mkdir -p $ddir

rsync --exclude=.git -a --no-perms --no-owner --chmod=g-w eol_scons $ddir

# cd $ddir
# python << EOD
# import compileall
# compileall.compile_dir("eol_scons", force=1)
# EOD

ddir=$pkgdir/usr/share/doc/eol-scons
mkdir -p $ddir

cp copyright $ddir

$sdir/deb_changelog.sh | gzip -9 -c > $ddir/changelog.Debian.gz
# cp $ddir/changelog.Debian.gz /tmp

cat << EOD | gzip -9 -c > $ddir/changelog.gz
eol-scons Debian maintainer and upstream author are identical.
Therefore see also normal changelog file for Debian changes.
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

$sign && fakeroot dpkg-sig --sign builder -k "$key" $newname

if [ -n "$repo" ]; then
    # allow group write
    umask 0002
    flock $repo reprepro -V -b $repo remove jessie $pkg
    flock $repo reprepro -V -b $repo includedeb jessie $newname
fi

popd > /dev/null

if [ -n "$dest" ]; then
    cp $tmpdir/$newname $dest && echo "$dest/$newname is ready"
fi
