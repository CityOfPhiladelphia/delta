import sys
import os
import csv
from collections import defaultdict, namedtuple
import random
import click
from pprint import pprint
from .util import import_module_from_file

def stringify_change(change):
    """Helper function to make a readable string out of a Change object
    (e.g. old_val => new_val)"""
    key = change.key
    a = change.a or '<null>'
    b = change.b or '<null>'
    return '{}: {} => {}'.format(key, a, b)

def make_row_map(file_path, key_field, field_map=None, transforms=None, \
                 file_encoding=None):
    """Constructs a map of data rows indexed by the key field. Also applies
    transforms and handles field mappings."""

    with open(file_path, encoding=file_encoding) as file:
        # preprocess transforms
        if transforms:
            _transforms = {}
            for tf_field, tf in transforms.items():
                _type = type(tf).__name__
                if _type not in ['str', 'function']:
                    raise ValueError('Invalid transform')
                _transforms[tf_field] = {
                    'transform':    tf,
                    'type':         _type
                }

        # get fields from csv
        fields_reader = csv.reader(file)
        fields = next(fields_reader)

        # make sure we aren't missing any field names
        first_row = next(fields_reader)
        if len(fields) != len(first_row):
            raise ValueError('Header has a different number of columns than data')

        # apply field map
        if field_map:
            # TODO use a case insensitive dictionary for field map
            fields = [field_map.get(field.lower()) or field for field in fields]
            key_field = field_map.get(key_field) or key_field

        # lowercase
        fields = [field.lower() for field in fields]

        # handle spaces
        fields = [field.replace(' ', '_') for field in fields]

        # use namedtuple for rows
        fields_joined = ' '.join(fields)
        Row = namedtuple('Row', fields_joined)

        # make map
        row_map = {}
        reader = csv.DictReader(file, fieldnames=fields)

        for i, row in enumerate(reader):
            key = row[key_field]

            # apply transforms
            if transforms:
                for tf_field, tf_map in _transforms.items():
                    tf = tf_map['transform']
                    tf_type = tf_map['type']
                    source_val = row[tf_field]
                    if tf_type == 'str':
                        val = getattr(source_val, tf)()
                    else:
                        val = tf(source_val)
                    row[tf_field] = val

            # row_map[key] = row
            # str_row = {key: str(val) for key, val in row.items()}
            row_map[key] = Row(**row)
            # from pprint import pprint
            # pprint(str_row)
            # row_map[key] = Row(**str_row)

        return row_map

def diff(row_map_a, row_map_b, key_field, exclude_fields=None, limit=None):
    """Returns a list of diff dicts. Types: add, delete, change."""

    # store changes as a namedtuple to save some memory
    Change = namedtuple('Change', 'key a b')

    # compute fields of interest
    fields_a = next(iter(row_map_a.values()))._fields
    fields_b = next(iter(row_map_b.values()))._fields
    common_fields = set(fields_a).intersection(fields_b)
    include_fields = common_fields - set(exclude_fields)

    # sort keys
    keys_a = sorted(list(row_map_a.keys()))
    keys_b = sorted(list(row_map_b.keys()))

    # limit, optionally
    if limit:
        keys_a = keys_a[:limit]
        keys_b = keys_b[:limit]

    # make sets for fast lookups
    keys_a_set = set(keys_a)
    keys_b_set = set(keys_b)

    # deletes
    dels = keys_a_set - keys_b_set

    # adds
    adds = keys_b_set - keys_a_set

    # changes
    not_deleted = sorted(list(keys_a_set - dels))
    changes = defaultdict(list)  # field => [{key: '', a: '', b: ''}]

    for key in not_deleted:
        row_a = row_map_a[key]
        row_b = row_map_b[key]

        # diff fields
        for field in include_fields:
            val_a = getattr(row_a, field)
            val_b = getattr(row_b, field)
            if val_a != val_b:
                change = Change(key=key, a=val_a, b=val_b)
                changes[field].append(change)

    diffs = {
        'adds':         adds,
        'deletes':      dels,
        'changes':      changes,
    }

    return diffs

@click.command()
@click.option('-c', '--config', help='Path to the config file')
@click.option('-e', '--expand', help='A comma-separated list of fields to '
                                     'provide additional examples of. By '
                                     'default this will return 20, but you can '
                                     'specify any number with '
                                     '`--expand=fields:n`. To expand all use '
                                     '`--expand=all`.')
@click.option('-l', '--limit', type=int, help='Max number of rows to diff '
                                              '(after sorting)')
def main(config, expand, limit):
    print('Starting...')

    # handle args
    if expand:
        if ':' in expand:
            expand_fields, expand_count_str = expand.split(':')
            expand_count = int(expand_count_str)
        else:
            expand_fields = expand
            expand_count = 20
        expand_fields = expand_fields.split(',')
    config_path = config

    # load config
    if config_path is None or not os.path.isfile(config_path):
        raise ValueError('Invalid config path')
    config_mod = import_module_from_file('config_mod', config_path)
    config = config_mod.config

    # some global config
    field_map = {key.lower(): val.lower() for key, val in \
                                config['field_map'].items()}
    key_field = config['key_field'].lower()
    exclude_fields = config['exclude_fields']

    print('Reading rows from A...')
    file_path_a = config['sources']['a']['file']
    # TODO: can `open` accept None as an encoding?
    file_encoding_a = config['sources']['a'].get('encoding') or 'utf-8'
    transforms_a = config.get('transforms').get('a')
    row_map_a = make_row_map(file_path_a, key_field, transforms=transforms_a)
    
    print('Reading rows from B...')
    file_path_b = config['sources']['b']['file']
    file_encoding_b = config['sources']['b'].get('encoding') or 'utf-8'
    transforms_b = config.get('transforms').get('b')
    row_map_b = make_row_map(file_path_b, key_field, field_map=field_map, \
                             transforms=transforms_b)

    print('Diffing...')
    diffs = diff(row_map_a, row_map_b, key_field, \
                 exclude_fields=exclude_fields, limit=limit)

    # summarize
    total = limit or len(row_map_a)
    adds = diffs['adds']
    adds_len = len(adds)
    print('\n#########################\n')
    print('Adds: {} ({}%)'.format(adds_len, round(100 * adds_len / total), 2))

    dels = diffs['deletes']
    dels_len = len(dels)
    print('Deletes: {} ({}%)'.format(dels_len, round(100 * dels_len / total), 2))

    changes = diffs['changes']
    changes_len = 0
    for field, field_changes in changes.items():
        changes_len += len(field_changes)
    print('Changes: {}\n'.format(changes_len))

    for field in sorted(changes, key=lambda k: len(changes[k]), reverse=True):
        field_changes = changes[field]
        field_changes_len = len(field_changes)
        example_change = field_changes[0]
        example = stringify_change(example_change)
        stats = '{}: {} ({}%)'.format(field,
                                      field_changes_len,
                                      round(100 * field_changes_len / total),
                                      2)
        print('{}{}example: {}'.format(stats, ' ' * (50 - len(stats)), example))

        # if the user requested additional examples
        if expand and (field in expand_fields or expand_fields == ['all']):
            print('\n    {} additional examples:'\
                      .format(expand_count))
            # get n random examples
            random.shuffle(field_changes)
            for change in field_changes[:expand_count]:
                example = stringify_change(change)
                print('    {}'.format(example))
            print()

    print('\n#########################')

# dev
if __name__ == '__main__':
    from config import config
    main(config)
