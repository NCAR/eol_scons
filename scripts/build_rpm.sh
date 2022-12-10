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
# standard name for package source archives is pkgname-version
tarname=
arch=
# rpms is the array of rpm filenames which will be created.  the first rpm is
# always the source rpm.
declare -a rpms
rpms=()
snapshot_specfile=

# temporary directory to clone source and create archive.  we want it to be
# local rather than in /tmp so git can optimize the clone with hard
# links.
builddir=build

set -o pipefail

topdir=${TOPDIR:-$(rpmbuild --eval %_topdir)_$(hostname)}
sourcedir=$(rpm --define "_topdir $topdir" --eval %_sourcedir)
[ -d $sourcedir ] || mkdir -p $sourcedir


get_pkgname_from_spec() # specfile
{
    specfile="$1"
    pkgname=`rpmspec --define "releasenum $releasenum" --srpm -q --queryformat "%{name}\n" "$specfile"`
}


# set version and tag from the spec file
get_version_and_tag_from_spec() # specfile
{
    specfile="$1"
    version=`rpmspec --define "releasenum $releasenum" --srpm -q --queryformat "%{version}\n" "$specfile"`
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


# set tarname from pkgname and version
set_tarname()
{
    tarname="${pkgname}${version:+-$version}"
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


setup_tar_source() # source-directory
{
    # Clean the build source.  This is only useful for copies, but it doesn't
    # hurt in clones.  A 'git clean -x -d -f' might be thorough and effective,
    # but that would remove any files in a copy which were needed but not yet
    # added to git, so be a little more conservative than that.
    (cd "$builddir/$tarname" && scons -c .)
    # Update version headers using the gitinfo alias.
    scons -C "$builddir/$tarname" versionfiles
    # Remove scons artifacts
    (cd "$builddir/$tarname"
     rm -rf .sconsign.dblite .sconf_temp config.log)
}


create_build_clone() # tag
{
    set_tarname
    # Create a clean clone of the current repo in its own build directory,
    # including generating any version-dependent files.  The result is meant
    # to be suitable for a source archive.
    tag="$1"
    echo "Cloning source for tag: ${tag}..."
    # we want to copy the origin url in the cloned repository so it shows
    # up same as in the source repository.
    url=`git config --local --get remote.origin.url`
    git="git -c advice.detachedHead=false"
    if test -d .git ; then
        (set -x; rm -rf "$builddir/$tarname"
        mkdir -p "$builddir/$tarname"
        $git clone . "$builddir/$tarname"
        cd "$builddir/$tarname" && git remote set-url origin "$url")
    else
        echo "This needs to be run from the top of the repository."
        exit 1
    fi
    if [ -n "$tag" ]; then
        (set -x;
         cd "$builddir/$tarname";
         $git checkout "$tag")
        if [ $? != 0 ]; then
            exit 1
        fi
    fi
    setup_tar_source "$builddir/$tarname"
}


create_build_copy()
{
    # Like create_build_clone, but copy the current source instead of cloning
    # it.  This is meant only for testing the packaging, it should not be used
    # to create packages for release, since nothing verifies the source is
    # clean.  This uses rsync to copy the directory tree where the files are
    # hard links back to the source, so it's fast and saves space.  The
    # subsequent clean in the build tree only removes the hard links and does
    # not affect the source.
    set_tarname
    echo "Copying source with hard links..."
    if test -d .git ; then
        (set -x; rm -rf "$builddir/$tarname"
        mkdir -p "$builddir/$tarname"
        rsync -av --link-dest="$PWD" --exclude build ./ "$builddir/$tarname")
    else
        echo "This needs to be run from the top of the repository."
        exit 1
    fi
    setup_tar_source "$builddir/$tarname"
}


# get the full paths to the rpm files given the spec file and the release
# number.  sets variables rpms, srpm, and arch
get_rpms() # specfile releasenum
{
    local specfile="$1"
    local releasenum="$2"
    rpms=()
    if [ -z "$specfile" -o -z "$releasenum" ]; then
        echo "get_rpms {specfile} {releasenum}"
        exit 1
    fi
    # Get the arch the spec file will build. Technically this command queries
    # for the single srpm but returns a format which is the default for arch
    # for the packages in this spec.  It might also work to just use the
    # `arch` command, but I'm not sure if that's always equivalent.
    arch=`rpmspec --define "releasenum $releasenum" -q --srpm --queryformat="%{arch}\n" $specfile`

    # The package names from rpmspec -q are inconsistent (ie sometimes wrong)
    # across OS releases, so specify the package name format explicitly.
    qfsrpm="%{name}-%{version}-%{release}.src.rpm"
    qfrpm="%{name}-%{version}-%{release}.%{arch}.rpm"

    srpm=`rpmspec --define "releasenum $releasenum" --srpm -q --queryformat="${qfsrpm}\n" "${specfile}"`
    # SRPM ends up in topdir/SRPMS/$srpmfile
    # RPMs end up in topdir/RPMS/<arch>/$rpmfile
    srpm="$topdir/SRPMS/$srpm"
    # This puts all the built rpms except for src in the same architecture
    # subdirectory, even if some packages are noarch.  I don't think this has
    # made a difference in practice.  This could be fixed by making the arch
    # directory part of the package name in the query format.
    rpms=(`echo "$srpm" ; \
           rpmspec --define "releasenum $releasenum" -q --queryformat="${qfrpm}\n" "${specfile}" | \
           while read rpmf; do \
               echo "$topdir/RPMS/$arch/${rpmf}" ; \
           done`)
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
    for rpmfile in "$@" END; do
        [ "$rpmfile" == END ] && break
        (set -x ; rm -f "$rpmfile")
    done
}


# run the whole sequence to build an rpm: clone the source, archive it, and
# pass it to rpmbuild.  If copy specified, create a test package from a copy
# of the current source, instead of from a clean tag or commit.
run_rpmbuild() # [copy]
{
    archive="$1"
    get_pkgname_from_spec "$specfile"

    # get the version to package from the spec file
    get_version_and_tag_from_spec "$specfile"

    if [ "$archive" == "copy" ]; then
        create_build_copy
    else
        create_build_clone "$tag"
    fi

    get_releasenum "$version"

    get_rpms "$specfile" "$releasenum"

    clean_rpms "${rpms[@]}"

    # now we can build the source archive and the package...
    cat <<EOF
Building ${pkgname} version ${version}, release ${releasenum}, arch: ${arch}.
EOF

    (cd "$builddir" && tar czf $sourcedir/${tarname}.tar.gz \
        --exclude .svn --exclude .git --exclude config.log \
        --exclude .sconf_temp --exclude .sconsign.dblite \
        --exclude __pycache__ --exclude "*.pyc" \
        $tarname) || exit $?

    rpmbuild -v -ba \
        --define "_topdir $topdir"  \
        --define "releasenum $releasenum" \
        --define "debug_package %{nil}" \
        $specfile || exit $?

    cat /dev/null > rpms.txt
    for rpmfile in "${rpms[@]}" ; do
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
  test -
    Like snapshot, but build from a copy of the source rather
    than a clean commit.
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
        for rpmfile in ${rpms[@]} ; do
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

    test)
        create_snapshot_specfile "$specfile" "$@"
        specfile="$snapshot_specfile"
        run_rpmbuild copy
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
