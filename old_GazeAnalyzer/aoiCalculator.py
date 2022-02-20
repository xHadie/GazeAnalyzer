import math
import os

import pandas as pd
import plotGenerator
import yawningExperiment as exp

from PIL import Image

COLOR_CODING_MOUTH = (12, 17, 252)
COLOR_CODING_FACE = (255, 0, 52)

# DETAILED
COLOR_CODING_RIGHT_EYE = (239, 12, 252)
COLOR_CODING_LEFT_EYE = (246, 252, 12)
COLOR_CODING_BETWEEN_EYE = (12, 252, 249)
COLOR_CODING_NOSE = (85, 252, 12)


def inColorRange(r, g, b, cond):
    # pixel value offset tolerance
    tolerance = 15
    return (cond[0] - tolerance < r < cond[0] + tolerance) and \
           (cond[1] - tolerance < g < cond[1] + tolerance) and \
           (cond[2] - tolerance < b < cond[2] + tolerance)


def resize_canvas(im, canvas_width=1024, canvas_height=768):
    """
    Resize the canvas of old_image_path.

    Store the new image in new_image_path. Center the image on the new canvas.

    Parameters
    ----------
    old_image_path : str
    new_image_path : str
    canvas_width : int
    canvas_height : int
    """
    old_width, old_height = im.size

    # Center the image
    x1 = int(math.floor((canvas_width - old_width) / 2))
    y1 = int(math.floor((canvas_height - old_height) / 2))

    mode = im.mode
    if len(mode) == 1:  # L, 1
        new_background = (255)
    if len(mode) == 3:  # RGB
        new_background = (255, 255, 255)
    if len(mode) == 4:  # RGBA, CMYK
        new_background = (255, 255, 255, 255)

    newImage = Image.new(mode, (canvas_width, canvas_height), new_background)
    newImage.paste(im, (x1, y1, x1 + old_width, y1 + old_height))
    return newImage


# inits a dataframe prefilled with values, needed for intenstiy
def initIntensityDataframe():
    cols = {'eyes': 0.0, 'nose': 0.0, 'mouth': 0.0, 'other': 0.0,
            'gaze_time_sec': 0.0}

    df = pd.DataFrame()
    for i in range(exp.NUMBER_OF_INTENSITIES):
        df = df.append(cols, ignore_index=True)
    return df


