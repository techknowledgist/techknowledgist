#!/bin/csh -f

# this script assumes we are in ../../utils directory

set module = $1
set version = `date +"%Y%m%d-%H%M%S"`

echo tar cfp $module-$version.tar $module
tar cfp $module-$version.tar $module

echo mv $module-$version.tar ../tmp
mv $module-$version.tar ../tmp

echo rm -rf $module
rm -rf $module

echo tar xfp $module-*.tar
tar xfp $module-*.tar

echo mv $module-*.tar $module
mv $module-*.tar $module
