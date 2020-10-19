from operator import methodcaller
from toolz import flip
from toolz.curried import filter, get, map, pipe
from toolz.dicttoolz import dissoc
from typing import Any, Dict, List, Optional, Tuple
import argparse
import json
import sys


# Exclude these fields from the generated output
ATTRIBUTES_TO_SKIP = {'CommonSettlementID'}


def main():
    """ Convert JSON payload obtained from ResWare API+ GET /fees
        to JavaScript assertion statements for use in Runscope tests
    """
    with open('output.js', 'w') as output_file:
        results = process_json_file(*parse_command_line_arguments())
        output_file.write(generate_preamble())
        output_file.write(''.join(results))
        output_file.write(generate_end(len(results)))


def parse_command_line_arguments() -> Tuple[str, List[int]]:
    """ Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Generate Runscope test assertions')
    parser.add_argument(
        '--file', dest='file_name', help='Input file containing JSON to convert to assertions'
    )
    parser.add_argument(
        'integers', metavar='N', type=int, nargs='+', help='Integer that represents a SettlementTypeID'
    )
    args = parser.parse_args()
    return args.file_name, args.integers


def generate_preamble() -> str:
    """ Generate start of non-asserting JS code
    """
    return '''// check for specific status code
assert.equal(response.status, 200, "status was 200 OK");

// parse JSON response body into object
var data = JSON.parse(response.body);
var fees = data.fees;
var updated_fees = 0;
for (var i in fees) {
var fee = fees[i]
'''

def generate_end(num_fees: int) -> str:
    """ Generate end of non-asserting JS code
    """
    return f'''}}\nassert.equal(updated_fees, {num_fees});'''
 

def process_json_file(file_name: str, ids: List[int]) -> List[str]:
    """ Process a JSON file containing fee data and convert to JS assertions
    """
    open_file = flip(open, 'r')
    read_file = methodcaller('read')
    to_dict = json.loads
    desired_settlement_type = lambda fee: fee.get('SettlementTypeID') in ids

    return list(
        pipe(
            file_name,
            open_file,
            read_file,
            to_dict,
            get('fees'),
            filter(desired_settlement_type),
            map(generate_fee_assertions),
        )
    )


def generate_fee_assertions(fee: Dict) -> str:
    """ Convert a fee to JS assertion code
    """
    to_items = methodcaller('items')

    begin = generate_if_statement(fee)
    assertions = list(
        pipe(
            dissoc(fee, *ATTRIBUTES_TO_SKIP),
            to_items,
            map(generate_assertion),
        )
    )
    middle = ''.join(assertions)
    end = '\t\t++updated_fees;\n\t}\n'
    return begin + middle + end

    
def generate_if_statement(fee: Dict) -> str:
    """ Generates a JS 'if' statement
    """
    return f'\tif (fee.SettlementTypeID === {fee.get("SettlementTypeID")}) {{\n'


def generate_assertion(*args) -> str:
    arg, *_ = args
    key, value = arg
    if is_quoted_value_types(value):
        return quoted_value_assert(key, value)
    else:
        return unquoted_value_assert(key, nullify(value))


def is_quoted_value_types(value: Any) -> bool:
    """ Determine if value is of a type that should be quoted in the generated code
    """
    return type(value) is str or type(value) is float


def quoted_value_assert(key, value) -> str:
    """ Generate assertion code for quoted value
    """
    return f'\t\tassert.equal(fee.{key}, "{value}");\n'


def unquoted_value_assert(key, value) -> str:
    """ Generate assertion code for non-quoted value
    """
    return f'\t\tassert.equal(fee.{key}, {value});\n'


def nullify(value: Optional[Any]) -> str:
    """ Return 'null' string if value is None. Otherwise, return value
    """
    return 'null' if value is None else value


if __name__ == "__main__":
    main()