colsFinal = ['SUBJECT',
             'S_1_E', 'S_1_N', 'S_1_M', 'S_1_OTHER', 'S_1_ALL',
             'S_2_E', 'S_2_N', 'S_2_M', 'S_2_OTHER', 'S_2_ALL',
             'S_3_E', 'S_3_N', 'S_3_M', 'S_3_OTHER', 'S_3_ALL',
             'S_4_E', 'S_4_N', 'S_4_M', 'S_4_OTHER', 'S_4_ALL',
             'S_5_E', 'S_5_N', 'S_5_M', 'S_5_OTHER', 'S_5_ALL',
             'S_6_E', 'S_6_N', 'S_6_M', 'S_6_OTHER', 'S_6_ALL',
             'S_7_E', 'S_7_N', 'S_7_M', 'S_7_OTHER', 'S_7_ALL',
             'S_8_E', 'S_8_N', 'S_8_M', 'S_8_OTHER', 'S_8_ALL',
             'S_9_E', 'S_9_N', 'S_9_M', 'S_9_OTHER', 'S_9_ALL',
             'S_10_E', 'S_10_N', 'S_10_M', 'S_10_OTHER', 'S_10_ALL',
             'S_11_E', 'S_11_N', 'S_11_M', 'S_11_OTHER', 'S_11_ALL',
             'S_12_E', 'S_12_N', 'S_12_M', 'S_12_OTHER', 'S_12_ALL',

             'A_1_E', 'A_1_N', 'A_1_M', 'A_1_OTHER', 'A_1_ALL',
             'A_2_E', 'A_2_N', 'A_2_M', 'A_2_OTHER', 'A_2_ALL',
             'A_3_E', 'A_3_N', 'A_3_M', 'A_3_OTHER', 'A_3_ALL',
             'A_4_E', 'A_4_N', 'A_4_M', 'A_4_OTHER', 'A_4_ALL',
             'A_5_E', 'A_5_N', 'A_5_M', 'A_5_OTHER', 'A_5_ALL',
             'A_6_E', 'A_6_N', 'A_6_M', 'A_6_OTHER', 'A_6_ALL',
             'A_7_E', 'A_7_N', 'A_7_M', 'A_7_OTHER', 'A_7_ALL',
             'A_8_E', 'A_8_N', 'A_8_M', 'A_8_OTHER', 'A_8_ALL',
             'A_9_E', 'A_9_N', 'A_9_M', 'A_9_OTHER', 'A_9_ALL',
             'A_10_E', 'A_10_N', 'A_10_M', 'A_10_OTHER', 'A_10_ALL',
             'A_11_E', 'A_11_N', 'A_11_M', 'A_11_OTHER', 'A_11_ALL',
             'A_12_E', 'A_12_N', 'A_12_M', 'A_12_OTHER', 'A_12_ALL',

             'Y_1_E', 'Y_1_N', 'Y_1_M', 'Y_1_OTHER', 'Y_1_ALL',
             'Y_2_E', 'Y_2_N', 'Y_2_M', 'Y_2_OTHER', 'Y_2_ALL',
             'Y_3_E', 'Y_3_N', 'Y_3_M', 'Y_3_OTHER', 'Y_3_ALL',
             'Y_4_E', 'Y_4_N', 'Y_4_M', 'Y_4_OTHER', 'Y_4_ALL',
             'Y_5_E', 'Y_5_N', 'Y_5_M', 'Y_5_OTHER', 'Y_5_ALL',
             'Y_6_E', 'Y_6_N', 'Y_6_M', 'Y_6_OTHER', 'Y_6_ALL',
             'Y_7_E', 'Y_7_N', 'Y_7_M', 'Y_7_OTHER', 'Y_7_ALL',
             'Y_8_E', 'Y_8_N', 'Y_8_M', 'Y_8_OTHER', 'Y_8_ALL',
             'Y_9_E', 'Y_9_N', 'Y_9_M', 'Y_9_OTHER', 'Y_9_ALL',
             'Y_10_E', 'Y_10_N', 'Y_10_M', 'Y_10_OTHER', 'Y_10_ALL',
             'Y_11_E', 'Y_11_N', 'Y_11_M', 'Y_11_OTHER', 'Y_11_ALL',
             'Y_12_E', 'Y_12_N', 'Y_12_M', 'Y_12_OTHER', 'Y_12_ALL',
             ]

AOI = {}
AOI_RGB = {}


def get_aoi_for_session_and_id(session, image, image_type="normal"):
    aoi_key = "%s_%s" % (session, image)
    if image_type == "RGB":
        if aoi_key in AOI_RGB:
            return AOI_RGB[aoi_key]
        elif aoi_key in AOI:
            AOI_RGB[aoi_key] = AOI[aoi_key].convert('RGB')
            return AOI_RGB[aoi_key]
        else:
            AOI[aoi_key] = init_aoi_image(session, image)
            AOI_RGB[aoi_key] = AOI[aoi_key].convert('RGB')
    elif aoi_key in AOI:
        return AOI[aoi_key]
    else:
        AOI[aoi_key] = init_aoi_image(session, image)
        return AOI[aoi_key]


def init_aoi_image(session, image_id):
    aoi_image_base_path = ""

    if session == "smile":
        aoi_image_base_path = "/smile/smile_%s_%s.png"
    if session == "angry":
        aoi_image_base_path = "/angry/angry_%s_%s.png"
    if session == "yawn":
        aoi_image_base_path = "/yawning/yawning_%s_%s.png"

    aoi_image_final_path = exp.paths["AOI_DIR"] + aoi_image_base_path % (image_id, "AOI")

    image = Image.open(aoi_image_final_path)

    image = image.resize(
        (int(exp.STIMULUS_WIDTH * exp.IMAGE_SCALING),
         int(exp.STIMULUS_HEIGHT * exp.IMAGE_SCALING)))
    image = resize_canvas(image)

    return image


