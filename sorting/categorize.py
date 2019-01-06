#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys
import re
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from collections import namedtuple
import signal


Entry = namedtuple('Entry', 'status, date, description, debit, credit')

CATEGORIES = {
    'amazon':       '1',
    'eating out':   '2',
    'shopping':     '3',
    'misc':         '4',
    'costco':       '5',
    'gas':          '6',
    'grocery':      '7',
    'transit':      '8',
    'dogs':         '9',
    'payment':      '10',
    'bill':         '11',
    'vehicle':      '12',
    'pay check':    '13',
    'investments':  '14',
    'work':         '15',
    'gifts':        '16'
}
REV_CAT = {x:y for y, x in CATEGORIES.items()}

line_expr = '\"([a-zA-Z]+)\"\,\"([0-9]{2}\/[0-9]{2}\/[0-9]{4})\"\,\"([a-zA-Z0-9\#\-\&\.\* ,\':\n/`!]+)\"\,\"((?:(?:[0-9]+\,){0,1}[0-9]+\.[0-9]{2}){0,1})\"\,\"((?:(?:[0-9]+\,){0,1}[0-9]+\.[0-9]{2}){0,1})\"'
line_prog = re.compile(line_expr)

def parse_expenses(data):
    result = [Entry(*x) for x in line_prog.findall(data)]
    return result


def categorize(expense, known_results):
    while True:
        if expense.description in known_results:
            print('Known Description: [{}] --> [{}]'.format(expense.description, known_results[expense.description]))
            return known_results[expense.description]

        print('\n\nFull: [{}]'.format(expense))
        print(expense.description)
        for key, value in CATEGORIES.items():
            print('({}) --> [{}]'.format(value, key))
        result = input('Select category and [Enter]:')
        if result in REV_CAT:
            return REV_CAT[result]

def main():
    parser = argparse.ArgumentParser('Categorizer')

    parser.add_argument(
        'csv_file',
        type=Path,
        help='CSV file to categorize'
    )
    parser.add_argument(
        'output_file',
        type=Path,
        help='Loction to store resulting cateogry csv'
    )
    parser.add_argument(
        '--category_dict',
        '-d',
        type=Path,
        help='Dictionary of previously categorized entries',
        default=Path('~/.config/budget_tools/cat_dict.yaml').expanduser()
    )
    parser.add_argument(
        '--start_index',
        '-i',
        type=int,
        help='Index of expenses to start',
        default=0
    )

    args = parser.parse_args()

    if not args.category_dict.is_file():
        args.category_dict.parent.mkdir(parents=True, exist_ok=True)
        known_results = {}
    else:
        with args.category_dict.open() as known_file:
            known_results = load(known_file, Loader=Loader)

    if not args.csv_file.is_file():
        print('File provided not found')
    with args.csv_file.open() as expense_file:
        expense_data = expense_file.read()

    expenses = parse_expenses(expense_data)

    def handle_sigint(signum, frame):
        print('Saving Category Dict...')
        with args.category_dict.open('w') as known_file:
            dump(known_results, known_file, Dumper=Dumper)
        print('Saved  Category Dict')
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_sigint)
    for i, expense in enumerate(expenses[args.start_index:]):
        print('Index: [{}]'.format(i+args.start_index))
        category = categorize(expense, known_results)
        if expense.description not in known_results:
            known_results[expense.description] = category
    with args.category_dict.open('w') as known_file:
        dump(known_results, known_file, Dumper=Dumper)

    with args.output_file.open('w') as result_file:
        for expense in expenses:
            line = '"{status}","{date}","{description}","{debit}","{credit}","{category}"\n'.format(
                status=expense.status,
                date=expense.date,
                description=expense.description,
                debit=expense.debit,
                credit=expense.credit,
                category=known_results[expense.description]
            )
            result_file.write(line)
    return 0


if __name__ == '__main__':
    sys.exit((0 or main()))
