#!/bin/sh

repo=eol_scons.git

cd /scr/tmp/$USER/$repo

git remote remove origin
git remote add origin git@github.com:ncareol/$repo

git push origin master
