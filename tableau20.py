## http://www.colourlovers.com/palette/2975964/Tableau_20

## blue x2 - orange x2 ---------------------------
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
## green x2 - red x2 ------------------------------
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
for j in range(len(tableau20)):
    r, g, b = tableau20[j]
    tableau20[j] = (r / 255., g / 255., b / 255.)

for (i, (r,g,b)) in enumerate(tableau20):
     print '\\definecolor{color%d}{rgb}{%f,%f,%f}' % (i, r,g,b)

colors = tableau20

# For heat-map plots
# --------------------------------------------------
import matplotlib

# Which colors to pick ..
# compare with https://owncloud.mad-kow.de/s/psgMnvnKGyT3ac2
# a value of X equals colorX
C_TOP_IDX=7
C_BOTTOM_IDX=1

# http://matplotlib.org/api/colors_api.html?highlight=linearsegmentedcolormap#matplotlib.colors.LinearSegmentedColormap
def _generate_cmap(idx):
    # (x, y0, y1)
    # x is the starting value at which this color entry starts
    #     (until next higher entry's x' kicks in)
    # y .. y is the range where we are picking the color value from;
    #     it's linearly calculated from the next entries y value and ours
    return (
        (0.0, None, colors[C_BOTTOM_IDX][idx]),
        (0.5, 1.0, 1.0), # white in the middle
        (1.0, colors[C_TOP_IDX][idx], None)
        )
def _generate_cmap_2(idx):
    # (x, y0, y1)
    # x is the starting value at which this color entry starts
    #     (until next higher entry's x' kicks in)
    # y .. y is the range where we are picking the color value from;
    #     it's linearly calculated from the next entries y value and ours
    return (
        (0.0, None, 1.0),
        (0.6, colors[5][idx], colors[5][idx]), # white in the middle
        (1.0, colors[0][idx], None)
        )

cdict1 = {'red': _generate_cmap(0),
          'green': _generate_cmap(1),
          'blue': _generate_cmap(2),
}
cdict2 = {'red': _generate_cmap_2(0),
          'green': _generate_cmap_2(1),
          'blue': _generate_cmap_2(2),
}
tab1_cmap = matplotlib.colors.LinearSegmentedColormap('tab1_cmap', cdict1, 256)
tab2_cmap = matplotlib.colors.LinearSegmentedColormap('tab2_cmap', cdict2, 256)
