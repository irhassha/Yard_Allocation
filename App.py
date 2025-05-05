import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors

# Load your Excel file here
# df = pd.read_excel("your_file.xlsx")
# Contoh kolom: ['Area', 'Row_Bay', 'Move', 'Carrier Out']

# Placeholder data buat demo
# Silakan ganti dengan df dari Excel
example_data = {
    'Area': ['A01', 'A01', 'A01', 'A02', 'A02', 'B01', 'B01', 'C01'],
    'Row_Bay': ['A01-01', 'A01-01', 'A01-01', 'A02-02', 'A02-02', 'B01-01', 'B01-01', 'C01-01'],
    'Move': ['Export', 'Transhipment', 'Import', 'Export', 'Import', 'Export', 'Import', 'Import'],
    'Carrier Out': ['MSC', 'HPL', 'Any', 'MSC', 'Any', 'ONE', 'Any', 'Any']
}
df = pd.DataFrame(example_data)

# Filter hanya Area yang ditentukan
areas_to_show = [f"{l}{i:02}" for l in ['A', 'B', 'C'] for i in range(1, 9)]
df = df[df['Area'].isin(areas_to_show)]

# Buat warna untuk tiap Carrier Out (selain Import yang abu-abu)
carrier_colors = {}
color_palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
color_index = 0

def get_color(move, carrier):
    global color_index
    if move == 'Import':
        return 'lightgrey'
    if carrier not in carrier_colors:
        carrier_colors[carrier] = color_palette[color_index % len(color_palette)]
        color_index += 1
    return carrier_colors[carrier]

# Siapkan grid layout untuk Area dan Row_Bay
grouped = df.groupby(['Area', 'Row_Bay'])

fig, ax = plt.subplots(figsize=(20, 10))
row_height = 1
block_width = 1

# Buat posisi per Area dan Row_Bay
area_order = areas_to_show
area_pos = {area: i for i, area in enumerate(area_order)}

rowbay_per_area = df.groupby('Area')['Row_Bay'].unique().to_dict()

for area in area_order:
    rowbays = sorted(set(rowbay_per_area.get(area, [])))
    for y_offset, rowbay in enumerate(rowbays):
        if (area, rowbay) not in grouped:
            continue
        stacks = grouped.get_group((area, rowbay))
        for i, row in enumerate(stacks.itertuples()):
            color = get_color(row._3, row._4)  # Move, Carrier Out
            ax.add_patch(
                mpatches.Rectangle(
                    (area_pos[area], y_offset + i * 0.2),
                    block_width, 0.2, facecolor=color, edgecolor='black')
            )
        ax.text(area_pos[area] + 0.5, y_offset + 0.3, rowbay,
                ha='center', va='bottom', fontsize=6)

# Set axes
ax.set_xlim(-0.5, len(area_order) - 0.5)
ax.set_ylim(0, 20)
ax.set_xticks([area_pos[a] + 0.5 for a in area_order])
ax.set_xticklabels(area_order, rotation=90)
ax.set_yticks([])
ax.set_title('Stacked Block View per Row/Bay by Area (EXE)')

# Buat legend
legend_handles = [
    mpatches.Patch(color='lightgrey', label='Import')
] + [
    mpatches.Patch(color=color, label=carrier)
    for carrier, color in carrier_colors.items()
]
ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.01, 1.0))

plt.tight_layout()
plt.show()
