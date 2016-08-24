import re

def handle_currency(val):
    """ This is an example of a function transform. Removes dollar signs and 
    decimal amounts from currency values."""
    match = re.match('^(\$)?(\d+)(?=\.)?', val)
    return match.group(2) if match else val

config = {
    # Files to read from
    'sources': {
        'a': {
            'file':         '~/data/properties_2014.csv',
        },
        'b': {
            'file':         '~/data/properties_2015.csv',
            # the csv module stumbles sometimes on non-utf-8 files, so use this
            'encoding':     'ascii',
        },
    },

    # This is not complete mapping of fields - just ones where the name changed
    # in B. The directionality of the mapping is B => A.
    'field_map': {
        # B              # A
        'propertyid':    'prop_id',
    },

    # Field name to join on, as it appears in A
    'key_field':    'prop_id',

    # Transformations to apply before comparing. Use field names from A
    # throughout (even in the B section).
        'a': {
            'market_value':         handle_currency,
            'unit_num':             lambda x: x.lstrip('0'),
        },
        'b': {
            'owner':              'rstrip',
        },
    },

    # Fields to exclude from the comparison. Use fields from A, since anything
    # that only appears in B will be excluded anyway.
    'exclude_fields': [
        'coordinates',
    ],

    # Max number of rows to compare, usually for testing purposes. Note that 
    # they're sorted first, so you won't be comparing x number of random rows :)
    'limit': None,
}
