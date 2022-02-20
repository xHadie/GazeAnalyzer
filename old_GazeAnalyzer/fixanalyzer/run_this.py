import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import EyeAnalyzer
from read_data import read_data

screenWidth = 1024
screenHeight = 768
deg_per_pix = np.arctan(((23 * 2.54 ) /5*4)/2 / 60) / (2*np.pi) * 360 / 512
fs = 300 # sampling rate

(raw_x, raw_y, raw_t) = read_data('smile4_WS.csv', screenHeight, screenWidth)

ea = EyeAnalyzer.EyeAnalyzer(raw_x * deg_per_pix, raw_y * deg_per_pix, raw_t, cut_f = 30, fs = fs,
                             saccade_thre = 30, saccade_min_dur = 0.015, fix_thre = 1, fix_min_dur = 0.1,
                             blink_detect_min_dur = 0.015, blink_rm_thre = 30, blink_rm_min_dur = 0.015)
(sac_start, sac_end) = ea.get_saccade()
(blink_start, blink_end) = ea.get_blink()
(fix_start, fix_end) = ea.get_fixation()

to_print = ["sac_start", "sac_end", "blink_start", "blink_end", "fix_start", "fix_end"]
for s in to_print:
    print(f"{s} : {eval(s)}")



def get_fixation_average_position(fix_start,fix_end,times,positions):
    n = 0
    sum = 0

    i = 0
    while fix_start > times[i]:
        i = i + 1

    while fix_end >= times[i]:
        n = n + 1
        sum = sum + positions[i]
        i = i +1
        if i == len(times):
            break

    return sum / n

plt.figure(1)
plt.scatter(raw_t, raw_x, marker='.')
plt.scatter(raw_t, raw_y, marker='.')
plt.legend(['x', 'y'])



plt.figure(2)
plt.scatter(ea.t_trim, ea.x_trim, marker='.')
plt.scatter(ea.t_trim, ea.y_trim, marker='.')
plt.legend(['x', 'y'])

# FIXATION:
for i in range(len(fix_start)):
    plt.axvline(x=fix_start[i], color='red', linestyle='-')
    plt.text(fix_start[i], 20, 'eyes', rotation=90)
    print("PRE GET AV")
    av_x = get_fixation_average_position(fix_start[i],fix_end[i],raw_t,raw_x)
    av_y = get_fixation_average_position(fix_start[i],fix_end[i],raw_t,raw_y)

    print("x: " + str(av_x))
    print("y: " + str(av_y))

for i in range(len(sac_start)):
    plt.axvline(x=sac_start[i], color='black', linestyle='--')
plt.show()