#! /bin/bash

# Used to test eol_scons changes against building a few projects.


scons="scons --site-dir=`realpath $(dirname $0)/..`"
config="--config=force"
projects=""
do_tests=0

while [ $# -gt 0 ]; do
    case "$1" in
        clean)
            scons="$scons -c"
            config=""
            ;;
        test)
            do_tests=1
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
    tests=""
    case $name in
        aspen)
            args="-C Aspen -D apidocs"
            dir="aspen"
            tests="diff-bufr utest"
            ;;
        nidas*)
            args="-C src -D"
            dir="nidas-master"
            tests="test"
            ;;
        aeros)
            args="-C source -D apidocs"
            dir="aeros"
            tests="datastore/tests/xtest"
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
    if [ $do_tests -ne 1 ]; then
        tests=""
    fi
    echo "Building in $dir..."
    (set -x
     export $vars
     cd $dir && $scons -j4 $args $tests) || exit 1
}


for p in $projects; do
    build_project $p
done
