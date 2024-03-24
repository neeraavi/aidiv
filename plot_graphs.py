import math
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import seaborn as sns
from matplotlib.colors import to_rgba
from matplotlib.ticker import MultipleLocator

start_year = 2015
current_year = datetime.now().year
end_year = current_year + 1  # Add 1 to include data up to the current year


def contrast_color(color):
    return 'black'
    rgba_color = to_rgba(color)
    luminance = 0.2126 * rgba_color[0] + 0.7152 * rgba_color[1] + 0.0722 * rgba_color[2]
    return 'black' if luminance > 0.5 else 'white'
#----------------------------------------------------------------


def plot_progress(ax):
    with open('out/div_cal.txt', 'r') as file:
        lines = file.readlines()

    data = [line.strip().split(',') for line in lines]
    header = data[0]

    # Extracting data
    months = [row[0] for row in data[1:]]
    years_data = [[int(value) for value in row[1:]] for row in data[1:]]
    ## Transposing the data for easy plotting
    years_data_transposed = list(map(list, zip(*years_data)))
    # Reverse the order of years
    years_data_transposed.reverse()
    legend_labels = data[0][1:][::-1]

    x = range(len(months))
    bar_width = 0.08
    opacity = 0.8
    # Using a color palette from seaborn
    palette = sns.color_palette("rocket", len(years_data_transposed))
    # Modify the last color
    last_color = sns.color_palette(["#8dd3c7"])[0]  # Convert hexadecimal color to RGB
    palette[-1] =  last_color


    for i, year_data in enumerate(years_data_transposed):
        bars = ax.bar([p + i * bar_width for p in x], year_data, bar_width, alpha=opacity, color=palette[i],
                       label=legend_labels[i])
        for bar, height in zip(bars, year_data):
            if height >= 250:
                text_color = contrast_color(palette[i])
                # Add background color for label
                # bbox_props = dict(boxstyle="round,pad=0.3", fc=palette[i], ec="black", lw=0.5, alpha=0.7)
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height()+50, str(int(bar.get_height())),
                         ha='center', va='top', rotation=0, fontsize=6, color=text_color, bbox=None)

    ax.set_ylabel('Div_A')
    # plt.title('Dividends for each month')
    ax.set_title(f'Dividends for each month - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    ax.set_xticks([p + 5 * bar_width for p in x], months)
    ax.legend(ncol=5, loc='upper right', fontsize=8)
#----------------------------------------------------------------


def get_cumulative_list_from_file(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()

    # Parse the header row and header column
    header_row = lines[0].strip().split(',')[1:]
    header_col = [line.strip().split(',')[0] for line in lines[1:]]

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


#----------------------------------------------------------------
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

#----------------------------------------------------------------
def plot_cumulative_dividends(ax):
    dividend_data, ym_labels, div_sums = get_cumulative_list_from_file('out/div_cal.txt')
    cumulative_dividends, y_labels = clean_ym_labels(dividend_data, ym_labels)

    data_length = len(cumulative_dividends)
    x = np.arange(0, data_length, 1).tolist()
    ax.stackplot(x, cumulative_dividends, color='g', alpha=0.2)
    top_val = rounded_max_value = math.ceil(max(cumulative_dividends) / 5000) * 5000
    ax.set_ylim(bottom=0, top=top_val)
    ax.set_xlim(left=0)
    ax.tick_params(axis='y', labelcolor='g')
    extended = len(y_labels) + 2
    major_ticks = np.arange(0, extended, 12)
    minor_ticks = np.arange(0, extended, 1)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)
    ax.grid(which='major', color='g', linestyle='-', linewidth=1, alpha=0.5)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(MultipleLocator(3 / 1))
    ax.xaxis.set_minor_formatter(lambda x, pos: 'DSJM'[int(round(x)) % 4])
    ax.xaxis.set_major_formatter(lambda x, pos: round(x / 12 + start_year))
    ax.tick_params(axis='x', which='minor', labelsize=5)
    ax.grid(True, which='both', alpha=0.2)
    last = len(y_labels) - 1
    for i, v in enumerate(cumulative_dividends):
        if i % 12 == 0 or i == last:
            ax.text(i, v + 25, "%d" % v, ha="center", fontsize=6)
    return div_sums, y_labels

#----------------------------------------------------------------
def plot_annual_dividends(ax, div_sums, cleaned_ym):
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

    # Create the bar plot on ax
    bars = ax.bar(x_positions, annual_divs, color='green', alpha=0.5)
    # Add value annotations to the bars
    for bar, value in zip(bars, annual_divs):
        if value != 0:
            ax.text(bar.get_x() + bar.get_width() / 2, 12000, str(value), ha='right', va='bottom', fontsize=6, rotation=90)

#----------------------------------------------------------------
def plot_cumulative_transactions(ax):
    transaction_data, ym_labels, transactions_sums = get_cumulative_list_from_file('out/transactions_cal.txt')
    cumulative_transactions, cleaned_ym = clean_ym_labels(transaction_data, ym_labels)
    ax.plot(cumulative_transactions, color='r', alpha=0.2)
    ax.tick_params(axis='y', labelcolor='r')
    top_val = math.ceil(max(cumulative_transactions) / 5000) * 5000
    ax.set_ylim(bottom=0, top=top_val)
    ax.yaxis.tick_left()
    ax.yaxis.tick_right()
#----------------------------------------------------------------
def main():
    fig, (ax_stacked, ax_cumulative) = plt.subplots(2, figsize=(10, 4), tight_layout=True)
    fig.set_size_inches(11, 8.5)
    plot_progress(ax_stacked)
    annual_dividends, cleaned_ym = plot_cumulative_dividends(ax_cumulative)
    ax2 = ax_cumulative.twinx()  # instantiate a second axes that shares the same x-axis
    plot_cumulative_transactions(ax2)
    plot_annual_dividends(ax2, annual_dividends, cleaned_ym)

    plt.title(f'Cumulative - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    plt.savefig('out/div_graphs.png')
    #plt.show()
    plt.close()

    plot_sector_details()
#----------------------------------------------------------------

def plot_sector_details():
    with open("out/sector_details.txt", "r") as file:
        lines = file.readlines()
        data = [line.strip().split(",") for line in lines if line.strip() and "Total" not in line]

    # Separate sectors and percentages
    sectors, percentages = zip(*data)

    # Convert percentages to integers
    percentages = [int(p) for p in percentages]

    # Plotting
    plt.figure(figsize=(11, 5.5), tight_layout=True)
    bars = plt.bar(sectors, percentages, color='#308ca6', width=0.5)

    # Add percentage labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height-2, f'{height}%', ha='center', va='bottom', rotation=0, color='white')

    plt.xticks(rotation=20, ha='right')
    plt.title(f'Sector distribution - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    plt.savefig('out/sector_graphs.png')
    #plt.show()
    plt.close()
#----------------------------------------------------------------
main()