import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

class EyeAnalyzer:

    def __init__(self, x, y, t, cut_f, fs, saccade_thre = 30, saccade_min_dur = 0.015, fix_thre = 30, fix_min_dur = 0.1,
    blink_detect_min_dur = 0.015, blink_rm_thre = 30, blink_rm_min_dur = 0.015):
        '''
        x, y : eye position (arbitrary unit)
        t : second

        cut_f : cut-off frequency
        fs : sampling rate
        saccade_thre : thredhold eye velocity for detecting saccades
        saccade_min_dur : minimum duration to be judged as a saccade
        fix_thre : maximum eye displacement from the start of a fixation
        fix_min_dure : minimum duration for fixation
        blink_detect_min_dure : minimum duration for blink
        blink_rm_thre : see below
        blink_rm_min_dur : see below

        blinkの検出方法
        ・まずデータの欠損をblinkとして検出する．
        ・検出された各blinkの前後の時間の不安定なデータも取り除きたい．そのために以下を行う．
        ・各blinkの終わりから後ろに向かって見ていって，速度が一定時間（blink_rm_min_dure）の間
          指定速度(blink_rm_thre)以下になるまで削除する．
        ・各blinkの始まりから前に向かって見ていって，同様に削除する．

        '''

        self.x_raw = x
        self.y_raw = y
        self.t_raw = t
        self.cut_f = cut_f
        self.fs = fs
        self.saccade_thre = saccade_thre
        self.saccade_min_dur = saccade_min_dur
        self.fix_thre = fix_thre
        self.fix_min_dur = fix_min_dur
        self.blink_detect_min_dur = blink_detect_min_dur
        self.blink_rm_thre = blink_rm_thre
        self.blink_rm_min_dur = blink_rm_min_dur

        # filtered signal
        self.x_filt, self.y_filt, self.t_filt = self.get_filtered()
        self.x_vel = np.diff(self.x_filt) / np.diff(self.t_filt)
        self.y_vel = np.diff(self.y_filt) / np.diff(self.t_filt)
        self.t_vel = self.t_filt[1:]

        # filtered & trimmed signal
        self.x_trim, self.y_trim, self.t_trim = self.remove_blink()
        self.x_trim_vel = np.diff(self.x_trim) / np.diff(self.t_trim)
        self.y_trim_vel = np.diff(self.y_trim) / np.diff(self.t_trim)
        self.t_trim_vel = self.t_trim[1:]


    def get_filtered(self):
        x2, y2, t2 = self.remove_nan(self.x_raw, self.y_raw, self.t_raw)
        nyq = 0.5 * self.fs
        cut = self.cut_f / nyq
        b, a = butter(2, cut)
        x_filt = filtfilt(b, a, x2)
        y_filt = filtfilt(b, a, y2)

        return (x_filt, y_filt, t2)

    def get_saccade(self):
        '''
        return : (start_sec_list, end_sec_list)
        '''
        
        abs_vel = np.sqrt(self.x_trim_vel**2 + self.y_trim_vel**2)

        return _get_helper(abs_vel, abs_vel, self.t_trim_vel, self.saccade_thre, self.saccade_min_dur,
         lambda x, y, thre, tmpx, tmpy: x > thre)


    def get_fixation(self):

        return _get_helper(self.x_trim, self.y_trim, self.t_trim, self.fix_thre, self.fix_min_dur,
         lambda x, y, thre, tmpx, tmpy: np.sqrt((x-tmpx)**2 + (y-tmpy)**2) < thre)


    def get_blink(self):

        xy_nan = np.logical_or(np.isnan(self.x_raw), np.isnan(self.y_raw))
        return _get_helper(xy_nan, xy_nan, self.t_raw, 0, self.blink_detect_min_dur, lambda x, y, thre, tmpx, tmpy: x)


    def remove_blink(self):
        '''
        少なくともmin_duration以上thresholdより速度が低くなるまで取り除く.
        '''
        
        blink = self.get_blink()
        abs_vel = np.sqrt(self.x_vel**2 + self.y_vel**2)

        remove_ind = []
        for i_blk in range(len(blink[0])):
            for d in [1, -1]: # 1は逆方向，-1は順方向に見ていく．
                blk = blink[0] if d==1 else blink[1]
                raw_ind = np.where(self.t_raw == blk[i_blk])[0]
                
                #print(f"i_blk: {i_blk}, d: {d}, raw_ind : {raw_ind}")
                if raw_ind - d < 0 or raw_ind - d >= len(self.t_raw):
                    continue

                vel_ind = np.where(self.t_vel == self.t_raw[raw_ind - d])[0]
                #print(f"vel_ind : {vel_ind}, vel : {abs_vel[vel_ind]}")
                if len(vel_ind) > 0:
                    vel_ind = vel_ind[0]
                else:
                    continue

                current_ind = vel_ind
                last_ind = vel_ind # 最後にthreshold超えていたind
                while True:

                    if abs_vel[current_ind] > self.blink_rm_thre:
                        last_ind = current_ind
                    else:
                        if np.abs(self.t_vel[current_ind] - self.t_vel[last_ind]) > self.blink_rm_min_dur:
                            break

                    current_ind -= d
                    if current_ind < 0 or current_ind >= len(self.t_vel):
                        break
                #print(list(range(vel_ind, last_ind - d, -d)))
                remove_ind.extend(list(range(vel_ind, last_ind - d, -d)))

        remove_ind = np.sort(np.unique(np.array(remove_ind)))
        if len(remove_ind)  == 0:
            return (self.x_filt, self.y_filt, self.t_filt)
            
        t_trim = np.delete(self.t_filt, remove_ind)
        x_trim = np.delete(self.x_filt, remove_ind)
        y_trim = np.delete(self.y_filt, remove_ind)

        return (x_trim, y_trim, t_trim)


    def remove_nan(self, x, y, t):

        ind = np.logical_not(np.logical_or(np.isnan(x), np.isnan(y)))
        return (x[ind], y[ind], t[ind])


