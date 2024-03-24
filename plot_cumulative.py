import math

import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from matplotlib.ticker import MultipleLocator

start_year = 2015


def get_cumulative_list_from_file(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()

    # Parse the header row and header column
    header_row = lines[0].strip().split(',')[1:]
    header_col = [line.strip().split(',')[0] for line in lines[1:]]

    # Extract end year from current date
    current_year = datetime.now().year
    end_year = current_year + 1  # Add 1 to include data up to the current year

    # Create a dictionary to store the data
    data = {}
    sums = {year: 0 for year in range(2015, end_year)}
    for line in lines[1:]:
        items = line.strip().split(',')
        month = items[0]
        values = [int(value) for value in items[1:]]
        data[month] = dict(zip(header_row, values))
        for i, year in enumerate(range(current_year, 2015-1, -1)):
            sums[year] += int(items[i + 1])  # Add the corresponding value to the sum for the year

    # Extract the values and corresponding year-month labels in the desired order
    data_values = []
    year_month_labels = []
    for year in range(start_year, end_year):
        for month in header_col:
            data_values.append(data[month][str(year)])
            year_month_labels.append(f"{year}-{month}")

    # Print or use the desired_order list and year_month_labels list as needed
    print("Data Values:", data_values)
    print("Year-Month Labels:", year_month_labels)
    print("Sums:", sums)
    return data_values, year_month_labels, sums


def clean_ym_labels(dividends, year_month_labels):
    cleaned_year_month = []
    for index, item in enumerate(year_month_labels):
        year, month = item.split('-')
        if month == 'Jan':
            cleaned_year_month.append(year)
        elif month in ['Mar', 'Jun', 'Sep']:
            cleaned_year_month.append(month[0])
        else:
            cleaned_year_month.append('')
    print(cleaned_year_month)
    cumulative_values = []
    cumulative_sum = 0
    for value in dividends:
        cumulative_sum += value
        cumulative_values.append(cumulative_sum)
    print(cumulative_values)
    return cumulative_values, cleaned_year_month


dividend_data, ym_labels, div_sums = get_cumulative_list_from_file('out/div_cal.txt')
cumulative_dividends, cleaned_ym = clean_ym_labels(dividend_data, ym_labels)
transaction_data, ym_labels, transactions_sums = get_cumulative_list_from_file('out/transactions_cal.txt')
cumulative_transactions, _ = clean_ym_labels(transaction_data, ym_labels)

data_length = len(cumulative_dividends)
fig, ax1 = plt.subplots(1, figsize=(10, 4), tight_layout=True, sharex=True)

x = np.arange(0, data_length, 1).tolist()
ax1.stackplot(x, cumulative_dividends, color='g', alpha=0.2)
top_val = rounded_max_value = math.ceil(max(cumulative_dividends) / 5000) * 5000
ax1.set_ylim(bottom=0, top=top_val)
ax1.set_xlim(left=0)
ax1.tick_params(axis='y', labelcolor='g')
extended = len(cleaned_ym) + 2
major_ticks = np.arange(0, extended, 12)
minor_ticks = np.arange(0, extended, 1)
ax1.set_xticks(major_ticks)
ax1.set_xticks(minor_ticks, minor=True)
ax1.grid(which='major', color='g', linestyle='-', linewidth=1, alpha=0.5)
ax1.minorticks_on()
ax1.xaxis.set_minor_locator(MultipleLocator(3 / 1))
ax1.xaxis.set_minor_formatter(lambda x, pos: 'DSJM'[int(round(x)) % 4])
ax1.xaxis.set_major_formatter(lambda x, pos: round(x / 12 + start_year))
ax1.tick_params(axis='x', which='minor', labelsize=5)
ax1.grid(True, which='both', alpha=0.2)
last = len(cleaned_ym) - 1
for i, v in enumerate(cumulative_dividends):
    if i % 12 == 0 or i == last:
        ax1.text(i, v + 25, "%d" % v, ha="center", fontsize=6)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
#color = 'tab:red'
#ax2.set_ylabel('sin', color=color)  # we already handled the x-label with ax1
#ax2.plot(t, data2, color=color)
ax2.plot(cumulative_transactions, color='r', alpha=0.2)
ax2.tick_params(axis='y', labelcolor='r')
top_val = rounded_max_value = math.ceil(max(cumulative_transactions) / 5000) * 5000
ax2.set_ylim(bottom=0, top=top_val)
ax2.yaxis.tick_left()
ax1.yaxis.tick_right()

annual_divs = []
for label in cleaned_ym:
    # If label is a key in value_dictionary, append the corresponding value to new_list
    if label.isdigit() and int(label) in div_sums:
        annual_divs.append(div_sums[int(label)])
    # Otherwise, append 0
    else:
        annual_divs.append(0)

# Generate x positions for the bars
x_positions = range(len(cleaned_ym))

# Create the bar plot on ax2
bars = ax1.bar(x_positions, annual_divs, color='green', alpha=0.5)
# Add value annotations to the bars
for bar, value in zip(bars, annual_divs):
    if value != 0:
        ax2.text(bar.get_x() + bar.get_width()/2, 12000, str(value), ha='right', va='bottom', fontsize=6, rotation=90)


#plt.savefig(fname, bbox_inches="tight", dpi=96)
plt.title(f'Cumulative - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
plt.tight_layout()
plt.savefig('out/div_after_tax_cumulative.png')
#plt.show()
plt.close()
