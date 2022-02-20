import numpy as np
import pandas as pd


def read_data_other(filename, screenWidth, screenHeight, to_img_space=True):
    def toNumpy(entry):
        values = np.fromstring(entry.strip('()'), sep=',')

        # values[0] = values[0] * screenWidth - xOffset

        return values

    def limitWithinScreen(corr):
        new_corr = np.zeros(2)
        if corr[0] < 0 or corr[0] > screenWidth:
            new_corr[0] = np.nan
        else:
            new_corr[0] = corr[0]

        if corr[1] < 0 or corr[1] > screenHeight:
            new_corr[1] = np.nan
        else:
            new_corr[1] = corr[1]

        return new_corr

    data = pd.read_csv(filename)

    x = []
    y = []
    for i in range(len(data)):
        locl = limitWithinScreen(toNumpy(data["left_eye_gp"].iloc[i]))
        locr = limitWithinScreen(toNumpy(data["right_eye_gp"].iloc[i]))

        if any(np.isnan(locl)) and not any(np.isnan(locr)):
            loc = locr
        elif any(np.isnan(locr)) and not any(np.isnan(locl)):
            loc = locl
        elif not any(np.isnan(locl)) and not any(np.isnan(locr)):
            loc = (locl + locr) / 2
        else:
            loc = [np.nan, np.nan]

        x.append(loc[0])
        y.append(loc[1])

    raw_x = np.array(x)
    raw_y = np.array(y)
    raw_t = (data.loc[:, 'timestamp'] - data.loc[:, 'timestamp'][0]) / 1000000

    if to_img_space:
        # TO coord space
        newImageWidth = 768 / 3 * 4
        xOffset = (newImageWidth - 1024) / 2
        return ((raw_x * newImageWidth) - xOffset, raw_y * 768, raw_t.values.squeeze())
    else:
        return (raw_x, raw_y, raw_t.values.squeeze())


def read_data_updated(filename, screenWidth, screenHeight):
    def toNumpy(entry):
        values = np.fromstring(entry.strip('()'), sep=',')

        # values[0] = values[0] * screenWidth - xOffset
        newImageWidth = 768 / 3 * 4
        xOffset = (newImageWidth - 1024) / 2

        values[0] = (values[0] * screenWidth) - xOffset
        values[1] = values[1] * 768

        return values

    def limitWithinScreen(corr):
        new_corr = np.zeros(2)
        if corr[0] < 0 or corr[0] > screenWidth:
            new_corr[0] = np.nan
        else:
            new_corr[0] = corr[0]

        if corr[1] < 0 or corr[1] > screenHeight:
            new_corr[1] = np.nan
        else:
            new_corr[1] = corr[1]

        return new_corr

    data = pd.read_csv(filename)

    x = []
    y = []
    for i in range(len(data)):
        locl = limitWithinScreen(toNumpy(data["left_eye_gp"].iloc[i]))
        locr = limitWithinScreen(toNumpy(data["right_eye_gp"].iloc[i]))

        if any(np.isnan(locl)) and not any(np.isnan(locr)):
            loc = locr
        elif any(np.isnan(locr)) and not any(np.isnan(locl)):
            loc = locl
        elif not any(np.isnan(locl)) and not any(np.isnan(locr)):
            loc = (locl + locr) / 2
        else:
            loc = [np.nan, np.nan]

        x.append(loc[0])
        y.append(loc[1])

    raw_x = np.array(x)
    raw_y = np.array(y)
    raw_t = (data.loc[:, 'timestamp'] - data.loc[:, 'timestamp'][0]) / 1000000

    return (raw_x, raw_y, raw_t.values.squeeze())
