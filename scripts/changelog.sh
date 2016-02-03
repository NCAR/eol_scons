#!/bin/bash

awkcom=`mktemp /tmp/${script}_XXXXXX.awk`
trap "{ rm -f $log $tmpspec $awkcom; }" EXIT

# In the changelog, copy most recent commit subject lines
# since this tag (max of 100).
sincetag=v2.0

# to get the most recent tag of the form: vN
sincetag=$(git tag -l --sort=version:refname "[vV][0-9]*" | tail -n 1)

if ! gitdesc=$(git describe --match "v[0-9]*"); then
    echo "git describe failed, looking for a tag of the form v[0-9]*"
    exit 1
fi

# example output of git describe: v2.0-14-gabcdef123
gitdesc=${gitdesc/#v}       # remove leading v
version=${gitdesc%%-*}       # 2.0

release=${gitdesc#*-}       # 14-gabcdef123
release=${release%-*}       # 14
[ $gitdesc == "$release" ] && release=0 # no dash

# run git describe on each hash to create a version
cat << \EOD > $awkcom
/^[0-9a-f]{7}/ {
    hash = $0
    cmd = "git describe --match '[vV][0-9]*' " hash " 2>/dev/null"
    res = (cmd | getline version)
    close(cmd)
    if (res == 0) {
        version = ""
    }
    else {
        # print "quack " version
        hash = gensub(".*-g([0-9a-f]+)","\\1",1,version)
        version = gensub("^v(.*)-g.*$","\\1",1,version)
        # print "version=" version ",hash=" hash
    }
}
/^eol-scons/ { print $0 " (" version ") stable; urgency=low" }
/^  \*/ { print $0 " (" hash ")" }
/^ --/ { print $0 }
/^$/ { print $0 }
EOD

# create change log from git log messages since the tag $sincetag.
# Put SHA hash by itself on first line. Above awk script then
# converts it to the output of git describe, and appends it to "*" line.
# Truncate subject line at 60 characters 
# git convention is that the subject line is supposed to be 50 or shorter
git log --max-count=100 --date-order --format="%H%neol-scons%n  * %s%n -- %aN <%ae>  %cD" --date=local ${sincetag}.. | awk -f $awkcom



