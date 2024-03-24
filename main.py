import json
import collections
import os
from datetime import datetime, timedelta
from operator import itemgetter
import sys
import pprint as pp

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QItemSelection, QItemSelectionModel, Qt, QProcess, QProcessEnvironment
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QLabel, QFrame

from CustompProxyModel import CustomProxyModel
from SummaryTableModel import SummaryTableModel
from dtool_gui import Ui_MainWindow

# Global dictionaries
config_data = {}
transactions_by_ticker = collections.defaultdict(list)
ticker_summary = collections.defaultdict(list)
sector_summary = collections.defaultdict(list)
sector_details = collections.defaultdict(list)
transactions_calendar = {}
ym_div = collections.defaultdict(list)
ticker_divs = collections.defaultdict(list)
ticker_divs_aggregated = collections.defaultdict(list)
ticker_divs_aggregated_with_yield = collections.defaultdict(list)
ym_div_aggregated = collections.defaultdict(lambda: [0, 0])
ticker_names = {}
ticker_sector = {}

# Global lists
overall_summary = []
selected_ticker = None
cal_data_div_after_tax = None
cal_investment = None
calendar_header = None
total_annual_dividend_before_tax = 0
total_annual_dividend_after_tax = 0

# Constants
summary_header = ['Ticker', '#', 'Inv', 'Alloc', 'Ann_B', 'Yoc_B', 'Con%', 'Ann_A', 'Yoc_A', 'Name', 'Sector', '+-']
ticker_index = summary_header.index('Ticker')
nos_index = summary_header.index('#')
inv_index = summary_header.index('Inv')
alloc_index = summary_header.index('Alloc')
annb_index = summary_header.index('Ann_B')
yocb_index = summary_header.index('Yoc_B')
con_percent_index = summary_header.index('Con%')
anna_index = summary_header.index('Ann_A')
yoca_index = summary_header.index('Yoc_A')
name_index = summary_header.index('Name')
sector_index = summary_header.index('Sector')

transaction_summary_header = ['Ticker', 'Date', 'b/s', '#', 'Invested', 'CPS']
dividend_summary_header = ['Ticker', 'F', 'Date', '#', 'DPS', 'Div_B', 'Ann_B', 'Yoc_B', 'Div_A', 'Ann_A', 'Yoc_A', 'Where', 'DivInc']
dividend_calendar_details_header = ['Ticker', 'F', 'Date', '#', 'DPS', 'Div_B', 'Div_A']
investment_calendar_details_header = ['Ticker', 'Date', 'B/S', '#', 'Cost', 'DPS']
frequency_factors = {'q': 4, 'm': 12, 'a': 1, 'b': 2}

# Constants and mappings
column_alignments = {0: Qt.AlignLeft, 1:Qt.AlignCenter,  10: Qt.AlignLeft, 11: Qt.AlignLeft}
transaction_column_alignments = {0: Qt.AlignLeft, 2: Qt.AlignLeft}
dividend_column_alignments = {0: Qt.AlignLeft, 1: Qt.AlignLeft, 2: Qt.AlignLeft, 11: Qt.AlignLeft, 12: Qt.AlignLeft}
month_dict = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
width_mapping = {
    'calendar_details_table': [60, 100],
    'transaction_summary_table': [35, 90],
    'dividend_summary_table': [50, 100],
}
# Define a dictionary mapping each frequency to its corresponding timedelta
frequency_timedelta = {
    'q': timedelta(days=95),  # Quarterly dividend payment (approximately 3 months)
    'm': timedelta(days=35),       # Monthly dividend payment (1 month)
    'a': timedelta(days=370),      # Annual dividend payment (1 year)
    'b': timedelta(days=185),   # Biannual dividend payment (approximately 6 months)
}

def convert_and_format(value):
    try:
        f = float(value)
        return "{:.2f}".format(f)
    except ValueError:
        return value

