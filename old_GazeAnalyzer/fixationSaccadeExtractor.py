import os
from fixanalyzer import read_data
from fixanalyzer import EyeAnalyzer
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from aoiCalculator import get_aoi_for_gaze_point
import yawningExperiment as exp
from subject import Subject
from sessionData import SessionData
from StimulusData import StimulusData
from aoiCalculator import get_aoi_for_session_and_id
import sys
import math

deg_per_pix = np.arctan(((23 * 2.54) / 5 * 4) / 2 / 60) / (2 * np.pi) * 360 / 512
fs = 300  # sampling rate



def create_saccade_csvs(subjects):
    full_num_sac_df = None
    full_dis_sac_df = None

    n_iter = len(subjects) * 3 * 12
    progress_index = 0
    progress_subject = 0
    subject_n = len(subjects)
    print("Generating SACCADE_COUNT.csv and SACCADE_DISTANCE.csv....")
    sys.stdout.progressBar("Generating SACCADE_COUNT.csv and SACCADE_DISTANCE.csv", progress_index, n_iter)

    for subject in subjects:
        total_trials_count = 0
        total_excluded_trials_count = 0
        progress_subject = progress_subject + 1
        if subject.nationality == "JP" or subject.nationality == "WS":
            continue
        subject: Subject = subject
        num_sac_subject_column_dic = {}
        dis_sac_subject_column_dic = {}

        subject.loadSessionData()
        for session in subject.sessionData:
            session_trials_count = 0
            session_excluded_trials_count = 0
            session_data: SessionData = subject.sessionData[session]

            num_intensities = {}
            dis_intensities = {}

            for intensity in [1, 2, 3, 4]:
                num_intensities[intensity] = {}
                dis_intensities[intensity] = {}

                num_intensities[intensity]["data"] = 0
                dis_intensities[intensity]["data"] = 0

                num_intensities[intensity]["n_trials"] = 0
                dis_intensities[intensity]["n_trials"] = 0

            for image_data in session_data.stimulusData.values():
                progress_index = progress_index + 1
                image_data: StimulusData = image_data
                image_id = image_data.image_id
                intensity_index = ((image_id - 1) % exp.NUMBER_OF_INTENSITIES) + 1

                num_saccade_image = 0
                dis_saccade_image = 0

                subject.loadSessionData()

                fix_index_name = []
                last_time = 0

                trial_end = []

                trial_list = image_data.trials
                for trial in trial_list:
                    total_trials_count = total_trials_count + 1
                    session_trials_count = session_trials_count + 1
                    if trial.excluded():
                        total_excluded_trials_count = total_excluded_trials_count + 1
                        session_excluded_trials_count = session_excluded_trials_count + 1

                        key = "%s%s_%s" % (session, image_id, trial.appearance_index)
                        num_sac_subject_column_dic[key] = "excluded"
                        dis_sac_subject_column_dic[key] = "excluded"
                    else:
                        num_intensities[intensity_index]["n_trials"] = num_intensities[intensity_index]["n_trials"] + 1
                        dis_intensities[intensity_index]["n_trials"] = dis_intensities[intensity_index]["n_trials"] + 1
                        (raw_x, raw_y, raw_t) = read_data.read_data_other(trial.get_trial_file_path(),
                                                                          exp.SCREEN_HEIGHT,
                                                                          exp.STIMULUS_WIDTH)

                        ea = EyeAnalyzer.EyeAnalyzer(raw_x * deg_per_pix, raw_y * deg_per_pix, raw_t, cut_f=30, fs=fs,
                                                     saccade_thre=30, saccade_min_dur=0.015, fix_thre=1,
                                                     fix_min_dur=0.1,
                                                     blink_detect_min_dur=0.015, blink_rm_thre=30,
                                                     blink_rm_min_dur=0.015)

                        (sac_start, sac_end) = ea.get_saccade()
                        (blink_start, blink_end) = ea.get_blink()
                        (fix_start, fix_end) = ea.get_fixation()
                        #fix_list = [f + last_time for f in fix_start]
                        #fix_start_all.extend(fix_list)

                        #sac_list = [s + last_time for s in sac_start]
                        #sac_start_all.extend(sac_list)

                        #x_trim_all.extend(ea.x_trim)
                        #y_trim_all.extend(ea.y_trim)

                        time_list = [x + last_time for x in ea.t_trim]
                        last_time = max(time_list)
                        trial_end.append(last_time)
                        #t_trim_all.extend(time_list)

                        # Get fixation location:
                        sum_of_sac_count = 0
                        sum_of_sac_distance = 0
                        for i in range(len(sac_start)):
                            saccade_distance = get_saccade_distance(sac_start[i], sac_end[i], raw_t, raw_x, raw_y)
                            sum_of_sac_count = sum_of_sac_count + 1
                            sum_of_sac_distance = sum_of_sac_distance + saccade_distance




                        # Add trial data to overall subject-data:
                        key = "%s%s_%s" % (session, image_id, trial.appearance_index)
                        num_sac_subject_column_dic[key] = sum_of_sac_count
                        num_saccade_image = num_saccade_image + sum_of_sac_count

                        # Intensities:
                        num_intensities[intensity_index]["data"] = num_intensities[intensity_index]["data"] + sum_of_sac_count

                        if sum_of_sac_distance == 0:
                            dis_sac_subject_column_dic[key] = 0
                        else:
                            avg_distance = sum_of_sac_distance / sum_of_sac_count
                            dis_sac_subject_column_dic[key] = avg_distance
                            dis_saccade_image = dis_saccade_image + avg_distance
                            # Intensities:
                            dis_intensities[intensity_index]["data"] = dis_intensities[intensity_index]["data"] + avg_distance

                # Image means:
                mean_key = "%s%s_mean" % (session, image_id)
                valid_trials_n = len(image_data.get_valid_trials())
                if valid_trials_n == 0:
                    num_sac_subject_column_dic[mean_key] = 0
                    dis_sac_subject_column_dic[mean_key] = 0
                else:
                    num_sac_subject_column_dic[mean_key] = num_saccade_image / valid_trials_n
                    dis_sac_subject_column_dic[mean_key] = dis_saccade_image / valid_trials_n


                sys.stdout.progressBar("[Excluded %s/%s] for %s/%s (%s - %s_%s)" % (
                    exp.EXCLUDED_TRIALS, exp.VALID_TRIALS + exp.EXCLUDED_TRIALS, progress_subject, subject_n,
                    subject.initials, session, image_id), progress_index, n_iter)


            for intensity in [1, 2, 3, 4]:
                mean_key = "%s_intensity_%s_mean" % (session, intensity)
                valid_trials_n = num_intensities[intensity]["n_trials"]
                if valid_trials_n == 0:
                    num_sac_subject_column_dic[mean_key] = 0
                    dis_sac_subject_column_dic[mean_key] = 0
                else:
                    num_sac_subject_column_dic[mean_key] = num_intensities[intensity]["data"] / valid_trials_n
                    dis_sac_subject_column_dic[mean_key] = dis_intensities[intensity]["data"] / valid_trials_n

            # Image trials and exclusion for session:
            session_n_key = "%s_n_trials" % session
            session_excluded_key = "%s_excluded_trials" % session
            session_excluded_ration_key = ("%s_exclusion_ratio_" % session) + "_%"

            for dic in [num_sac_subject_column_dic, dis_sac_subject_column_dic]:
                dic[session_n_key] = session_trials_count
                dic[session_excluded_key] = session_excluded_trials_count
                dic[session_excluded_ration_key] = (session_excluded_trials_count / session_trials_count) * 100


        for cond in ["smile","angry","yawn"]:
            mean_of_intensity_key = "%s_intensities_mean" % (cond)
            num_sum = 0
            dis_sum = 0
            for intensity in [1, 2, 3, 4]:
                intensity_mean_key = "%s_intensity_%s_mean" % (cond, intensity)

                num_sum = num_sum + num_sac_subject_column_dic[intensity_mean_key]
                dis_sum = dis_sum + dis_sac_subject_column_dic[intensity_mean_key]

            num_sac_subject_column_dic[mean_of_intensity_key] = num_sum / 4
            dis_sac_subject_column_dic[mean_of_intensity_key] = dis_sum / 4

        # Image trials and exclusion for subject:
        subj_n_key = "n_trials"
        subj_excluded_key = "excluded_trials"
        subj_exlcuded_ration_key = "exclusion_ratio_%"

        for dic in [num_sac_subject_column_dic, dis_sac_subject_column_dic]:
            dic[subj_n_key] = total_trials_count
            dic[subj_excluded_key] = total_excluded_trials_count
            dic[subj_exlcuded_ration_key] = (total_excluded_trials_count / total_trials_count) * 100

        sac_num_series = pd.Series(num_sac_subject_column_dic)
        sac_dis_series = pd.Series(dis_sac_subject_column_dic)
        if full_num_sac_df is None:
            full_num_sac_df = pd.DataFrame(index=sac_num_series.index)
            full_dis_sac_df = pd.DataFrame(index=sac_dis_series.index)

        full_num_sac_df[subject.initials] = sac_num_series.values
        full_dis_sac_df[subject.initials] = sac_dis_series.values


    full_num_sac_df.to_csv(exp.paths["RESULT_DIR"] + "all/SACCADE_COUNT_HK_AS.csv", index=True)
    full_dis_sac_df.to_csv(exp.paths["RESULT_DIR"] + "all/SACCADE_DISTANCE_HK_AS.csv", index=True)



