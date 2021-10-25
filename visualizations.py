import numpy as np
import sig_detect as sd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib as mpl
from matplotlib.colors import ListedColormap
from datetime import datetime

def mk_offs(start_frq, incr, num, loop_num):
    offs = []
    t = 0
    while t < loop_num:
        off=[]
        i = 0
        while i < num:
            off.append(start_frq + (i * incr))
            i = i + 1
        t = t + 1
        offs.append(off)
    return offs

def stitch_scans(df):
    start_frqs = df['frqfirststep'].unique()
    df.sort_values(by=['frqfirststep'])
    off_arr = []
    levels_arr = []
    for start_frq in start_frqs:
        num_traces = len(df[df.frqfirststep == start_frq])
        num_datapoints = len(df['levels'][0])
        incr = df['step_frq'][0]
        offs = mk_offs(start_frq, incr, num_datapoints, num_traces)
        off_arr.append(offs)
        levels_arr.append(df[df.frqfirststep == start_frq]['levels'].tolist())
    levels_arr = np.array(levels_arr)
    levels_arr = levels_arr.flatten()
    print(len(levels_arr), len(off_arr))
    off_arr = np.array(off_arr)
    off_arr = off_arr.flatten()
    return off_arr, levels_arr

def spectrum_histogram(start_frq, step_frq, start_time, stop_time, levels, max_line='no', mean_line='no', min_line='no', detects='yes'):
    
    num_datapoints = len(levels[0])
    num = int(num_datapoints)
    num_traces = len(levels)
    incr = step_frq
    stop_frq = start_frq + (num_datapoints * incr)
    y = np.array(levels)
    maximum = np.max(y, axis=0)
    minimum = np.min(y, axis=0)
    mean = np.mean(y, axis=0) 
    y = y.flatten()
    level_line = 45
    sigs, counts = sd.signal_detect(maximum, level_line)
    det_df = sd.create_detects(sigs, counts, start_frq, incr)
    
    x = np.array(mk_offs(start_frq, incr, num_datapoints, num_traces))
    x = x.flatten()

    xmin = x.min()
    xmax = x.max()
    ymin = y.min()
    ymax = y.max()
    print(xmin, xmax, ymin, ymax)

    theme_color = "Spectral_r"
    top_bgcolor = "black"
    bottom_bgcolor = 'silver'
    print(num/100)
    print((ymax - ymin)/10)
    fig = plt.figure(figsize =((num/100), (ymax - ymin)/100), dpi=300)
    #fig, ax = plt.subplots(((num/100), (ymax-ymin/(-10))), dpi=100)
    #fig = plt.figure()
    #fig = plt.figure(figsize=(20, 3), dpi=300)

    my_cmap = mpl.cm.get_cmap(f'{theme_color}').copy()
    #my_cmap = ListedColormap(["gray", "red", "yellow", "lime", "blue", "purple"])
    #my_cmap.set_bad(color='silver')

    ybin = int(ymax - ymin)
    print(ymax, ymin, ybin)
    xbin = int((xmax - xmin)/incr)
    print(f'xbin, ybin: {xbin, ybin}')

    bins = ((num-1),int((ymax-ymin) - 1))
    #bins = (3198,300)
    vmax = ((num * num_traces) / 200000 )
    
    h, xedges, yedges = np.histogram2d(x, y, bins=bins)
    #h, xedges, yedges = np.histogram2d(x, y, bins=bins)
    pcm = plt.pcolormesh(xedges, yedges, h.T, cmap=my_cmap, norm=mcolors.Normalize(vmax=vmax), rasterized=True)
    plt.fill_between(x[0:num], maximum, ymax, color=f'{top_bgcolor}', alpha=0.8, linewidth=0.05)
    plt.fill_between(x[0:num], minimum, ymin, color=f'{bottom_bgcolor}', alpha=0.8, linewidth=0.05)
    
    #for start_freq, stop_freq in zip(det_df['start_frq'], det_df['stop_frq']):
    #    plt.axvspan(start_freq, stop_freq, alpha=0.30, facecolor='Orange')
    
    plt.axhline(level_line, linestyle='--', color='white', linewidth=0.75)

    #plt.fill_between(x[0:num], maximum, mean, color='orange', alpha=0.5)
    #plt.fill_between(x[0:num], minimum, mean, color='white', alpha=0.5)

    #fig.set_title(f'{start_frq/1000000}MHz - {stop_frq/1000000}MHz, {start_time} - {stop_time}')
    #max = plt.plot(x[0:num],maximum, color='orange', alpha=1, linewidth=1, markersize=1)
    #min = plt.plot(x[0:num],minimum, color='lightblue', alpha=1, linewidth=0.05, markersize=0.05)
    #mean = plt.plot(x[0:num],mean, color='black', linewidth=0.75, markersize=0.75)
    print(f'start_stop = {start_frq, stop_frq}')
    cb = plt.colorbar()
    cb.set_label("density")
    print(start_time, stop_time)
    start_time = datetime.fromtimestamp(start_time/1000)
    stop_time = datetime.fromtimestamp(stop_time/1000)
    plt.title(f'{start_time} - {stop_time}, {start_frq/1000000}MHz - {stop_frq/1000000}MHz, RBW - {incr/1000} kHz, Number of Traces: {num_traces}')

    plt.savefig(f"{start_frq/1000000}_output.jpg")
    return(det_df)
    #return(fig)

def spectrum_waterfall(levels):
    fig = plt.figure(figsize=(20, 7), dpi=300)
    im = plt.imshow(levels, cmap='Spectral_r')
    plt.savefig(f"waterfall.jpg")
    plt.show()