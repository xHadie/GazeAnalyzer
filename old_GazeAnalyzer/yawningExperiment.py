import csv
import os

import sys
import traceback

import StimulusData as SD
from subject import Subject
from heatmapGenerator import HeatmapGenerator
from aoiCalculator import AoiCalculator
from functools import partial
import pandas as pd
from aoiCalculator import colsFinal
import fixationSaccadeExtractor
import sessionData as sDat
import responseTimeAnalyzer


# TRACKERS:
EXCLUDED_TRIALS = 0
VALID_TRIALS = 0
KILL_THREAD = False


def count_excluded():
    global EXCLUDED_TRIALS
    EXCLUDED_TRIALS = EXCLUDED_TRIALS + 1


def count_valid():
    global VALID_TRIALS
    VALID_TRIALS = VALID_TRIALS + 1


def reset_excluded_count():
    global EXCLUDED_TRIALS, VALID_TRIALS
    EXCLUDED_TRIALS = 0
    VALID_TRIALS = 0


def cancelInfo(custom_info=""):
    print()
    print("WARNING: OPERATION CANCELLED %s" % custom_info)


# END TRACKERS
ethnicities = ["AS", "WS", "JP", "HK"]
NUMBER_OF_STIMULUS = 12
NUMBER_OF_INTENSITIES = 4
IMAGES_PER_INTENSITY = 3
IMAGE_SCALING = 0.75
##
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

STIMULUS_WIDTH = 1024
STIMULUS_HEIGHT = 768
ASPECT_WIDTH = 4
ASPECT_HEIGHT = 3
##
INITIAL_GAZE_SEC = 1 / 10
settings = {
    "NUMBER_OF_STIMULUS": 12,
    "conditions": ["smile", "angry", "yawn"],
    "ethnicities": ["AS", "WS", "JP", "HK"],
    "stimulusWidth": 1024,
    "stimulusHeight": 768,
    "aspectWidth": 4,
    "aspectHeight": 3,
    "LOOPS_PER_IMAGE": 10,
    "IMAGES_PER_INTENSITY": 3,
    "NUMBER_OF_INTENSITIES": 4,
    "HEATMAP_IMAGE_SCALE": 15

}

DATA_PATH = "./../Yawning Experiment/CH Experiment/data/"
RESULT_DIR = "./RESULTS/"
AOI_DIR = "./stimulus_aoi/"

paths = {"DATA": DATA_PATH, "RESULT_DIR": RESULT_DIR, "AOI_DIR": AOI_DIR}