def parse_config_file(file_path):
    global config_data
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print("Config file not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON in config file.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def initialize_const_indexes():
    global const_indexes
    const_indexes = {
        'ticker': 0,
        'date': 1,
        'action': 2,
        'num_shares': 3,
        'cost': 4,
        'parts_in_transaction': 7,
        'summary_num_of_shares': 0,
        'summary_invested': 1,
    }

def parse_names_file():
    file_name = config_data.get('input_folder') + '/' + config_data.get('names_file')
    file_name = os.path.expanduser(file_name)

    if not file_name:
        print("Names file path not specified in config.")
        return

    try:
        with open(file_name, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '-' not in line:
                    continue
                ticker, name, sector = map(str.strip, line.split('-', 2))
                ticker_names[ticker.lower()] = name.replace('_', ' ')
                ticker_sector[ticker.lower()] = sector.strip()
    except FileNotFoundError:
        print("Names file not found.")
    except Exception as e:
        print(f"An error occurred while parsing names file: {str(e)}")

def parse_line(line):
    parts = line.strip().split('-')
    if len(parts) != const_indexes['parts_in_transaction']:
        return None
    ticker, year, month, day, action, num_shares, cost = [part.strip().lower() for part in parts]

    if not all([ticker, year, month, day, action, num_shares, cost]):
        return None

    if action not in ['buy', 'sell']:
        print('Invalid action: {}'.format(action), line)
        return None

    date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    cost = float(cost) if action == 'buy' else -float(cost)
    # pp.pprint([ticker, date, action, int(num_shares), cost])
    return [ticker, date, action, int(num_shares), cost]

def parse_akt():
    initialize_const_indexes()  # Initialize const_indexes
    file_path = config_data.get('input_folder') + '/' +config_data.get('akt_file')
    file_path = os.path.expanduser(file_path)
    if not file_path:
        print("Akt file path not specified in config.")
        return

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                transaction = parse_line(line)
                if transaction:
                    ticker = transaction[const_indexes.get('ticker')]
                    transactions_by_ticker[ticker].append(transaction)
    except FileNotFoundError:
        print("Akt file not found.")
        return
    except Exception as e:
        print(f"An error occurred while parsing akt file: {str(e)}")
        return

    calculate_summary()  # Calculate summary statistics
    update_overall_summary()  # Update overall_summary with name and sector corresponding to each ticker
    calculate_sector_summary()  # Calculate summary statistics for each sector
    # update_sector_details()  # Update sector_details with ticker details
    calculate_allocation_percentage()  # Calculate allocation percentage for each ticker within its sector

def calculate_summary():
    # Calculate summary statistics
    for ticker, transactions in transactions_by_ticker.items():
        total_shares = sum(
            transaction[const_indexes['num_shares']] * (-1 if transaction[const_indexes['action']] == 'sell' else 1)
            for transaction in transactions
        )
        total_invested = sum(transaction[const_indexes['cost']] for transaction in transactions)
        if total_shares > 0:
            ticker_summary[ticker] = [total_shares, total_invested]
        else:
            ticker_summary[ticker] = [total_shares, 0]

    # Calculate overall summary
    total_invested = sum(summary[const_indexes['summary_invested']] for summary in ticker_summary.values())

    for ticker, summary in ticker_summary.items():
        invested = summary[const_indexes['summary_invested']]
        allocation_percentage = ( invested/ total_invested) * 100
        overall_summary.append( [ticker, summary[const_indexes['summary_num_of_shares']], invested, allocation_percentage])

def aggregate_transactions_by_ticker():
    for ticker, transactions in transactions_by_ticker.items():
        total_count = len(transactions)
        total_shares = sum(
            transaction[const_indexes['num_shares']] * (-1 if transaction[const_indexes['action']] == 'sell' else 1)
            for transaction in transactions
        )
        total_invested = sum(float(transaction[const_indexes['cost']]) for transaction in transactions)

        for transaction in transactions:
            num_shares = int(transaction[const_indexes['num_shares']])
            cost = float(transaction[const_indexes['cost']])
            transaction[const_indexes['cost']] = "{:.2f}".format(cost)
            transaction.append("{:.2f}".format(cost / num_shares) if num_shares != 0 else '')

        transactions.append(['Total', '', total_count, total_shares, "{:.2f}".format(total_invested), "{:.2f}".format(total_invested / total_shares) if total_shares != 0 else ''])

def update_overall_summary():
    global ticker_names, ticker_sector, overall_summary
    for summary in overall_summary:
        ticker = summary[ticker_index]
        name = ticker_names.get(ticker, "Unknown")
        sector = ticker_sector.get(ticker, "Unknown")
        summary.extend([name, sector])
    overall_summary.sort(key=lambda x: x[ticker_index])


def calculate_sector_summary():
    global const_indexes, ticker_summary, sector_summary, ticker_sector

    for ticker, summary in ticker_summary.items():
        nos = summary[0]
        #pp.pprint(summary)
        sector = ticker_sector.get(ticker, "Unknown")
        total_invested = summary[const_indexes['summary_invested']]
        sector_info = sector_summary.setdefault(sector, [0, 0, 0])
        if nos > 0:
            sector_info[0] += total_invested
            sector_info[2] += 1
        if sector in sector_details:
            sector_details[sector].append([ticker, total_invested, 0])
        else:
            sector_details[sector] = [[ticker, total_invested, 0]]


def calculate_allocation_percentage():
    global sector_details, sector_summary

    for sector, details in sector_details.items():
        total_invested_in_sector = sector_summary[sector][0]
        for detail in details:
            if total_invested_in_sector > 0:
                detail[2] = (detail[1] / total_invested_in_sector) * 100
            else:
                detail[2] = 0

def update_transactions_calendar():
    global transactions_calendar
    # Initialize a dictionary to store the total investment for each month
    calendar = {}

    # Iterate through each element in transactions_by_ticker
    for ticker, transactions in transactions_by_ticker.items():
        for transaction in transactions[:-1]:
            date = transaction[1]  # Extract date from the transaction
            year_month = date[:7]  # Extract year and month (yyyy-mm)
            cost = float(transaction[4])  # Extract cost from the transaction
            # Add the cost to the existing value or initialize it if the key doesn't exist
            calendar[year_month] = calendar.get(year_month, 0) + cost

    # Update the global transaction_calendar
    transactions_calendar = calendar


def write_calendar_to_file(data, fname):
    current_year = datetime.now().year
    years = list(range(current_year, current_year - len(data[0]), -1))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    processed_data = [','.join(['Month'] + [str(year) for year in years])]

    for i, line in enumerate(data):
        modified_line = months[i] + ',' + ','.join(str(x).replace('.','0') if x is not None else '0' for x in line)
        processed_data.append(modified_line)

    with open(f"{config_data['output_path']}/{fname}", 'w') as file:
        for line in processed_data:
                file.write(line + '\n')


def display_calendar(calendar, cal_type=None):
    global calendar_header
    # Extract the years from the keys in calendar and filter out years before 2015
    current_year = datetime.now().year
    years = list(range(current_year, 2014, -1))
    calendar_header = years  # Create the header with years from the current year to 2015
    data = []  # Create a list to store the data for each month
    totals = [0] * len(years)  # Initialize a list to store totals for each year

    nos_index = summary_header.index('#')
    invested_index = summary_header.index('Inv')
    # Iterate over months (Jan to Dec)
    for month in range(1, 13):
        # month_data = [month_abbr[month - 1]]
        month_data = []

        # Add the value for each year's corresponding month (or '#' if not present)
        for year_index, year in enumerate(years):
            month_year = f"{year}-{month:02d}"
            if month_year in calendar:
                val = calendar[month_year]
                rounded_data = int(round(val))
                month_data.append(rounded_data)
                totals[year_index] += val
            else:
                month_data.append('.')

        # Append the month's data to the main data list
        data.append(month_data)

    if cal_type == 'dividend_after_tax':
        write_calendar_to_file(data, 'div_cal.txt')
    elif cal_type == 'transactions':
        write_calendar_to_file(data, 'transactions_cal.txt')

    # Round the totals and append
    rounded_totals = [int(round(total)) if total != '.' else '.' for total in totals]
    data.append(rounded_totals)

    # Calculate and append the 'Average' row
    average_row = []
    for total in totals:
        if total == '.':
            average_row.append('.')
        else:
            average = int(round(total / 12))  # Always divide by 12 for average
            average_row.append(average)
    data.append(average_row)

    # Calculate and append the '∑' (big sigma) row
    grand_total = sum([val for val in totals if val != '.'])
    years_since_2015 = current_year - 2014
    if cal_type == 'transactions':
        invested = 0
        for inner_list in overall_summary:
            if inner_list[nos_index] != 0:
                invested += inner_list[invested_index]
        sigma_row = [int(invested), '', 'Φ', round(invested / years_since_2015)]
    else:
        sigma_row = [round(grand_total), '', 'Φ', round(grand_total / years_since_2015)]

    total_row_length = len(rounded_totals)
    while len(sigma_row) < total_row_length:
        sigma_row.append('~')
    data.append(sigma_row)
    return calendar_header, data


def is_valid_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def to_annual_div(frequency, dividend_per_share):
    if frequency in frequency_factors:
        return dividend_per_share * frequency_factors[frequency]
    raise ValueError(f"Unsupported frequency: {frequency}. Expected 'Q', 'M', 'A', or 'B'.")
def parse_dividend_line(line):
    parts = [part.strip() for part in line.split('-')]

    ticker = parts[0]
    frequency = parts[1].strip()
    month = parts[2].zfill(2)
    year = parts[3]
    date = f"{year}-{month}"  # Date format: yyyy-mm
    num_shares = int(parts[4])
    # Check if dividend_per_share is empty
    if parts[5] == '':
        total_dividend_before_tax = float(parts[6])
        dividend_per_share = total_dividend_before_tax / num_shares
    else:
        dividend_per_share = float(parts[5])
        total_dividend_before_tax = float(parts[6])

    # Check if total dividend after tax and 'where' are provided
    if len(parts) >= 8:
        if is_valid_number(parts[7]):
            total_dividend_after_tax = float(parts[7])
            where = parts[8] if len(parts) >= 9 else '#'
        else:
            # If not provided or not a valid number, calculate after-tax dividend
            total_dividend_after_tax = total_dividend_before_tax * config_data.get('tax_factor')
            where_index = 7 if len(parts) >= 8 else 6
            where = parts[where_index]
    else:
        total_dividend_after_tax = total_dividend_before_tax * config_data.get('tax_factor')
        where = "#"

    return [ticker, frequency, date, num_shares, dividend_per_share,
            total_dividend_before_tax, total_dividend_after_tax,where]

def update_ym_div_and_aggregated(parsed_data):
    global ym_div, ym_div_aggregated, ticker_divs
    for entry in parsed_data:
        ticker, _, date, _, _, total_dividend_before_tax, total_dividend_after_tax, _ = entry
        # Update ym_div
        ym_div[date].append(entry)
        ticker_divs[ticker].append(entry)

        # Update ym_div_aggregated - before. after
        ym_div_aggregated[date][0] += total_dividend_before_tax
        ym_div_aggregated[date][1] += total_dividend_after_tax


def post_process_divs():
    global ticker_divs, ticker_divs_aggregated

    processed_divs = {}
    for ticker, div_entries in ticker_divs.items():
        divs_by_date = {}

        for entry in div_entries:
            key = entry[2]

            if key not in divs_by_date:
                divs_by_date[key] = entry[:]  # Create a copy of the entry to avoid modifying the original list
                divs_by_date[key][3] = divs_by_date[key][5] = divs_by_date[key][6] = 0
            else:
                divs_by_date[key][-1] = '~'
            # Accumulate num_shares, total_dividend_before_tax, and total_dividend_after_tax for the same date
            divs_by_date[key][3] += entry[3]  # Increment num_shares
            divs_by_date[key][5] += entry[5]  # Add to total_dividend_before_tax
            divs_by_date[key][6] += entry[6]  # Add to total_dividend_after_tax

        # Add processed entries to the final result
        processed_divs[ticker] = list(divs_by_date.values())

    ticker_divs_aggregated = processed_divs
    # pp.pprint(ticker_divs_aggregated)
    return processed_divs

def append_yield():
    global ticker_summary, ticker_divs_aggregated, ticker_divs_aggregated_with_yield
    # Retrieve total_invested and total_shares from ticker_summary
    for ticker, divs in ticker_divs_aggregated.items():
        total_shares, total_invested = ticker_summary.get(ticker, [0, 0])
        for div in divs:
            ticker, frequency, date, num_shares, dividend_per_share, total_dividend_before_tax, total_dividend_after_tax, where = div
            annual_div_before_tax = to_annual_div(frequency, total_dividend_before_tax)
            annual_div_after_tax= to_annual_div(frequency, total_dividend_after_tax)

            # Calculate yield before tax and yield after tax
            if total_shares == 0:
                yield_before_tax = yield_after_tax = 0
            else:
                # Pre-calculate the common expression (yield factor)
                yield_factor =  100 / total_invested * total_shares/num_shares
                yield_before_tax = annual_div_before_tax * yield_factor
                yield_after_tax = annual_div_after_tax * yield_factor

            result = (ticker, frequency, date, num_shares, dividend_per_share,
                total_dividend_before_tax, annual_div_before_tax , yield_before_tax,
                total_dividend_after_tax, annual_div_after_tax , yield_after_tax,
                where)
            ticker_divs_aggregated_with_yield[ticker].append(result)

def parse_dividend_file(file_path):
    # global config_data
    # file_path = config_data.get('div_file', None)

    if not file_path:
        print("Error: No file path specified in the config dictionary.")
        return None

    parsed_data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip().lower()

            # Ignore lines starting with #
            if not line.startswith('#'):
                parsed_data.append(parse_dividend_line(line))

    update_ym_div_and_aggregated(parsed_data)
    post_process_divs()
    append_yield()
    return parsed_data

def split_ym_div_aggregated(ym_div_aggregated):
    aggregated_dividend_before_tax_dict = {}
    aggregated_dividend_after_tax_dict = {}

    for key, value in ym_div_aggregated.items():
        aggregated_dividend_before_tax_dict[key] = value[0]
        aggregated_dividend_after_tax_dict[key] = value[1]

    return aggregated_dividend_before_tax_dict, aggregated_dividend_after_tax_dict

def calculate_next_expected_date(frequency, latest_date):
    next_date = latest_date + frequency_timedelta.get(frequency, timedelta(0))
    return next_date.strftime('%Y-%m')

def add_expected_dividends():
    global ticker_divs_aggregated_with_yield, overall_summary, config_data
    tax_factor = config_data.get('tax_factor')

    for ticker, div_entries in ticker_divs_aggregated_with_yield.items():
        latest_div_entry = max(div_entries, key=lambda x: datetime.strptime(x[2], '%Y-%m'))
        latest_frequency = latest_div_entry[1]
        latest_dps = latest_div_entry[4]
        latest_num_shares_that_paid_dividend = latest_div_entry[3]
        dividend_before_tax = latest_div_entry[5]

        # Find the entry corresponding to the ticker in overall_summary and extract num_shares, total_invested_in_this_stock from the match
        num_shares, total_invested_in_this_stock = next((entry[nos_index], entry[inv_index]) for entry in overall_summary if entry[ticker_index] == ticker)

        # Calculate expected dividend before tax per share
        expected_dividend_before_tax_per_share = dividend_before_tax / latest_num_shares_that_paid_dividend
        expected_dividend_before_tax = expected_dividend_before_tax_per_share * num_shares

        if total_invested_in_this_stock > 0:
            factor = 100 / total_invested_in_this_stock
        else:
            factor = 0
        annual_expected_div_before_tax = to_annual_div(latest_frequency, expected_dividend_before_tax)
        yoc_before_tax = annual_expected_div_before_tax *factor

        # Calculate expected dividend after tax
        expected_dividend_after_tax = expected_dividend_before_tax * tax_factor
        annual_expected_div_after_tax = to_annual_div(latest_frequency, expected_dividend_after_tax)
        yoc_after_tax = annual_expected_div_after_tax * factor if num_shares >0 else ''

        latest_date = datetime.strptime(latest_div_entry[2], '%Y-%m')
        next_date = calculate_next_expected_date(latest_frequency, latest_date) if num_shares >0 else ''
        # Create a new row with the expected dividend information
        expected_div_row = [ticker, 'Next/'+latest_frequency, next_date, num_shares,
                            latest_dps,
                            expected_dividend_before_tax, annual_expected_div_before_tax, yoc_before_tax,
                            expected_dividend_after_tax, annual_expected_div_after_tax, yoc_after_tax,
                            '', '']

        # Add the new row to the list of dividend entries
        div_entries.append(expected_div_row)


def mark_dividend_increase():
    global ticker_divs_aggregated_with_yield, total_annual_dividend_before_tax,   total_annual_dividend_after_tax

    for ticker, div_entries in ticker_divs_aggregated_with_yield.items():
        # Sort the dividend entries by date in ascending order
        sorted_div_entries = sorted(div_entries[:-1], key=lambda x: x[2])

        # Mark the first entry as "~.~"
        sorted_div_entries[0] += ("~.~",)

        max_range=len(sorted_div_entries) - 1
        for i in range(max_range):
            current_div, next_div = sorted_div_entries[i], sorted_div_entries[i + 1]
            current_dps, next_dps = current_div[4], next_div[4]

            if current_dps == next_dps:
                mark = "."
            elif current_dps < next_dps:
                increase_percentage = ((next_dps - current_dps) / current_dps) * 100
                mark = f"+{increase_percentage:.2f}%"
            else:
                decrease_percentage = ((current_dps - next_dps) / current_dps) * 100
                mark = f"-{decrease_percentage:.2f}%"

            sorted_div_entries[i + 1] += (mark,)  # Append the mark to the dividend entry at index i+1

        # Mark the last entry as "~.~" if not already marked
        if len(sorted_div_entries[-1]) == len(div_entries[0]):
            sorted_div_entries[-1] += ("~.~",)

        total_dividend_before_tax, total_dividend_after_tax = map(sum, zip(*((entry[5], entry[8]) for entry in sorted_div_entries)))
        total_row = ("Total", "", "",  "", "", f"{total_dividend_before_tax:.2f}", "", "", f"{total_dividend_after_tax:.2f}", "", "", "", "" )

        expected =  div_entries[-1]
        if expected[3] != 0:  # Check for non-zero share count
            total_annual_dividend_before_tax += expected[6]
            total_annual_dividend_after_tax += expected[9]

        # Mark the entry with the next expected dividend as "~.~"
        div_entries[-1] += ("~.~",)
        sorted_div_entries.append(div_entries[-1])

        # Update the entries in ticker_divs_aggregated_with_yield with the marked entries
        ticker_divs_aggregated_with_yield[ticker] = sorted_div_entries + [total_row]

def clean_overall_summary():
    global overall_summary

    # Define formatting functions
    def format_integer(value):
        return round(value)

    def format_percentage(value):
        return "{:.2f}%".format(value)

    # Define lists for integer and percentage indices
    integer_indices = [inv_index, annb_index, anna_index]
    percentage_indices = [alloc_index, yocb_index, con_percent_index]

    # Iterate through each entry in overall_summary
    for entry in overall_summary:
        # Apply formatting functions to integer indices
        for index in integer_indices:
            entry[index] = format_integer(entry[index])

        # Apply formatting functions to percentage indices
        for index in percentage_indices:
            value = entry[index]
            entry[index] = format_percentage(value)

        yoca = entry[yoca_index]
        entry[yoca_index] = "{:.2f}%".format(yoca) if is_valid_number(yoca) else ''



def clean_ticker_divs_aggregated_with_yield():
    global ticker_divs_aggregated_with_yield
    cleaned_data = {}

    for ticker, data_list in ticker_divs_aggregated_with_yield.items():
        cleaned_data_list = []
        last_row = data_list[-1]

        for item in data_list[:-1]:
            item = list(item)
            item[4] = "{:.3}".format(item[4])
            item[5] = round(item[5],2)
            item[6] = int(round(item[6], 0))
            item[7] = "{:.2%}".format(item[7]/100)
            item[8] = round(item[8], 2)
            item[9] = int(round(item[9], 0))
            item[10] = "{:.2%}".format(item[10] / 100) if is_valid_number(item[10]) else ''
            cleaned_data_list.append(tuple(item))
        cleaned_data_list.append(last_row)
        cleaned_data[ticker] = cleaned_data_list
    ticker_divs_aggregated_with_yield = cleaned_data


def update_overall_summary_with_yoc():
    global ticker_divs_aggregated_with_yield, total_annual_dividend_before_tax, total_annual_dividend_after_tax, overall_summary

    next_entries = {}
    for ticker, div_entries in ticker_divs_aggregated_with_yield.items():
        # Find the 'Next' entry and store it in the dictionary
        for entry in div_entries:
            if 'Next' in entry[1] :
                next_entries[ticker] = entry
                break

    # Iterate through overall_summary and update entries using the 'Next' entries
    for summary_entry in overall_summary:
        ticker = summary_entry[ticker_index]
        expected_div = next_entries.get(ticker)

        # If no 'Next' entry is found, set all new fields to zero
        if expected_div is None:
            ae_b = con_b = yoc_b = ae_a = yoc_a = con_a = 0
        else:
            ae_b, ae_a, yoc_b, yoc_a = expected_div[6], expected_div[9], expected_div[7], expected_div[10]
            con_b = ae_b / total_annual_dividend_before_tax * 100
            con_a = ae_a / total_annual_dividend_after_tax * 100

        # Update the overall_summary entry for the ticker with the new fields
        # Insert the new fields starting from the 4th position (0-indexed)
        summary_entry[annb_index:annb_index] = [ae_b, yoc_b, con_b, ae_a, yoc_a ]
    clean_overall_summary()

def get_received_dividends_by_month(ym):
    global ticker_divs_aggregated_with_yield

    received_dividends = [
        list(dividend[:6]) + [dividend[8]]
        for dividends_list in ticker_divs_aggregated_with_yield.values()
        for dividend in dividends_list
        if len(dividend) >= 9 and dividend[2] == ym and dividend[3]>0
    ]

    # Separate the list into 'Next' and 'Received' dividends
    next_list = [dividend for dividend in received_dividends if dividend[1].startswith('Next')]
    rcvd_list = [dividend for dividend in received_dividends if not dividend[1].startswith('Next')]

    # Sort the lists
    next_list.sort(key=itemgetter(0))
    rcvd_list.sort(key=itemgetter(0))

    # Calculate totals for 'Received' dividends
    rcvd_total = calculate_total(rcvd_list)

    # Calculate totals for 'Next' dividends
    next_total = calculate_total(next_list)

    # Prepare the result list
    result_list = []
    if rcvd_list:
        result_list.extend(rcvd_list)
        result_list.append(rcvd_total)

    if next_list:
        result_list.extend(next_list)
        result_list.append(next_total)

    # Calculate the grand total if both 'Next' and 'Received' lists are non-empty
    if next_list and rcvd_list:
        grand_total = calculate_grand_total(next_total, rcvd_total)
        result_list.append(grand_total)

    return result_list

def calculate_total(dividends_list):
    if dividends_list:
        count = len(dividends_list)
        total = ['Total', count] + ['.' for _ in range(3)] + [
            round(sum(item[-2] for item in dividends_list), 2),
            round(sum(item[-1] for item in dividends_list), 2)
        ]
    else:
        total = []
    return total

def calculate_grand_total(next_total, rcvd_total):
    if next_total and rcvd_total:
        count = next_total[1] + rcvd_total[1]
        grand_total = ['Σ', count] + ['.' for _ in range(3)] + [
            round(next_total[-2] + rcvd_total[-2], 2),
            round(next_total[-1] + rcvd_total[-1], 2)
        ]
    else:
        grand_total = []
    return grand_total

def get_investments_by_month(ym):
    global transactions_by_ticker

    investments=[]
    for inv_list in transactions_by_ticker.values():
        for inv in inv_list:
            # print(inv)
            if ym in inv[1]:
                investments.append(inv)

    investments_list=[]
    if investments:
        investments_list = sorted(investments, key=itemgetter(0))
        total = sum(float(item[4]) for item in investments_list)
        count = len(investments_list)
        total_row = ['Total', count, '', '', "{:.2f}".format(total), '']
        investments_list.append(total_row)
    return investments_list



def main_with_print():
    global cal_data_div_after_tax, cal_investment, cal_data_div_before_tax
    parse_config_file('config.json')
    parse_names_file()  # Call parse_names_file before parse_akt
    parse_akt()
    aggregate_transactions_by_ticker()
    update_transactions_calendar()
    header, cal_investment = display_calendar(transactions_calendar, cal_type='transactions')
    fname = os.path.expanduser(config_data.get('input_folder', None) + '/' + config_data.get('div_file', None))
    parse_dividend_file(fname)
    add_expected_dividends()
    mark_dividend_increase()
    update_overall_summary_with_yoc()
    clean_ticker_divs_aggregated_with_yield()
    aggregated_dividend_before_tax_dict, aggregated_dividend_after_tax_dict = split_ym_div_aggregated(ym_div_aggregated)
    header, cal_data_div_after_tax = display_calendar(aggregated_dividend_after_tax_dict, 'dividend_after_tax')
    header, cal_data_div_before_tax = display_calendar(aggregated_dividend_before_tax_dict, 'dividend_before_tax')
    update_overall_summary_with_inc_dec()


def update_overall_summary_with_inc_dec():
    global overall_summary
    new_position = 1
    for entry in overall_summary:
        if entry[nos_index] == 0:
            entry.insert(new_position,'#')
            continue
        ticker = entry[ticker_index]
        divs = ticker_divs_aggregated_with_yield.get(ticker)
        if divs == None:
            entry.insert(new_position,'*')
            continue
        if len(divs) >= 3:
            div=divs[-3]
            ff = div[1]
            f = frequency_factors[ff]
            result = divs[-f-2:-2]
            if result is not None:
                marked = False
                for element in result[::-1]:
                    if element[-1].startswith('+'):
                        entry.insert(new_position,'+')
                        marked = True
                        break
                    if element[-1].startswith('-'):
                        entry.insert(new_position,'-')
                        marked = True
                        break
                if not marked :
                    if len(result) >= f:
                        entry.insert(new_position,'=')
                    else:
                        entry.insert(new_position,'?')
        else:
            entry.insert(new_position,'~')
        reset_header()

def reset_header():
    global summary_header, ticker_index, nos_index, inv_index, alloc_index, annb_index, yocb_index, con_percent_index, anna_index, yoca_index, name_index, sector_index, plus_minus_index

    summary_header = ['Ticker', '+-', '#', 'Inv', 'Alloc', 'Ann_B', 'Yoc_B', 'Con%', 'Ann_A', 'Yoc_A', 'Name', 'Sector' ]
    ticker_index = summary_header.index('Ticker')
    nos_index = summary_header.index('#')
    inv_index = summary_header.index('Inv')
    alloc_index = summary_header.index('Alloc')
    annb_index = summary_header.index('Ann_B')
    yocb_index = summary_header.index('Yoc_B')
    con_percent_index = summary_header.index('Con%')
    anna_index = summary_header.index('Ann_A')
    yoca_index = summary_header.index('Yoc_A')
    name_index = summary_header.index('Name')
    sector_index = summary_header.index('Sector')

def set_vertical_header_properties(table_view):
    tvh = table_view.verticalHeader()
    tvh.setDefaultSectionSize(10)
    tvh.sectionResizeMode(QHeaderView.Fixed)
# ---------------------------------------------------------------

# -------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, overall_summary):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_shortcuts_and_connections()
        self.create_status_bar()
        self.fill_investment_calendar()
        self.fill_dividend_calendar_after_tax()
        self.setup_summary_table()
        self.setup_transaction_summary_table()
        self.setup_dividend_summary_table()
        self.setup_sector_summary_table()
        self.start_external_process()

    def setup_summary_table(self):
        self.summary_model = SummaryTableModel(overall_summary, summary_header, column_alignments, 'overall_summary', config_data)
        t = self.ui.summary_table
        t.setObjectName("summary_table")
        self.proxy_model = CustomProxyModel(nos_index)
        self.proxy_model.setSourceModel(self.summary_model)
        t.setModel(self.proxy_model)
        self.setup_summary_table_view(t, QHeaderView.ResizeToContents, True, 60)
        t.selectionModel().selectionChanged.connect(self.on_selection_changed)
        if self.summary_model.rowCount() > 0:
            t.selectRow(0)
            # first_index = self.summary_model.index(0, 0)
            # t.setCurrentIndex(first_index)
        t.setFocus()

    def setup_sector_summary_table(self):
        for sector, details in sector_details.items():
            rounded_list = [[sublist[0], "{m:0.0f}".format(m=sublist[1]), "{m:0.2f}%".format(m=sublist[2])] for sublist in details]
            filtered_list = [sublist for sublist in rounded_list if sublist[1] != '0']
            sorted_list = sorted(filtered_list, key=lambda x: x[1])
            result = []
            for item in sorted_list:
                ticker = item[0]
                for summary_entry in overall_summary:
                    if ticker == summary_entry[0]:
                        l = [summary_entry[5], summary_entry[8], summary_entry[4]]
                        item = item + l
                        result.append(item)
            s1=s2=s3=s4=s5=0
            for item in result:
                s1 += int(item[1])
                s2 += float(item[2].strip('%'))
                s3 += int(item[3])
                s4 += int(item[4])
                s5 += float(item[5].strip('%'))
            total_row = ['Total', s1, "{m:0.0f}%".format(m=s2), s3, s4 , "{m:0.0f}%".format(m=s5) ]
            result.append(total_row)

            sector_details[sector] = result

        merged_list = [[key] + value for key, value in sector_summary.items()]
        rounded_list = [[sublist[0], round(sublist[1]), sublist[2], sublist[3]] for sublist in merged_list]
        sorted_list = sorted(rounded_list, key=lambda x: x[1])
        sum_second_column = sum(sublist[1] for sublist in sorted_list)
        sorted_list.append(['Total', round(sum_second_column,2),'', '', ''])
        for sublist in sorted_list:
            r = round(sublist[1] / sum_second_column * 100)
            sublist[2] = f"{r}%"
        filtered_list = [sublist for sublist in sorted_list if sublist[2] != '0%']
        # pp.pprint( rounded_list)
        column_alignments = {0: Qt.AlignLeft, 1: Qt.AlignRight, 10: Qt.AlignLeft, 11: Qt.AlignLeft}
        sector_model = SummaryTableModel(filtered_list, ['Sector', 'Invested', '%', '#'], column_alignments, 'sector_summary', config_data)
        t = self.ui.sector_summary
        t.setObjectName("sector_table")
        t.setModel(sector_model)
        self.setup_summary_table_view(t, QHeaderView.ResizeToContents, True, 60)
        t.selectionModel().selectionChanged.connect(self.sector_selection_changed)
        if sector_model.rowCount() > 0:
            t.selectRow(0)

        with open(f"{config_data['output_path']}/sector_details.txt", 'w') as file:
            for item in filtered_list:
                line = item[0] +  ',' +  item[2].replace('%', '')
                file.write(line + '\n')



    def sector_selection_changed(self, selected):
        indexes = selected.indexes()
        if indexes:
            selected_index = indexes[0]
            m = self.ui.sector_summary.model()
            selected_ticker = m.data(selected_index, Qt.DisplayRole)
            # print(selected_ticker)
            data = sector_details.get(selected_ticker, None)
            if data is not None:
                model = SummaryTableModel(data, ['Ticker', 'Inv', '%', 'ann_b', 'ann_a', 'alloc'], {}, 'sector_details', config_data)
                t = self.ui.sector_details
                set_vertical_header_properties(t)
                t.setModel(model)

                # adjust_column_widths(t, 'calendar_details_table')


    def set_horizontal_header_properties(self, table_view, resize_mode, stretch_last_section, min_section_size=None):
        thh = table_view.horizontalHeader()
        thh.setSectionResizeMode(resize_mode)
        thh.setStretchLastSection(stretch_last_section)
        if min_section_size is not None:
            thh.setMinimumSectionSize(min_section_size)

    def setup_summary_table_view(self, table_view, resize_mode, stretch_last_section, min_section_size):
        set_vertical_header_properties(table_view)
        self.set_horizontal_header_properties(table_view, resize_mode, stretch_last_section, min_section_size)

    def setup_transaction_summary_table(self):
        t = self.ui.transaction_summary_table
        adjust_column_widths(t, 'transaction_summary_table')

    def setup_dividend_summary_table(self):
        t = self.ui.dividend_summary_table
        adjust_column_widths(t, 'dividend_summary_table')

    def fill_calendar(self, calendar_data, calendar_type):
        # print(calendar_data, calendar_header)
        calendar_model = SummaryTableModel(calendar_data, calendar_header, {}, 'calendar', config_data)
        table_view = self.ui.dividend_calendar if calendar_type == "dividend" else self.ui.investment_calendar
        table_view.setModel(calendar_model)
        self.setup_table_view(table_view)
        if calendar_type == "investment":
            table_view.selectionModel().selectionChanged.connect(self.on_investment_calendar_selection_changed)
        else:
            table_view.selectionModel().selectionChanged.connect(self.on_dividend_calendar_selection_changed)
            table_view.setFocus()
        # Select current month's row
        self.select_current_month(table_view, calendar_model)
        adjust_column_widths(table_view, 'calendar')

    def select_current_month(self, table_view, calendar_model):
        col_index = 0
        row_index = datetime.now().month - 1
        index = calendar_model.index(row_index, col_index)
        self.select_index(table_view, index)
    def setup_table_view(self, table_view):
        set_vertical_header_properties(table_view)
        table_view.resizeColumnsToContents()
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.scrollToBottom()
        table_view.setFocus()

    def select_index(self, table_view, index):
        # Create a selection model and set the selection
        selection_model = table_view.selectionModel()
        selection = QItemSelection(index, index)
        selection_model.select(selection, QItemSelectionModel.Select)
    def fill_dividend_calendar_after_tax(self):
        self.fill_calendar(cal_data_div_after_tax, "dividend")

    def toggle_before_after(self):
        tab = self.ui.tab_widget
        cur_index = tab.currentIndex()
        if cur_index == 1:
            if self.ui.after_tax_radio.isChecked():
                self.ui.before_tax_radio.setChecked(True)
            else:
                self.ui.after_tax_radio.setChecked(True)
            self.switch_before_after()
    def switch_before_after(self):
        if self.ui.before_tax_radio.isChecked():
            self.fill_dividend_calendar_before_tax()
        else:
            self.fill_dividend_calendar_after_tax()

    def fill_dividend_calendar_before_tax(self):
        self.fill_calendar(cal_data_div_before_tax, "dividend")

    def fill_investment_calendar(self):
        self.fill_calendar(cal_investment, "investment")


    def setup_shortcuts_and_connections(self):
        # @formatter:off
        key_function_mapping = [
            #[QtGui.QKeySequence.StandardKey.Find, self.reset_main_filter],
            [QtGui.QKeySequence.StandardKey.Cancel, self.reset_main_filter],
            #[QtCore.Qt.Key_F12, self.reset_main_filter],
            #[QtGui.QKeySequence("Space"), self.reset_main_filter],
            ##[QtGui.QKeySequence("+"), self.reset_main_filter],
            [QtGui.QKeySequence.StandardKey.Quit, self.close],
            #[QtGui.QKeySequence("Ctrl+R"), self.reload],
            [QtCore.Qt.Key_F2, self.search_all_columns],
            [QtCore.Qt.Key_F3, self.show_closed_positions_changed],
            #[QtCore.Qt.Key_F5, self.write_summary_to_file],
            [QtCore.Qt.Key_Tab, self.next_tab],
            [QtCore.Qt.Key_NumberSign, self.toggle_before_after],
        ]
        # @formatter:on

        for item in key_function_mapping:
            shortcut = QtWidgets.QShortcut(item[0], self)
            shortcut.activated.connect(item[1])

        self.ui.main_filter.returnPressed.connect(self.ui.summary_table.setFocus)
        self.ui.main_filter.textChanged.connect(self.filter_changed)
        self.ui.after_tax_radio.toggled.connect(self.switch_before_after)

    def reset_main_filter(self):
        tab_idx = self.ui.tab_widget.currentIndex()
        if tab_idx == 0:
            m_filter = self.ui.main_filter
        else:
            return
        if m_filter.hasFocus():
            m_filter.setText("")
        else:
            m_filter.setFocus()

    def search_all_columns(self):
        new_state = not self.ui.search_all_columns.isChecked()  # toggle
        self.ui.search_all_columns.setChecked(new_state)
        self.proxy_model.setFilterParams(self.ui.main_filter.text(), self.ui.show_closed_positions.isChecked(), new_state)

    def show_closed_positions_changed(self):
        new_state = not self.ui.show_closed_positions.isChecked() #toggle
        #print(new_state)
        self.ui.show_closed_positions.setChecked(new_state)
        self.proxy_model.setFilterParams(self.ui.main_filter.text(), new_state, self.ui.search_all_columns.isChecked())

    def filter_changed(self, new_filter):
        show_closed_positions = self.ui.show_closed_positions.isChecked()
        search_all_columns = self.ui.search_all_columns.isChecked()
        self.proxy_model.setFilterParams(new_filter, show_closed_positions, search_all_columns)
        self.ui.summary_table.selectRow(0)

    def next_tab(self):
        tab = self.ui.tab_widget
        cur_index = tab.currentIndex()
        if cur_index < len(tab) - 1:
            tab.setCurrentIndex(cur_index + 1)
        else:
            tab.setCurrentIndex(0)

    def on_dividend_calendar_selection_changed(self, selected):
        self.on_calendar_selection_changed(selected, "dividend")

    def on_investment_calendar_selection_changed(self, selected):
        self.on_calendar_selection_changed(selected, "investment")

    def on_calendar_selection_changed(self, selected, calendar_type):
        indexes = selected.indexes()
        if indexes:
            selected_index = indexes[0]
            if calendar_type == "dividend":
                m = self.ui.dividend_calendar.model()
            elif calendar_type == "investment":
                m = self.ui.investment_calendar.model()
            else:
                return

            horizontal_header_text = m.headerData(selected_index.column(), Qt.Horizontal)
            vertical_header_text = m.headerData(selected_index.row(), Qt.Vertical)
            #print("Clicked cell:", vertical_header_text, horizontal_header_text)
            formatted_month = month_dict.get(vertical_header_text)
            if formatted_month is None:
                self.ui.calendar_details_table.setModel(None)
                return
            ym = f"{horizontal_header_text}-{formatted_month}"
            #print(ym)  # Output: 2023-06
            self.ui.ym_label.setText(calendar_type.title() + ' ' + ym )
            self.update_calendar_details_table(ym, calendar_type)


    def update_calendar_details_table(self, ym, calendar_type):
        matching_data = None
        if calendar_type == "dividend":
            matching_data = get_received_dividends_by_month(ym)
            header = dividend_calendar_details_header
            for item in matching_data:
                item[4] = convert_and_format(item[4])
                item[5] = convert_and_format(item[5])
                item[6] = convert_and_format(item[6])
        elif calendar_type == "investment":
            matching_data = get_investments_by_month(ym)
            header = investment_calendar_details_header

        self.calendar_details_model = SummaryTableModel(matching_data, header, {}, 'calendar_details', config_data )
        t = self.ui.calendar_details_table
        t.setModel(self.calendar_details_model)
        adjust_column_widths(t, 'calendar_details_table')

    def on_selection_changed(self, selected):
        global selected_ticker

        indexes = selected.indexes()
        if indexes:
            selected_index = indexes[0]
            selected_ticker = self.proxy_model.data(selected_index, Qt.DisplayRole)
            #print("Selected Ticker:", selected_ticker)
            summary = transactions_by_ticker[selected_ticker]
            self.transaction_summary_model = SummaryTableModel(summary, transaction_summary_header, transaction_column_alignments, 'transaction_summary', config_data )
            t = self.ui.transaction_summary_table
            t.setModel(self.transaction_summary_model)
            adjust_column_widths(t, 'transaction_summary_table')

            summary = ticker_divs_aggregated_with_yield.get(selected_ticker)
            if summary is None or len(summary)==0:
                self.ui.dividend_summary_table.setModel(None)
            else:
                self.dividend_summary_model = SummaryTableModel(summary, dividend_summary_header, dividend_column_alignments, 'dividend_summary', config_data)
                t = self.ui.dividend_summary_table
                t.setModel(self.dividend_summary_model)
                adjust_column_widths(t, 'dividend_summary_table')

    def create_status_bar(self):
        self.ui.status_bar = self.statusBar()
        font = QtGui.QFont()
        label_colors = config_data.get("label_colors")
        self._label_ = []
        for i, color in enumerate(label_colors):
            label = QLabel(str(i))
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
            label.setFont(font)
            label.setStyleSheet(f"background-color: {label_colors[i]}")
            self._label_.append(label)
            self.ui.status_bar.addPermanentWidget(label, 1)

        f = self._label_[-1].font()
        f.setBold(True)
        self._label_[-1].setFont(f)

        count = invested = annual_div_b = annual_div_a = 0
        for inner_list in overall_summary:
            if inner_list[nos_index] != 0:
                count+= 1
                invested += inner_list[inv_index]
                annual_div_b += inner_list[annb_index]
                annual_div_a += inner_list[anna_index]
        div_a_plus = annual_div_a + 2000*.27 #no tax for first 2000

        self._label_[0].setText(f"Active#   {count}")
        self._label_[1].setText(f"Invested:   {round(invested)}")
        self._label_[2].setText("FwdAnnDivB:   {m:0.0f}".format(m=annual_div_b))
        self._label_[3].setText("YocB:   {m:0.2f}%".format(m=annual_div_b/invested*100))
        self._label_[4].setText("FwdDivB_M:   {m:0.0f}".format(m=annual_div_b/12))
        self._label_[5].setText("FwdAnnDivA:   {m:0.0f}".format(m=annual_div_a))
        self._label_[6].setText("FwdAnnDivA+:   {m:0.0f}".format(m=div_a_plus))
        self._label_[7].setText("YoCA+:   {m:0.2f}%".format(m=div_a_plus/invested*100))
        self._label_[8].setText("FwdDivA_M+:   {m:0.0f}".format(m=div_a_plus / 12))

    def start_external_process(self):
        self.p = QProcess()
        self.p.finished.connect(self.process_finished)

        env = QProcessEnvironment.systemEnvironment()
        env.insert('QT_QPA_PLATFORM', 'wayland')
        self.p.setProcessEnvironment(env)

        # Start the external process
        python_exe = config_data['python3_exe']

        script = 'gen_plot.sh'
        self.p.start('bash', [script])
        #self.p.waitForFinished()

    def process_finished(self):
        pixmap = QPixmap(f"{config_data['output_path']}/sector_graphs.png")
        self.ui.sector_graph.setPixmap(pixmap)
        self.ui.sector_graph.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(f"{config_data['output_path']}/div_graphs.png")
        self.ui.div_graph.setPixmap(pixmap)
        self.ui.div_graph.setAlignment(Qt.AlignCenter)
        self.p = None

#=================================================================================================


def adjust_column_widths(t, table_type):
    # Define min and max widths for different table types
    min_w, max_w = width_mapping.get(table_type, [50, 100])

    # Set up vertical header
    tvh = t.verticalHeader()
    tvh.setDefaultSectionSize(10)
    tvh.sectionResizeMode(QHeaderView.Fixed)

    # Set up horizontal header
    thh = t.horizontalHeader()
    if table_type == 'calendar':
        thh.setSectionResizeMode(QHeaderView.Fixed)
        for i in range(thh.count()):
            thh.resizeSection(i, 55)
        thh.resizeSection(0, 70)
        #print(table_type, '##################')
    else:
        thh.setSectionResizeMode(QHeaderView.ResizeToContents)
        thh.setStretchLastSection(True)
        thh.setMinimumSectionSize(min_w)
        thh.setMaximumSectionSize(max_w)
        # Scroll to bottom
        t.scrollToBottom()

if __name__ == "__main__":
    main_with_print()
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        * { font-family: Arial; font-size: 10pt;}
    """)
    window = MainWindow(overall_summary)
    window.show()
    sys.exit(app.exec_())