def plot_fixation_images(subjects):
    face_regions = ["left_eye", "right_eye", "between_eyes", "nose", "mouth", "other_face",
                    "out_of_face", "out_of_image"]
    full_num_fix_df = None
    full_dur_fix_df = None

    n_iter = len(subjects) * 3 * 12
    progress_index = 0
    progress_subject = 0
    subject_n = len(subjects)
    print("Generating FIXATION_COUNT.csv and FIXATION_DURATION.csv....")
    sys.stdout.progressBar("Generating FIXATION_COUNT.csv and FIXATION_DURATION.csv", progress_index, n_iter)

    for subject in subjects:
        total_trials_count = 0
        total_excluded_trials_count = 0
        progress_subject = progress_subject + 1
        if subject.nationality == "JP" or subject.nationality == "WS":
            continue
        subject: Subject = subject
        num_fix_subject_column_dic = {}
        dur_fix_subject_column_dic = {}

        subject.loadSessionData()
        for session in subject.sessionData:
            session_trials_count = 0
            session_excluded_trials_count = 0
            session_data: SessionData = subject.sessionData[session]

            num_intensities = {}
            dur_intensities = {}
            for intensity in [1, 2, 3, 4]:
                num_intensities[intensity] = {}
                dur_intensities[intensity] = {}
                for region in face_regions:
                    # [0] = sum, [1] = n
                    num_intensities[intensity][region] = 0
                    dur_intensities[intensity][region] = 0

                    num_intensities[intensity]["n_trials"] = 0
                    dur_intensities[intensity]["n_trials"] = 0

            for image_data in session_data.stimulusData.values():
                progress_index = progress_index + 1
                image_data: StimulusData = image_data
                image_id = image_data.image_id
                intensity_index = ((image_id - 1) % exp.NUMBER_OF_INTENSITIES) + 1

                num_fixation_dic_image = {"left_eye": 0, "right_eye": 0, "between_eyes": 0,
                                          "nose": 0, "mouth": 0,
                                          "other_face": 0, "out_of_face": 0, "out_of_image": 0}

                dur_fixation_dic_image = num_fixation_dic_image.copy()

                subject.loadSessionData()

                fix_start_all = []
                sac_start_all = []

                t_trim_all = []
                x_trim_all = []
                y_trim_all = []
                fix_index_name = []
                last_time = 0

                trial_end = []

                trial_list = image_data.trials
                for trial in trial_list:
                    total_trials_count = total_trials_count + 1
                    session_trials_count = session_trials_count + 1
                    if trial.excluded():
                        total_excluded_trials_count = total_excluded_trials_count + 1
                        session_excluded_trials_count = session_excluded_trials_count + 1

                        for region in face_regions:
                            key = "%s%s_%s_%s" % (session, image_id, trial.appearance_index, region)
                            num_fix_subject_column_dic[key] = "excluded"
                            dur_fix_subject_column_dic[key] = "excluded"
                    else:
                        num_fixation_dic_trial = {"left_eye": 0, "right_eye": 0,
                                                  "between_eyes": 0, "nose": 0,
                                                  "mouth": 0,
                                                  "other_face": 0, "out_of_face": 0,
                                                  "out_of_image": 0}
                        dur_fixation_dic_trial = num_fixation_dic_trial.copy()

                        (raw_x, raw_y, raw_t) = read_data.read_data_other(trial.get_trial_file_path(),
                                                                          exp.SCREEN_HEIGHT,
                                                                          exp.STIMULUS_WIDTH)

                        ea = EyeAnalyzer.EyeAnalyzer(raw_x * deg_per_pix, raw_y * deg_per_pix, raw_t, cut_f=30, fs=fs,
                                                     saccade_thre=30, saccade_min_dur=0.015, fix_thre=1,
                                                     fix_min_dur=0.1,
                                                     blink_detect_min_dur=0.015, blink_rm_thre=30,
                                                     blink_rm_min_dur=0.015)
                        (sac_start, sac_end) = ea.get_saccade()
                        (blink_start, blink_end) = ea.get_blink()
                        (fix_start, fix_end) = ea.get_fixation()
                        fix_list = [f + last_time for f in fix_start]
                        #fix_start_all.extend(fix_list)

                        sac_list = [s + last_time for s in sac_start]
                        #sac_start_all.extend(sac_list)

                        x_trim_all.extend(ea.x_trim)
                        y_trim_all.extend(ea.y_trim)

                        time_list = [x + last_time for x in ea.t_trim]
                        last_time = max(time_list)
                        trial_end.append(last_time)
                        t_trim_all.extend(time_list)

                        # Get fixation location:
                        for i in range(len(fix_start)):
                            # Getting avg fixation coords for each fixation
                            av_x,av_y = get_fixation_average_positions(fix_start[i], fix_end[i], raw_t, raw_x,raw_y)

                            # get AOI position for fixation:
                            aoi_image = get_aoi_for_session_and_id(session, image_id, image_type="RGB")
                            roi_detailed_name, roi_detailed_id = get_aoi_for_gaze_point(av_x, av_y, aoi_image)
                            fix_index_name.append((roi_detailed_name, av_x, av_y))
                            # print("fixation------ (%s,%s) - %s" %(av_x,av_y,roi_detailed_name))

                            num_fixation_dic_trial[roi_detailed_name] = num_fixation_dic_trial[roi_detailed_name] + 1
                            num_fixation_dic_image[roi_detailed_name] = num_fixation_dic_image[roi_detailed_name] + 1

                            fixation_duration = fix_end[i] - fix_start[i]
                            dur_fixation_dic_trial[roi_detailed_name] = dur_fixation_dic_trial[roi_detailed_name] + fixation_duration
                            dur_fixation_dic_image[roi_detailed_name] = dur_fixation_dic_image[roi_detailed_name] + fixation_duration

                            # Intensities:
                            num_intensities[intensity_index][roi_detailed_name] = num_intensities[intensity_index][roi_detailed_name] + 1
                            dur_intensities[intensity_index][roi_detailed_name] = dur_intensities[intensity_index][roi_detailed_name] + fixation_duration

                        num_intensities[intensity_index]["n_trials"] = num_intensities[intensity_index]["n_trials"] + 1
                        dur_intensities[intensity_index]["n_trials"] = dur_intensities[intensity_index]["n_trials"] + 1

                        # Add trial data to overall subject-data:
                        for region in face_regions:
                            key = "%s%s_%s_%s" % (session, image_id, trial.appearance_index, region)
                            num_fix_subject_column_dic[key] = num_fixation_dic_trial[region]
                            dur_fix_subject_column_dic[key] = dur_fixation_dic_trial[region]

                # Image means:
                for region in face_regions:
                    mean_key = "%s%s_%s_mean" % (session, image_id, region)
                    valid_trials_n = len(image_data.get_valid_trials())
                    if valid_trials_n == 0:
                        num_fix_subject_column_dic[mean_key] = 0
                        dur_fix_subject_column_dic[mean_key] = 0
                    else:
                        num_fix_subject_column_dic[mean_key] = num_fixation_dic_image[region] / valid_trials_n
                        dur_fix_subject_column_dic[mean_key] = dur_fixation_dic_image[region] / valid_trials_n



                # save_fixation_plot(t_trim_all, x_trim_all, y_trim_all, fix_start_all, fix_index_name,
                #                  sac_start_all, trial_end, session, image_id)

                sys.stdout.progressBar("[Excluded %s/%s] for %s/%s (%s - %s_%s)" % (
                    exp.EXCLUDED_TRIALS, exp.VALID_TRIALS + exp.EXCLUDED_TRIALS, progress_subject, subject_n,
                    subject.initials, session, image_id), progress_index, n_iter)


            for intensity in [1, 2, 3, 4]:
                for region in face_regions:
                    mean_key = "%s_intensity_%s_%s_mean" % (session, intensity, region)
                    valid_trials_n = num_intensities[intensity]["n_trials"]
                    if valid_trials_n == 0:
                        num_fix_subject_column_dic[mean_key] = 0
                        dur_fix_subject_column_dic[mean_key] = 0
                    else:
                        num_fix_subject_column_dic[mean_key] = num_intensities[intensity][region] / valid_trials_n
                        dur_fix_subject_column_dic[mean_key] = dur_intensities[intensity][region] / valid_trials_n

            # Image trials and exclusion for session:
            session_n_key = "%s_n_trials" % session
            session_excluded_key = "%s_excluded_trials" % session
            session_excluded_ration_key = ("%s_exclusion_ratio_" % session) + "_%"

            for dic in [num_fix_subject_column_dic, dur_fix_subject_column_dic]:
                dic[session_n_key] = session_trials_count
                dic[session_excluded_key] = session_excluded_trials_count
                dic[session_excluded_ration_key] = (session_excluded_trials_count / session_trials_count) * 100


        for cond in ["smile","angry","yawn"]:
            for region in face_regions:
                mean_of_intensity_key = "%s_intensities_mean_%s" % (cond, region)
                num_sum = 0
                dur_sum = 0
                for intensity in [1, 2, 3, 4]:
                    intensity_mean_key = "%s_intensity_%s_%s_mean" % (cond, intensity, region)

                    num_sum = num_sum + num_fix_subject_column_dic[intensity_mean_key]
                    dur_sum = dur_sum + dur_fix_subject_column_dic[intensity_mean_key]

                num_fix_subject_column_dic[mean_of_intensity_key] = num_sum / 4
                dur_fix_subject_column_dic[mean_of_intensity_key] = dur_sum / 4

        # Image trials and exclusion for subject:
        subj_n_key = "n_trials"
        subj_excluded_key = "excluded_trials"
        subj_exlcuded_ration_key = "exclusion_ratio_%"

        for dic in [num_fix_subject_column_dic, dur_fix_subject_column_dic]:
            dic[subj_n_key] = total_trials_count
            dic[subj_excluded_key] = total_excluded_trials_count
            dic[subj_exlcuded_ration_key] = (total_excluded_trials_count / total_trials_count) * 100

        fix_num_series = pd.Series(num_fix_subject_column_dic)
        fix_dur_series = pd.Series(dur_fix_subject_column_dic)
        if full_num_fix_df is None:
            full_num_fix_df = pd.DataFrame(index=fix_num_series.index)
            full_dur_fix_df = pd.DataFrame(index=fix_dur_series.index)

        full_num_fix_df[subject.initials] = fix_num_series.values
        full_dur_fix_df[subject.initials] = fix_dur_series.values





    full_num_fix_df.to_csv(exp.paths["RESULT_DIR"] + "all/FIXATION_COUNT_HK_AS.csv", index=True)
    full_dur_fix_df.to_csv(exp.paths["RESULT_DIR"] + "all/FIXATION_DURATION_HK_AS.csv", index=True)