class YawningExperiment:
    def __init__(self):
        self.subjects = []
        self.paths = paths
        self.allSubjectsInitials = []
        self.heatmapGenerator = HeatmapGenerator(paths, settings)
        self.aoiCalculator = AoiCalculator(paths, settings)
        self.ready = False

    def __initSubjectList(self):
        for root, dirs, files in os.walk(self.paths["DATA"]):
            for dir in dirs:
                if dir == "1":
                    subject_initials = root.split("/")[-1]
                    sub = Subject(settings, paths, subject_initials)
                    self.subjects.append(sub)
                    self.allSubjectsInitials.append(subject_initials)
                    print("Loaded session data for subject '%s'" % subject_initials)

    def init(self):
        self.__initSubjectList()
        self.ready = True

    # REPONSE
    def generateCombinedResponseCsv(self):
        with open(self.paths["RESULT_DIR"] + 'all/RESPONSE_RESULTS.csv', 'w+', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            headerlist = ['subject']
            conditions = ["smile", "angry", "yawn"]
            for cond in conditions:
                headerlist.append("%s_intensity1" % cond)
                headerlist.append("%s_intensity2" % cond)
                headerlist.append("%s_intensity3" % cond)
                headerlist.append("%s_intensity4" % cond)
                for i in range(0, settings["NUMBER_OF_STIMULUS"]):
                    headerlist.append("%s_%s" % (cond, (i + 1)))

            filewriter.writerow(headerlist)

            for eth in ethnicities:
                print("Extracting response data For ethnicity '%s'" % eth)
                n = 0
                sumDic = {}

                for cond in conditions:
                    intensities = [0, 0, 0, 0]
                    pics = [0, 0, 0, 0,
                            0, 0, 0, 0,
                            0, 0, 0, 0]
                    sumDic[cond] = intensities + pics

                for subject in self.subjects:
                    if subject.nationality == eth:
                        print("For subejct '%s'" % subject.initials)
                        subject.loadSessionData()
                        n = n + 1

                        subject_row = [subject.initials]
                        for session in subject.sessionData.values():
                            session: sDat.SessionData = session
                            session_name = session.blockName
                            intensity1 = session.get_intensity_response_data(1)[0]
                            intensity2 = session.get_intensity_response_data(2)[0]
                            intensity3 = session.get_intensity_response_data(3)[0]
                            intensity4 = session.get_intensity_response_data(4)[0]

                            sumDic[session_name][0] += intensity1
                            sumDic[session_name][1] += intensity2
                            sumDic[session_name][2] += intensity3
                            sumDic[session_name][3] += intensity4

                            imagesData = []
                            for image in session.stimulusData.values():
                                image: SD.StimulusData = image
                                yes_rate_for_image = image.get_yes_rate()
                                imagesData.append(yes_rate_for_image)
                                sumDic[cond][4 + i] += yes_rate_for_image

                            subject_row = subject_row + [intensity1, intensity2, intensity3, intensity4] + imagesData

                        filewriter.writerow(subject_row)

                divider = lambda x: x / n

                ethnicity_row = ["ALL_%s" % eth]

                for cond in conditions:
                    row_part = list(map(divider, sumDic[cond]))
                    ethnicity_row = ethnicity_row + row_part

                filewriter.writerow(ethnicity_row)

    def generateAoiDataFromAllSubjects(self):
        print("Creating full gaze_distri    bution.csv")
        FULL_FRAME = pd.DataFrame()
        INITIAL_FULL_FRAME = pd.DataFrame()

        for subject in self.subjects:
            subject.loadSessionData()
            detailed = subject.getGazeDistributionCsv()
            detailed_initial = subject.getGazeDistributionCsv(initial=True)

            FULL_FRAME = FULL_FRAME.append(detailed, ignore_index=True)
            INITIAL_FULL_FRAME = INITIAL_FULL_FRAME.append(detailed_initial, ignore_index=True)

        os.makedirs(self.paths["RESULT_DIR"] + "all/gaze_distribution/", exist_ok=True)

        save_path_deateiled = self.paths["RESULT_DIR"] + "all/gaze_distribution/" + "aoi.csv"
        save_path_deateiled_initial = self.paths["RESULT_DIR"] + "all/gaze_distribution/" + "aoi_initial.csv"

        inverted_save_path_deateiled = self.paths["RESULT_DIR"] + "all/gaze_distribution/" + "_INVERTED_aoi.csv"
        inverted_save_path_deateiled_initial = self.paths[
                                                   "RESULT_DIR"] + "all/gaze_distribution/" + "_INVERTED_aoi_initial.csv"

        FULL_FRAME[colsFinal].to_csv(save_path_deateiled, index=False)
        INITIAL_FULL_FRAME[colsFinal].to_csv(save_path_deateiled_initial, index=False)

        FULL_FRAME[colsFinal].set_index('SUBJECT').T.to_csv(inverted_save_path_deateiled, index=True)
        INITIAL_FULL_FRAME[colsFinal].set_index('SUBJECT').T.to_csv(inverted_save_path_deateiled_initial, index=True)

        ### ETHNICITY:
        finalToCsvDF = pd.DataFrame()

        initial_finalToCsvDF = pd.DataFrame()
        for eth in ethnicities:
            subjects_of_ethnicity = []
            print("For ethnicity: %s" % eth)
            for subject in self.subjects:
                if eth == subject.nationality:
                    subjects_of_ethnicity.append(subject.initials)

            finalToCsvDF = self.aoiCalculator.createImagesAOI(subjects_of_ethnicity, eth, finalToCsvDF)
            initial_finalToCsvDF = self.aoiCalculator.createImagesAOI(subjects_of_ethnicity, eth, initial_finalToCsvDF,
                                                                      initial=True)

        resultPathFragement = self.paths["RESULT_DIR"] + 'ethnicties/gaze_distribution/'
        os.makedirs(resultPathFragement, exist_ok=True)

        finalToCsvDF[colsFinal].set_index('SUBJECT').T.to_csv("%s/COMPARE__aoi.csv" % resultPathFragement, index=True,
                                                              mode="w+")

        initial_finalToCsvDF[colsFinal].set_index('SUBJECT').T.to_csv(
            "%s/COMPARE_aoi_initial.csv" % resultPathFragement, index=True, mode="w+")

    def generateIndividualResponseCsv(self, pSubjectList, skipIfExisting):
        self.runCommandSubjectInSubjectList("createResponseCsv", pSubjectList, skipIfExisting)

    def generateResponseTimeCsv(self):
        responseTimeAnalyzer.generate_response_time_csv(self.subjects)

    # PLOTS
    def generateIndividualAoiDics(self, pSubjectList, skipIfExisting, createFullGazeHeatmaps,
                                  createInitialGazeHeatmaps):
        self.runCommandOnSubjectList(partial(self.aoiCalculator.generate_aoi_data), pSubjectList,
                                     skipIfExisting, createFullGazeHeatmaps, createInitialGazeHeatmaps)

    def generateFixationData(self, pSubjectList):
        self.runCommandOnSubjectList(partial(fixationSaccadeExtractor.plot_fixation_images), pSubjectList)

    def generate_saccade_data(self, pSubjectList):
        self.runCommandOnSubjectList(partial(fixationSaccadeExtractor.create_saccade_csvs), pSubjectList)

    # HEATMAPS
    def generateIndividualHeatmaps(self, pSubjectList, skipIfExisting, createFullGazeHeatmaps,
                                   createInitialGazeHeatmaps):
        self.runCommandOnSubjectList(partial(self.heatmapGenerator.createHeatmapForSubjects), pSubjectList,
                                     skipIfExisting, createFullGazeHeatmaps, createInitialGazeHeatmaps)

    def generateCombinedHeatmaps(self, skipIfExisting, createFullGazeHeatmaps, createInitialGazeHeatmaps):
        self.heatmapGenerator.createHeatmapForEthnicities(self.subjects, skipIfExisting, createFullGazeHeatmaps,
                                                          createInitialGazeHeatmaps)

    ####### HELPER #######
    def runCommandSubjectInSubjectList(self, functionName, pSubjectList, skipIfExisting=False):
        subject_list = self.allSubjectsInitials
        if len(pSubjectList) > 0:
            print("Running command for following subjects:")
            print(pSubjectList)
            subject_list = pSubjectList

        subject_object_list = []
        for subject in self.subjects:
            if subject.initials in subject_list:
                subject_object_list.append(subject)

        if len(subject_object_list) > 0:
            for subject in subject_object_list:
                try:
                    func = getattr(subject, functionName)
                    func(skipIfExisting)
                except AttributeError as err:
                    print(traceback.print_exc())
                    print(err)
                    print("!! ERROR: ATTRIBUTE NOT FOUND !!")
        else:
            print("!! WARNING: Subject with given initials not found !!")

    def runCommandOnSubjectList(self, function, pSubjectList, *args):
        subject_list = self.allSubjectsInitials
        if len(pSubjectList) > 0:
            print("Running command for following subjects:")
            print(pSubjectList)
            subject_list = pSubjectList

        subject_object_list = []
        for subject in self.subjects:
            if subject.initials in subject_list:
                subject_object_list.append(subject)

        if len(subject_object_list) > 0:
            function(subject_object_list, *args)
        else:
            print("!! WARNING: Subject with given initials not found !!")
