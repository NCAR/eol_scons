#! /bin/bash

# Used to test eol_scons changes against building a few projects.


scons="scons --site-dir=`realpath $(dirname $0)/..`"
config="--config=force"
projects=""

while [ $# -gt 0 ]; do
    case "$1" in
        clean)
            scons="$scons -c"
            config=""
            ;;
        *)
            projects="$projects $1"
            ;;
    esac
    shift
done

if [ -z "$projects" ]; then
    projects="nidas aeros aspen nc_compare acTrack2kml"
fi

build_project() # name
{
    name=$1
    args=""
    # Allow this to be overridden since it interferes with aeros datastore
    # test.
    vars="PYTHONWARNINGS=default PYTHONTRACEMALLOC=10"
    vars="PYTHONWARNINGS=default"
    dir=""
    case $name in
        aspen)
            args="-C Aspen -D apidocs diff-bufr utest"
            dir="aspen"
            ;;
        nidas*)
            args="-C src -D test"
            dir="nidas-master"
            ;;
        aeros)
            args="-C source -D apidocs datastore/tests/xtest"
            dir="aeros"
            ;;
        *nc_compare)
            args="-f SConscript ."
            dir="aircraft_nc_utils/nc_compare"
            ;;
        *acTrack2kml)
            args=""
            dir="kml_tools/acTrack2kml"
            ;;
        *)
            echo "Unknown project: $name"
            exit 1
            ;;
    esac
    dir=$HOME/code/$dir
    echo "Building in $dir..."
    (set -x
     export $vars
     cd $dir && $scons -j4 $args) || exit 1
}


for p in $projects; do
    build_project $p
done
