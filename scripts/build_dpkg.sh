#!/bin/bash

key='<eol-prog@eol.ucar.edu>'

usage() {
    echo "Usage ${0##*/} [-s] [-i repository ] dest"
    echo "dest is a destination directory for the .deb file"
    echo "-s: sign the package files with $key"
    echo "-i: install them with reprepro to the repository"
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
        ;;
    esac
    shift
done

[ -z "$dest" ] && usage

pkg=eol-scons

dir=$(dirname $0)/..
cd $dir

gitdesc=$(git describe --match "v[0-9]*")     # v2.0-14-gabcdef123
gitdesc=${gitdesc%-*}       # v2.0-14
gitdesc=${gitdesc/#v}       # 2.0-14

tmpdir=$(mktemp -d /tmp/${0##*/}_XXXXXX)
trap "{ rm -rf $tmpdir; }" EXIT
pkgdir=$tmpdir/$pkg
mkdir -p $pkgdir

rsync --exclude=.git -a DEBIAN $pkgdir

sed -ri "s/^Version:.*/Version: $gitdesc/" $pkgdir/DEBIAN/control

destdir=$pkgdir/usr/share/scons/site_scons
mkdir -p $destdir

rsync --exclude=.git -a eol_scons $destdir

cd $destdir

python << EOD
import compileall
compileall.compile_dir("eol_scons", force=1)
EOD

cd $pkgdir
chmod -R g-ws DEBIAN

cd ..
dpkg-deb -b  $pkg

# dpkg-name: info: moved 'eol-scons.deb' to './eol-scons_2.0-56_all.deb'
newname=$(dpkg-name $pkg.deb | sed -r "s/^[^']+'[^']+' to '([^']+).*/\1/")
newname=${newname##*/}

$sign && dpkg-sig --sign builder -d '<eol-prog@eol.ucar.edu>' $newname

cp $newname $dest

echo "$dest/$newname"

if [ -n "$repo" ]; then
    flock $repo reprepro -V -b $repo includedeb jessie $newname
fi