def _get_helper(x, y, t, value, min_duration, func):
    '''
    helper function
    value : 例えばthresholdなど．
    min_duration : 最低持続時間
    func : func(x, y, value, tmpx, tmpy)の形でとり，True/Falseを返す関数．yは必要なければ適当に指定．
            例えばthreshold以上のところを得るのなら，x > value を返す関数．
            tmpx, tmpyはfixation用に必要. fixationの初期位置．

    return : (start_index_list, end_index_list)
    '''

    flg_thre = False
    flg_sac = False

    start_ind = []
    end_ind = []

    tmp_start = 0
    tmp_x = 0 # fixation用の変数．始まった時の位置
    tmp_y = 0

    for i_t in range(len(t)):
    
        if func(x[i_t], y[i_t], value, tmp_x, tmp_y):
            if flg_sac:
                continue

            if not flg_thre:
                flg_thre = True
                tmp_start = i_t
                tmp_x = x[i_t]
                tmp_y = y[i_t]

            if t[i_t] - t[tmp_start] > min_duration and not flg_sac:
                flg_sac = True
                flg_thre = False
                start_ind.append(tmp_start)
                tmp_start = 0

        else:
            if flg_thre:
                flg_thre = False
                tmp_start = 0

            if flg_sac:
                flg_sac = False
                end_ind.append(i_t - 1)
            
            tmp_x = x[i_t]
            tmp_y = y[i_t]

    if flg_sac:
        end_ind.append(len(x) - 1)
    
    start_ind = np.array(start_ind)
    end_ind = np.array(end_ind)

    start_t = t[start_ind] if len(start_ind) > 0 else np.array([])
    end_t = t[end_ind] if len(end_ind) > 0 else np.array([])
    
    return (start_t, end_t)

