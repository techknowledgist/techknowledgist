
# copied from maturity/collect_usage_data, should be consolidated somewhere else

def filter_term(term, language):
    if language == "en": return filter_term_en(term)
    if language == "cn": return filter_term_cn(term)

def filter_term_en(term):
    """Filter out some obvious crap. Do not allow (i) terms with spaces only,
    (ii) terms that do not start with a letter or digit, (iii) terms with three
    or more hyphens/underscores in a row, (iv) terms where half or less of the
    characters are letters, and (v) terms with more than 75 characters. The last
    avoids using what could be huge outliers like gene sequences."""
    if term.strip() == '' \
       or not term[0].isalnum() \
       or term.find('---') > -1 \
       or term.find('___') > -1 \
       or len([c for c in term if c.isalpha()]) * 2 < len(term) \
       or len(term) > 75:
        return True
    return False

