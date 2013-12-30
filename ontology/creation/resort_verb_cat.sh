# Create new sorted verb category list after the file has been edited.

mv verb.cat.en.dat.sorted verb.temp
sort verb.temp > verb.cat.en.dat.sorted
cp verb.cat.en.dat.sorted verb.cat.en.dat
