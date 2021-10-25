import pandas as pd

#level_line = 15
#sig = [10, 11, 12, 11, 10, 12, 18, 22, 24, 22, 18, 12, 10, 11, 10, 12, 12, 16, 18 , 22, 21, 20, 12, 16]
#start_frq = 1000
#stop_frq = 1200
#step_frq = 11.11111

def transmission_detect(frq_pwr_series, level_line):
    timestamp_lst_lst = []
    timestamp_lst = []
    timestamp_index = []
    level_line = 100
    for frq in det_df['start_frq']:
        num = int(((frq + 3125) - 159993750) / 3125)
        #print(num)
        for level_set, timestamp in zip(df['levels'], df['timestamp.$date']):
            if level_set[num] >= level_line:
                timestamp_lst.append(timestamp)
        if len(timestamp_lst) > 0:
            timestamp_lst_lst.append(timestamp_lst)
        timestamp_lst = []
    
#input levels i.e (-92,-94.5,-60,-62,-54,-62,-80,-93-95) and level i.e. -75
#output a list of levels above the level line and their position in the orginal levels list ie. [-60,-62,-54,-62] and [2,3,4,5]
def signal_detect(sig, level_line):
    count = 0
    sigs = []
    counts = []
    sig_array = []
    count_array = []
    for i in sig:
        if i < level_line:
            if len(sig_array) > 0:
                sigs.append(sig_array)
                counts.append(count_array)
                sig_array = []
                count_array = []
        if i >= level_line:
            sig_array.append(i)
            count_array.append(count)
        count = count + 1
    return sigs, counts

#sigs, counts = signal_detect(sig, level_line)

#print(sigs, counts)
#input start and step freq, sigs and counts from signal detect
#output detect_doc with start, stop frequency center frequency, bandwidth, power.

def create_detects(sigs, counts, start_frq, step_frq):
    pwrs = []
    bws = []
    start_frqs = []
    stop_frqs = []
    center_frqs = []
    t = 0
    for i in sigs:
        max_pwr = max(sigs[t])
        pwrs.append(max_pwr)
        t = t + 1
    t = 0
    for i in counts:
        #print(i[0], i[-1])
        start_frq_i = start_frq + (i[0] * step_frq)
        #print(start_frq, i[0], step_frq)
        stop_frq_i = start_frq + (i[-1] * step_frq)
        bw = stop_frq_i - start_frq_i
        center_frq = start_frq_i + (bw / 2)
        start_frqs.append(start_frq_i)
        stop_frqs.append(stop_frq_i)
        center_frqs.append(center_frq)
        bws.append(bw)

    det_doc = pd.DataFrame({'start_frq': start_frqs, 'stop_frq': stop_frqs, 'center_frq': center_frqs, 'bw': bws, 'pwr': pwrs})
    #det_doc = df.to_json(orient='records')
    return det_doc

#create_detects(sigs, counts, start_frq, step_frq)