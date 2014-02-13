
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
            # TODO: we are not getting the right vbc_ids
            line = line[line.find(',')+1:]
            fields = line.strip().split('","')
            fields = fields[:-1] + fields[-1].split('",')
            vbc_id = fields[0]
            vbc_name = fields[1]
            self.vb_categories[vbc_id] = vbc_name
            c_id = fields[4]
            self.categories[c_id]= fields

    def get_very_broad_categories(self):
        return sorted(self.vb_categories.items())
    
    def get_very_broad_category_ids(self):
        return sorted(self.vb_categories.keys())
    
    def get_very_broad_category_names(self):
        return sorted(self.vb_categories.values())
    
    def get_all_info(self, id):
        return self.categories[id][:2]
        

if __name__ == '__main__':

    categories = Categories(CATEGORY_FILE)

    print categories.get_very_broad_categories()
    #print categories.get_very_broad_category_ids()
    #print categories.get_very_broad_category_names()

    for vbc_id, vbc_name in categories.get_very_broad_categories():
        print vbc_id, vbc_name
        
    for line in open(PATENTS_FILE):
        if line.startswith('"'): continue
        (patent_id, category_id) = line.strip().split(',')
        category_id = category_id.strip('"')
        print patent_id, category_id, categories.get_all_info(category_id)
        break
