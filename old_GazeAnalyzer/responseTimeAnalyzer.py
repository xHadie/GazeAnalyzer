import yawningExperiment as exp
import sys
import pandas as pd
import os
RESPONSE_TIMES: pd.DataFrame = None


def __get_response_time_csv_path():
    outdir = exp.paths["RESULT_DIR"] + "all/"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    fullname = os.path.join(outdir, "RESPONSE_TIMES.csv")    
    return fullname


def __load_response_time_dic():
    global RESPONSE_TIMES
    if RESPONSE_TIMES is None:
        RESPONSE_TIMES = pd.read_csv(__get_response_time_csv_path(), index_col = 0)


def is_trial_valid(subject, session, image, trial):
    rt = get_response_time_for_trial(subject, session, image, trial)
    sd = get_sd_for_condition(subject, session)
    return rt <= sd


def get_sd_for_condition(subject, session):
    __load_response_time_dic()
    return RESPONSE_TIMES.at["%s_M+2.5SD" % session, subject.initials]


def get_response_time_for_trial(subject, session, image, trial):
    __load_response_time_dic()
    return RESPONSE_TIMES.at["%s%s_%s" % (session, image, trial), subject.initials]


def generate_response_time_csv(subjects):
    # For subjects:
    full_rt_df = None
    progress_index = 0
    n_subjects = len(subjects)
    print("Creating response-time csvs....")
    sys.stdout.progressBar("Generating RESPONSE_TIMES.csv", progress_index, n_subjects)
    for subject in subjects:
        progress_index = progress_index + 1
        subject.loadSessionData()
        subject_rt_series = pd.Series()
        for cond in exp.settings["conditions"]:
            sessionData = subject.sessionData[cond]
            cond_series = sessionData.createResponseTimeSeries()
            subject_rt_series = subject_rt_series.append(cond_series)
        if full_rt_df is None:
            full_rt_df = pd.DataFrame(index=subject_rt_series.index)
        full_rt_df[subject.initials] = subject_rt_series.values
        sys.stdout.progressBar(
            "[Excluded %s/%s] Generating RESPONSE_TIMES.csv (%s)" % (
                exp.EXCLUDED_TRIALS, exp.VALID_TRIALS + exp.EXCLUDED_TRIALS, subject.initials),
            progress_index, n_subjects)

    full_rt_df.to_csv(__get_response_time_csv_path(), index=True)
    print("Saved RESPONSE_TIME.csv! ")
