#!/bin/sh

set -ex

libtoolize --force --automake
# If libtoolize puts ltmain.sh in this directory, for what reason I
# cannot figure out, then move it to config
if [ -f ltmain.sh ]; then
    rm -f config/ltmain.sh
    mv ltmain.sh config
fi
aclocal -I config
autoheader
automake -f --add-missing --foreign
autoconf

set +x
echo 'run "configure; make"'
