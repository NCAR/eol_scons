#!/bin/bash

script=$(basename $0)

# --- global variables ---
# specfile must be specified, then pkg name is extracted from it.
specfile=
pkgname=
# releasenum defaults to 1
releasenum=1
tag=
version=
arch=
srpm=
rpms=
snapshot_specfile=

# temporary directory to clone source and create archive.  we want it to be
# local rather than in /tmp so git can optimize the clone with hard
# links.
builddir=build/build_rpm.$$

set -o pipefail

topdir=${TOPDIR:-$(rpmbuild --eval %_topdir)_$(hostname)}
sourcedir=$(rpm --define "_topdir $topdir" --eval %_sourcedir)
[ -d $sourcedir ] || mkdir -p $sourcedir


get_pkgname_from_spec() # specfile
{
    specfile="$1"
    pkgname=`rpmspec --define "releasenum $releasenum" --srpm -q --queryformat "%{NAME}\n" "$specfile"`
}


# set version and tag from the spec file
get_version_and_tag_from_spec() # specfile
{
    specfile="$1"
    version=`rpmspec --define "releasenum $releasenum" --srpm -q --queryformat "%{VERSION}\n" "$specfile"`
    tag="v${version}"
    tag=`echo "$tag" | sed -e 's/~/-/'`
    # If this is a snapshot version with an embedded commit, extract the
    # commit hash as the tag.
    if echo "$tag" | grep -q snapshot ; then
        tag=`echo "$tag" | sed -e 's/.*\.snapshot\.//'`
        echo "Snapshot tag: $tag"
    fi
}


# get the version and tag from the source instead of the spec file
get_version_and_tag_from_git()
{
    eval `scons ./gitdump | grep REPO_`

    # REPO_TAG is the most recent tagged version, so that's what the package is
    # built from.
    if [ "$REPO_TAG" == "unknown" ]; then
        echo "No latest version tag found."
        exit 1
    fi
    tag="$REPO_TAG"
    version=${tag/#v}
}


get_releasenum() # version
{
    version="$1"
    # The release number enumerates different packages built from the same
    # version version of the source.  On each new source version, the release
    # num restarts at 1.  The repo is the definitive source for the latest
    # release num for each version.
    local eolreponame
    get_eolreponame
    url="https://archive.eol.ucar.edu/software/rpms/${eolreponame}-signed"
    url="$url/\$releasever/\$basearch"
    yum="yum --refresh --repofrompath eol-temp,$url --repo=eol-temp"
    # yum on centos7 does not support --refresh or --repofrompath, so for now
    # resort to relying on the eol repo to be already defined, and explicitly
    # update the cache for it...
    yum="yum --disablerepo=* --enablerepo=eol-signed"
    $yum makecache
    entry=`$yum list $pkgname egrep $pkgname | tail -1`
    echo "$entry"
    release=`echo "$entry" | awk '{ print $2; }'`
    repoversion=`echo "$release" | sed -e 's/-.*//'`
    if [ "$repoversion" != "$version" ]; then
        echo "Version $version looks new, restarting at releasenum 1."
        releasenum=1
    elif [ -n "$release" ]; then
        releasenum=`echo "$release" | sed -e 's/.*-//' | sed -e 's/\..*$//'`
        releasenum=$((1+$releasenum))
    else
        echo "Could not determine current release number, cannot continue."
        exit 1
    fi
}


create_build_clone() # tag
{
    # Create a clean clone of the current repo in its own build directory.
    tag="$1"
    echo "Cloning source for tag: ${tag}..."
    # we want to copy the origin url in the cloned repository so it shows
    # up same as in the source repository.
    url=`git config --local --get remote.origin.url`
    git="git -c advice.detachedHead=false"
    if test -d .git ; then
        (set -x; rm -rf "$builddir"
        mkdir -p "$builddir"
        $git clone . "$builddir/$pkgname"
        cd "$builddir/$pkgname" && git remote set-url origin "$url")
    else
        echo "This needs to be run from the top of the repository."
        exit 1
    fi
    if [ -n "$tag" ]; then
        (set -x;
         cd "$builddir/$pkgname";
         $git checkout "$tag")
        if [ $? != 0 ]; then
            exit 1
        fi
    fi
    # Update version headers using the gitinfo alias.
    scons -C "$builddir/$pkgname" versionfiles
}


# get the full paths to the rpm files given the spec file and the release
# number.  sets variables rpms, srpm, and arch
get_rpms() # specfile releasenum
{
    local specfile="$1"
    local releasenum="$2"
    rpms=""
    if [ -z "$specfile" -o -z "$releasenum" ]; then
        echo "get_rpms {specfile} {releasenum}"
        exit 1
    fi
    # get the arch the spec file will build
    arch=`rpmspec --define "releasenum $releasenum" -q --srpm --queryformat="%{ARCH}\n" $specfile`

    srpm=`rpmspec --define "releasenum $releasenum" --srpm -q "${specfile}"`.src.rpm
    # not sure why rpmspec returns the srpm with the arch, even though srpm
    # actually built by rpmbuild does not have it.
    srpm="${srpm/.${arch}}"
    # SRPM ends up in topdir/SRPMS/$srpmfile
    # RPMs end up in topdir/RPMS/<arch>/$rpmfile
    srpm="$topdir/SRPMS/$srpm"
    rpms=`rpmspec --define "releasenum $releasenum" -q "${specfile}" | while read rpmf; do echo "$topdir/RPMS/$arch/${rpmf}.rpm" ; done`
}


# set eolreponame to fedora or epel according to the current dist
get_eolreponame()
{
    case `rpm -E %{dist}` in

        *fc*) eolreponame=fedora ;;
        *el*) eolreponame=epel ;;
        *) eolreponame=epel ;;

    esac
}


