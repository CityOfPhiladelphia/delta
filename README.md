# Delta

Delta is tool for finding differences in CSV files, with an emphasis on content over formatting. Let's say our data looks like:

    /* file_1.csv */
    employee_id, hire_date
    1, 02-01-2010
    
    /* file_2.csv */
    employee_id, hire_date
    1, 1-FEB-2010
    
A basic diff tool will tell us that the `hire_date` changed from `02-01-2010` to `1-FEB-2010`, but really only the _format_ changed. What if we only want to know when the date itself changes? Delta allows you to progressively filter out known or acceptable differences so you can focus on real discrepancies in the data.

A typical workflow would be:

1. Run your data through Delta.
2. Look at the output and isolate known or uninteresting differences.
3. Write transforms to effectively ignore those cases on the next run.
4. Repeat.

## Installation

Delta is Python-based and requires Python 3.4+ to run.

    pip install git+https://github.com/cityofphiladelphia/delta.git

## Usage

The basic usage is `delta -c /path/to/config.py`. For more details see `delta --help`.

Delta assumes two files which it calls `A` and `B`. `A` is considered to be the "parent" and will be the basis for comparison. `B` might be the same dataset from a later point in time, or the result of a forked data workflow. See below for how to specify these.

## Config

Delta requires a config file to run. See `sample_config.py` for an example. The basic values are:

* `sources`: defines the source files and, optionally, what encoding to use
* `key_field`: the field to join on, as it appears in `A`. The field map will be used if applicable.
* `field_map` (_optional_): fields that were renamed in file `B`. Use the `B` fields as keys and `A` fields as values.
* `transforms` (_optional_): a mapping of transforms to be applied to `A` and `B` respective; see below for possible values
* `exclude_fields` (_optional_): fields to be exlcuded from the comparison. Since `A` is treated as the "parent", fields that appear in `B` only will be exlcuded by default.

### Transforms

The `transforms` field contains the actions that should be performed before comparing the data (note: this won't change any of the source data, just what's loaded into memory). These can be:
* the name of a function to be called on the value, as a `str`. For example, if you would normally trim whitespace by calling `some_string.strip()` you can use `'strip'` as the transform.
* a `lambda` function. These are useful for calling functions with an argument. For example, if you wanted to strip leading zeros you could use `lambda x: x.lstrip('0')`. For more information on `lambda`s, see [here](http://www.secnetix.de/olli/Python/lambda_functions.hawk).
* a function object. If you have a `def my_function():` somewhere in your config file, you can use that as a transform. Note this should be the raw name, not enclosed in quotes.

## Output

Delta will output a summary of adds, deletes, and changes. Changes will be broken down by field, with one example given for each change. For example:

    Adds: 39 (0%)
    Deletes: 22 (0%)
    Changes: 3409588
    
    taxable_building: 215052 (37%)                    example: 132619 => 102619
    census_tract: 24024 (4%)                          example: 027 => 700
    book_and_page: 14057 (2%)                         example: 3039496 => 1137216
    sale_price: 92 (0%)                               example: 171600 => 1

## Todo

* Add an option to output a list of all differences, not just a summary