def get_aoi_for_gaze_point(x, y, rgb_im):
    try:
        r, g, b = rgb_im.getpixel((x, y))
        if inColorRange(r, g, b, COLOR_CODING_LEFT_EYE):
            return "left_eye", 0
        elif inColorRange(r, g, b, COLOR_CODING_RIGHT_EYE):
            return "right_eye", 1
        elif inColorRange(r, g, b, COLOR_CODING_BETWEEN_EYE):
            return "between_eyes", 2
        elif inColorRange(r, g, b, COLOR_CODING_NOSE):
            return "nose", 3
        elif inColorRange(r, g, b, COLOR_CODING_MOUTH):
            return "mouth", 4
        elif inColorRange(r, g, b, COLOR_CODING_FACE):
            return "other_face", 5
        else:
            return "out_of_face", 6
    except:
        return "out_of_image", -1


class AoiCalculator:
    def __init__(self, paths, settings):
        self.settings = settings
        self.paths = paths

    def generate_aoi_data(self, subject_list, skip_if_existing, create_full_gaze_aoi, create_initial_aoi):
        for subject in subject_list:
            subject.loadSessionData()
            print("Creating AOI data for %s " % subject.initials)
            subject_name = subject.initials

            full_distribution_detailed_dic = {}

            initial_full_distribution_detailed_dic = {}

            for sessionName in subject.sessionData:

                gaze_distribution_detailed_df = pd.DataFrame()

                intensity_gaze_distribution_detailed_df = initIntensityDataframe()

                initial_gaze_distribution_detailed_df = pd.DataFrame()

                initial_intensity_gaze_distribution_detailed_df = initIntensityDataframe()

                for imageId in range(self.settings["NUMBER_OF_STIMULUS"]):
                    if exp.KILL_THREAD:
                        exp.cancelInfo()
                        return

                    current_image_id = imageId + 1

                    whole_gaze_data_path = subject.getResultDir() + "gaze_results/%s/%s.csv" % (
                        sessionName, current_image_id)
                    subject.createGazeCsvForSubjectIfMissing(whole_gaze_data_path)

                    # ************ FULL GAZE ************
                    # Calc gaze distribution for current image:
                    gaze_list = subject.getGazeListFromCsv(sessionName, current_image_id)
                    image_gaze_distribution_detailed, (
                        numInRange, numOutOfRange) = self.calc_detailed_aoi_distribution_dic(gaze_list,
                                                                                             sessionName,
                                                                                             current_image_id)

                    # Add to session DF:
                    gaze_distribution_detailed_df = gaze_distribution_detailed_df.append(
                        image_gaze_distribution_detailed, ignore_index=True)

                    # current imaged dic to DF:
                    current_image_detailed_distribution_df = pd.DataFrame(image_gaze_distribution_detailed, index=[0])

                    # Add current image DF to intensity DF:
                    intensity_index = (current_image_id - 1) % self.settings["NUMBER_OF_INTENSITIES"]
                    intensity_gaze_distribution_detailed_df.loc[intensity_index] = \
                        current_image_detailed_distribution_df.loc[0] + intensity_gaze_distribution_detailed_df.loc[
                            intensity_index]

                    # ************ INITAL GAZE ************
                    # Calc gaze distribution for current image:
                    initial_gaze_list = subject.getGazeListFromCsv(sessionName, current_image_id, initial=True)
                    initial_image_gaze_distribution_detailed, (
                        numInRange, numOutOfRange) = self.calc_detailed_aoi_distribution_dic(initial_gaze_list,
                                                                                             sessionName,
                                                                                             current_image_id)

                    # Add to session DF:
                    initial_gaze_distribution_detailed_df = initial_gaze_distribution_detailed_df.append(
                        initial_image_gaze_distribution_detailed, ignore_index=True)

                    # current imaged dic to DF:
                    initial_current_image_detailed_distribution_df = pd.DataFrame(
                        initial_image_gaze_distribution_detailed, index=[0])

                    # Add current image DF to intensity DF:
                    intensity_index = (current_image_id - 1) % self.settings["NUMBER_OF_INTENSITIES"]
                    initial_intensity_gaze_distribution_detailed_df.loc[intensity_index] = \
                        initial_current_image_detailed_distribution_df.loc[0] + \
                        initial_intensity_gaze_distribution_detailed_df.loc[intensity_index]

                    print(current_image_id)

                # CREATE PLOTS FOR INTENSITY IMAGES:
                save_path = subject.getResultDir()

                # FULL
                plotGenerator.plotAllImagesDetailed(gaze_distribution_detailed_df, save_path, subject_name, sessionName,
                                                    skip_if_existing)

                plotGenerator.plotIntensityDetailed(intensity_gaze_distribution_detailed_df, save_path, subject_name,
                                                    sessionName, skip_if_existing)

                # INTIIAL
                plotGenerator.plotAllImagesDetailed(initial_gaze_distribution_detailed_df, save_path, subject_name,
                                                    sessionName, skip_if_existing, initial=True)

                plotGenerator.plotIntensityDetailed(initial_intensity_gaze_distribution_detailed_df, save_path,
                                                    subject_name, sessionName, skip_if_existing, initial=True)

                # ADD TO FULL DF
                session_initial = sessionToInitial(sessionName)
                full_distribution_detailed_dic[session_initial] = gaze_distribution_detailed_df

                initial_full_distribution_detailed_dic[session_initial] = initial_gaze_distribution_detailed_df

            distDic = createDistributionDicDetailed(subject_name, full_distribution_detailed_dic)

            FULL_SUBJECT_DETAILED_DF = pd.DataFrame()
            FULL_SUBJECT_DETAILED_DF = FULL_SUBJECT_DETAILED_DF.append(distDic, ignore_index=True)

            initial_distDic = createDistributionDicDetailed(subject_name, initial_full_distribution_detailed_dic)

            INITIAL_FULL_SUBJECT_DETAILED_DF = pd.DataFrame()
            INITIAL_FULL_SUBJECT_DETAILED_DF = INITIAL_FULL_SUBJECT_DETAILED_DF.append(initial_distDic,
                                                                                       ignore_index=True)

            csvs_save_path = subject.getResultDir() + "gaze_distribution/"
            os.makedirs(csvs_save_path, exist_ok=True)

            FULL_SUBJECT_DETAILED_DF[colsFinal].to_csv(csvs_save_path + "aoi.csv", index=False)

            FULL_SUBJECT_DETAILED_DF[colsFinal].to_csv(csvs_save_path + "aoi_initial.csv", index=False)

    def calc_detailed_aoi_distribution_dic(self, df, session, image_id):
        aoi_image = get_aoi_for_session_and_id(session, image_id)
        eye_tracker_rate = 300.0

        rgb_im = aoi_image.convert('RGB')
        dist = {'eyes': 0.0, 'nose': 0.0, 'mouth': 0.0, 'other': 0.0, 'gaze_time_sec': 0.0}

        num_in_range = 0
        num_out_of_range = 0
        for entry in df:
            try:
                r, g, b = rgb_im.getpixel(entry)
                if inColorRange(r, g, b, COLOR_CODING_LEFT_EYE):
                    dist["eyes"] = dist["eyes"] + 1.0
                elif inColorRange(r, g, b, COLOR_CODING_RIGHT_EYE):
                    dist["eyes"] = dist["eyes"] + 1.0
                elif inColorRange(r, g, b, COLOR_CODING_BETWEEN_EYE):
                    dist["eyes"] = dist["eyes"] + 1.0
                elif inColorRange(r, g, b, COLOR_CODING_NOSE):
                    dist["nose"] = dist["nose"] + 1.0
                elif inColorRange(r, g, b, COLOR_CODING_MOUTH):
                    dist["mouth"] = dist["mouth"] + 1.0
                else:
                    dist["other"] = dist["other"] + 1.0

                dist["gaze_time_sec"] = dist["gaze_time_sec"] + 1.0
                num_in_range += 1
            except:
                num_out_of_range += 1

        # normalize data to second:
        dist["eyes"] = dist["eyes"] / eye_tracker_rate * 1000.0
        dist["nose"] = dist["nose"] / eye_tracker_rate * 1000.0
        dist["mouth"] = dist["mouth"] / eye_tracker_rate * 1000.0
        dist["other"] = dist["other"] / eye_tracker_rate * 1000.0

        dist["gaze_time_sec"] = dist["gaze_time_sec"] / eye_tracker_rate * 1000.0
        return dist, (num_in_range, num_out_of_range)

    def createImagesAOI(self, subjectsDf, key, finalToCsvDF, skipIfExists=False, initial=False):
        ALL_AOI = None
        if initial:
            ALL_AOI = pd.read_csv(self.paths["RESULT_DIR"] + "all/gaze_distribution/" + "aoi_initial.csv")
        else:
            ALL_AOI = pd.read_csv(self.paths["RESULT_DIR"] + "all/gaze_distribution/" + "aoi.csv")

        n = len(subjectsDf)

        df = ALL_AOI[ALL_AOI['SUBJECT'].isin(subjectsDf)].reset_index()

        meanDic = df.mean().to_dict()
        meanDic["SUBJECT"] = key
        finalToCsvDF = finalToCsvDF.append(pd.DataFrame(meanDic, index=[0])[colsFinal], ignore_index=True)
        save_path = self.paths["RESULT_DIR"] + "ethnicties/%s/" % (key)

        sDf, aDf, yDf, sIDf, aIDf, yIDf = savedFormatToImageFormat(df.mean().to_dict())
        plotGenerator.plotAllImagesDetailed(sDf, save_path, key, "smile", skipIfExists, initial=initial, n=n)
        plotGenerator.plotAllImagesDetailed(aDf, save_path, key, "angry", skipIfExists, initial=initial, n=n)
        plotGenerator.plotAllImagesDetailed(yDf, save_path, key, "yawn", skipIfExists, initial=initial, n=n)

        plotGenerator.plotIntensityDetailed(sIDf, save_path, key, "smile", skipIfExists, initial=initial, n=n)
        plotGenerator.plotIntensityDetailed(aIDf, save_path, key, "angry", skipIfExists, initial=initial, n=n)
        plotGenerator.plotIntensityDetailed(yIDf, save_path, key, "yawn", skipIfExists, initial=initial, n=n)
        return finalToCsvDF