clean_rpms() # rpms
{
    echo "Removing expected RPMS:"
    for rpmfile in ${rpms}; do
        (set -x ; rm -f "$rpmfile")
    done
}


run_rpmbuild()
{
    get_pkgname_from_spec "$specfile"

    # get the version to package from the spec file
    get_version_and_tag_from_spec "$specfile"

    create_build_clone "$tag"

    get_releasenum "$version"

    get_rpms "$specfile" "$releasenum"

    clean_rpms "$rpms"

    # now we can build the source archive and the package...
    cat <<EOF
Building ${pkgname} version ${version}, release ${releasenum}, arch: ${arch}.
EOF

    (cd "$builddir" && tar czf $sourcedir/${pkgname}-${version}.tar.gz \
        --exclude .svn --exclude .git $pkgname) || exit $?

    rpmbuild -v -ba \
        --define "_topdir $topdir"  \
        --define "releasenum $releasenum" \
        --define "debug_package %{nil}" \
        $specfile || exit $?

    cat /dev/null > rpms.txt
    for rpmfile in $srpm $rpms ; do
        if [ -f "$rpmfile" ]; then
            echo "RPM: $rpmfile"
            echo "$rpmfile" >> rpms.txt
        else
            echo "Missing RPM: $rpmfile"
            exit 1
        fi
    done
}


# Given a spec file, copy it and bump it to build the latest commit, whether
# tagged or not.  Use a special encoding for the version based on git
# describe.  It would have been nice if there was a spec tag for setting a VCS
# commit identifier separately from the version, but I didn't find it.
create_snapshot_specfile() # specfile [commit]
{
    specfile="$1"
    commit="$2"
    if [ -z "$commit" ]; then
        commit=`git rev-parse --short=8 HEAD`
    fi
    # get just the most recent annotated tag on this branch
    tag=`git describe --abbrev=0 "$commit"`
    # Use full git describe to get a snapshot version.  The version cannot
    # contain hyphens.
    describe=`git describe --long --abbrev=8 "$commit"`
    # convert v2.0-alpha2-3-g9d6ff521 to 2.0.alpha2.3.snapshot.9d6ff521
    version=`echo "$describe" | sed -e 's/^v//' -e 's/-g/-snapshot-/'`
    version=`echo "$version" | sed -e 's/-/./g'`
    mkdir -p build
    snapshot_specfile=build/`basename "${specfile}" .spec`-"${commit}.spec"
    cp -fp "$specfile" "$snapshot_specfile"
    rpmdev-bumpspec -c "build snapshot $describe based on $tag" \
        -n "$version" "$snapshot_specfile"
    echo "Created snapshot ${snapshot_specfile}, version ${version}."
}


usage()
{
    cat <<EOF
Usage: ${script} {specfile} {op} [args]
ops:
  pkgname -
    Print the package name in the spec file.
  releasenum {version} -
    Print next release number for given package version.
  version -
    Print the version tag extracted from the spec file.
  clone -
    Clone the source tree and checkout the version from the
    spec file.
  build -
    Build RPMs for the given spec file.
  snapshot_specfile -
    Create a new specfile bumped to a snapshot version for the
    current source repo.
  snapshot -
    Create the snapshot specfile and build RPMs with it.
EOF
}

case "$1" in

    -h|--help|help)
        usage
        exit 0
        ;;

esac

specfile="$1"
if [ -z "$specfile" ]; then
    usage
    exit 1
fi
shift

if [ ! -f "$specfile" ]; then
    echo "spec file not found: $specfile"
    exit 1
fi

op="$1"
if [ -z "$op" ]; then
    op=build
else
    shift
fi

case "$op" in

    pkgname)
        get_pkgname_from_spec "$specfile"
        echo Package name: $pkgname
        ;;

    releasenum)
        if [ -z "$1" ]; then
            echo "Usage: $script {specfile} releasenum {version}"
            exit 1
        fi
        get_pkgname_from_spec "$specfile"
        get_releasenum "$@"
        echo Next releasenum: "$releasenum"
        ;;

    version)
        get_version_and_tag_from_spec "$specfile"
        echo $tag
        ;;

    rpms)
        get_rpms "$specfile" "$releasenum"
        for rpmfile in $srpm $rpms ; do
            echo "$rpmfile"
        done
        ;;

    clone)
        get_pkgname_from_spec "$specfile"
        create_build_clone "$@"
        ;;

    build)
        run_rpmbuild
        ;;

    snapshot_specfile)
        create_snapshot_specfile "$specfile" "$@"
        ;;

    snapshot)
        create_snapshot_specfile "$specfile" "$@"
        specfile="$snapshot_specfile"
        run_rpmbuild
        ;;

    help)
        usage
        exit 0
        ;;

    *)
        echo "unknown operation: $op"
        usage
        exit 1
        ;;

esac
