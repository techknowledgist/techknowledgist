"""

Run through a list of <patent_id, category_id> pairs and generate files that
contain the the patents for each very broad category.

This version assumes that /home/j/marc/Dropbox/fuse/data/patents/categories'
has the following two files:

    category-codes.csv
    1997-2007 us patents w category code.csv

The output is written to 11 files, all of the format patents-category-NN.txt,
where NN is a numeric identifier for the broad category.

These are the Very Broad Categories, both the numerical identifier and the name,
prefix with the number of those patents over the first 100k patents of a list
from 1997-2007:

  269 10 Agriculture/Husbandry/Food
  371 11 Building/Construction/Housing Materials and Fixtures
 1401 12 Chemical
  713 13 Electrical
 1212 14 Health
  572 15 Industrial Processes/Tools/Equipment
  908 16 Instruments/Measuring, Testing & Control
  835 17 Mechanical
 1294 18 Other
 2424 19 Semiconductors/Computers/Communication
    0 99 Not Categorized
  
"""

import os

CATEGORIES_DIR = '/home/j/marc/Dropbox/fuse/data/patents/categories'

CATEGORY_FILE = os.path.join(CATEGORIES_DIR, 'category-codes.csv')
PATENTS_FILE = os.path.join(CATEGORIES_DIR, '1997-2007 us patents w category code.csv')


class Categories(object):

    def __init__(self, category_file):
        self.filename = category_file
        self.categories = {}
        self.vb_categories = {} # very broad categories
        for line in open(category_file):
            if line.startswith('"'): continue
            # finding the correct fields requires some maneuvring because not
            # all of them are surrounded by double quotes
            line = line[line.find(',')+1:]
            fields = line.strip().split('","')
            fields = fields[:-1] + fields[-1].split('",')
            fields = [f.strip('"') for f in fields]
            vbc_id, vbc_name = fields[0:2]
            self.vb_categories[vbc_id] = vbc_name
            c_id = fields[4]
            self.categories[c_id]= fields

    def get_very_broad_categories(self):
        return sorted(self.vb_categories.items())
    
    def get_very_broad_category_ids(self):
        return sorted(self.vb_categories.keys())
    
    def get_very_broad_category_names(self):
        return sorted(self.vb_categories.values())
    
    def get_very_broad_category(self, id):
        return self.categories[id][:2]
        

if __name__ == '__main__':

    categories = Categories(CATEGORY_FILE)

    #print categories.get_very_broad_categories()
    #print categories.get_very_broad_category_ids()
    #print categories.get_very_broad_category_names()
    fhs = {}
    for vbc_id, vbc_name in categories.get_very_broad_categories():
        print vbc_id, vbc_name
        fhs[vbc_id] = open("patents-category-%s.txt" % vbc_id, 'w')
        fhs[vbc_id].write("# %s\n" % vbc_name)

    count = 0
    for line in open(PATENTS_FILE):
        count += 1
        if count % 100000 == 0: print count
        #if count > 10000: break
        if line.startswith('"'): continue
        (patent_id, category_id) = line.strip().split(',')
        category_id = category_id.strip('"')
        vbc_id, bc_name = categories.get_very_broad_category(category_id)
        fhs[vbc_id].write("%s\n" % patent_id)
        #print patent_id, category_id, vbc_name
        #break