def save_fixation_plot(t_trim_all, x_trim_all, y_trim_all, fix_start_all, fix_index_name, sac_start_all, trial_end,
                       session, image_id):
    fin_time = t_trim_all[-1]
    plt.figure(1, figsize=(fin_time * 10, 6))
    plt.scatter(t_trim_all, x_trim_all, label="x", marker='.')
    plt.scatter(t_trim_all, y_trim_all, label="y", marker='.')
    plt.axvline(x=fix_start_all[0], linewidth=1, color="red", label="fixation start", linestyle=':')
    plt.axvline(x=sac_start_all[0], linewidth=1, color="green", label="saccade start", linestyle='--')
    plt.axvline(x=trial_end[0], linewidth=4, color="black", label="trial start", linestyle='-')
    plt.legend(loc="upper left")

    # FIXATION:
    for i in range(len(fix_start_all)):
        plt.axvline(x=fix_start_all[i], linewidth=2, color='red', linestyle=':')
        plt.text(fix_start_all[i], 18, s=fix_index_name[i][0])

    for i in range(len(sac_start_all)):
        plt.axvline(x=sac_start_all[i], linewidth=2, color='green', linestyle='--')

    for i in range(len(trial_end)):
        plt.axvline(x=trial_end[i], linewidth=5, color='black', linestyle='-')

    plt.savefig("./RESULTS/fig/fix_%s_%s.png" % (session, image_id))
    plt.close()

def get_saccade_distance(sac_start,sac_end, times, raw_x, raw_y):
    i = 0
    while sac_start > times[i]:
        i = i + 1
    x_1 = raw_x[i]
    y_1 = raw_y[i]

    while sac_end >= times[i]:
        i = i + 1
        if i == len(times):
            break
    x_2 = raw_x[i-1]
    y_2 = raw_y[i-1]

    return math.sqrt((x_2 - x_1)**2 + (y_2 - y_1)**2)

def get_fixation_average_positions(fix_start, fix_end, times, raw_x,raw_y):
    n = 0
    sum_x = 0
    sum_y = 0

    i = 0
    while fix_start > times[i]:
        i = i + 1

    while fix_end >= times[i]:
        n = n + 1
        sum_x = sum_x + raw_x[i]
        sum_y = sum_y + raw_y[i]
        i = i + 1
        if i == len(times):
            break

    return (sum_x / n), (sum_y / n)
