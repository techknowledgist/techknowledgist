#!/bin/csh -f

set module = $1

echo rm -rf $module
rm -rf $module
echo tar xfp $module-*.tar
tar xfp $module-*.tar
echo mv $module-*.tar $module
mv $module-*.tar $module