def createDistributionDicDetailed(subjectName, df):
    distDic = {'SUBJECT': subjectName}
    for cond in ["S", "A", "Y"]:
        for x in range(1, 13):
            distDic["%s_%s_E" % (cond, x)] = df[cond]["eyes"][x - 1]
            distDic["%s_%s_N" % (cond, x)] = df[cond]["nose"][x - 1]
            distDic["%s_%s_M" % (cond, x)] = df[cond]["mouth"][x - 1]
            distDic["%s_%s_OTHER" % (cond, x)] = df[cond]["other"][x - 1]
            distDic["%s_%s_ALL" % (cond, x)] = df[cond]["gaze_time_sec"][x - 1]
    return distDic


def sessionToInitial(session):
    if session == "smile":
        return "S"
    if session == "angry":
        return "A"
    if session == "yawn":
        return "Y"


def savedFormatToImageFormat(dic):
    dfs = {"S": pd.DataFrame(), "A": pd.DataFrame(), "Y": pd.DataFrame(),
           "SI": initIntensityDataframe("detailed"), "AI": initIntensityDataframe("detailed"),
           "YI": initIntensityDataframe("detailed")}
    for c in ["S", "A", "Y"]:
        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
            new = {'eyes': 0.0, 'mouth': 0.0, 'nose': 0.0, 'other': 0.0, 'gaze_time_sec': 0.0}
            new["eyes"] = dic[c + "_" + str(i) + "_E"]
            new["nose"] = dic[c + "_" + str(i) + "_N"]
            new["mouth"] = dic[c + "_" + str(i) + "_M"]
            new["other"] = dic[c + "_" + str(i) + "_OTHER"]
            new["gaze_time_sec"] = dic[c + "_" + str(i) + "_ALL"]

            currentImDf = pd.DataFrame(new, index=[0])
            intensity_key = (i - 1) % 4

            dfs[c + "I"].loc[intensity_key] = currentImDf.loc[0] + dfs[c + "I"].loc[intensity_key]

            dfs[c] = dfs[c].append(new, ignore_index=True)

    return dfs["S"], dfs["A"], dfs["Y"], dfs["SI"], dfs["AI"], dfs["YI"]
