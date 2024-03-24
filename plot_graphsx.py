from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

def contrast_color(color):
    #Determine the contrasting color (black or white) for the given color.
    # Convert color to RGBA if it's not already in that format
    rgba_color = to_rgba(color)
    luminance = 0.2126 * rgba_color[0] + 0.7152 * rgba_color[1] + 0.0722 * rgba_color[2]
    return 'black' if luminance > 0.5 else 'white'

# Read data from file
with open('out/div_cal.txt', 'r') as file:
    lines = file.readlines()

# Process the data
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

# Plotting
plt.figure(figsize=(10, 4))
x = range(len(months))
bar_width = 0.08
opacity = 0.8
# Using a color palette from seaborn
palette = sns.color_palette("bright", len(years_data_transposed))


for i, year_data in enumerate(years_data_transposed):
    bars = plt.bar([p + i * bar_width for p in x], year_data, bar_width, alpha=opacity, color=palette[i], label=legend_labels[i])
    for bar, height in zip(bars, year_data):
        if height >= 100:
            text_color = contrast_color(palette[i])
            # Add background color for label
            #bbox_props = dict(boxstyle="round,pad=0.3", fc=palette[i], ec="black", lw=0.5, alpha=0.7)
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(int(bar.get_height())),
                     ha='center', va='top', rotation=90, fontsize=6, color=text_color, bbox=None)

#plt.yscale('log')
#plt.xlabel('Month')
plt.ylabel('Div_A')
#plt.title('Dividends for each month')
plt.title(f'Dividends for each month - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
plt.xticks([p + 5 * bar_width for p in x], months)
plt.legend(ncol=5, loc='upper right', fontsize=8)
plt.tight_layout()
# Save the plot to a file
plt.savefig('out/div_progress.png')
plt.close()
#plt.show()

