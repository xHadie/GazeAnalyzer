import os
import csv
from sessionData import SessionData
from StimulusData import StimulusData
from TrialData import TrialData
import pandas as pd
import sys

class Subject:

    def __init__(self, settings, paths, initials, age=0):
        self.initials = initials
        self.age = age
        self.paths = paths
        self.settings = settings
        self.nationality = initials.split("_")[0]
        self.sessionData = {}
        self.sessionDataLoaded = False

    def loadSessionData(self):
        if not self.sessionDataLoaded:
            for root, dirs, files in os.walk(self.paths["DATA"] + self.initials):
                for file in files:
                    if not file.startswith("et") and file.endswith(".csv"):
                        #print("------------------ INIT DATA START ------------------")
                        data = pd.read_csv(root + "/" + file)
                        if root.endswith("1"):
                            self.sessionData["smile"] = SessionData(self, data, "smile")

                        if root.endswith("2"):
                            self.sessionData["angry"] = SessionData(self, data, "angry")

                        if root.endswith("3"):
                            self.sessionData["yawn"] = SessionData(self, data, "yawn")
                        #print("------------------ INIT DATA END ------------------")

            self.sessionDataLoaded = True


    def getGazeListFromCsv(self, session, image_id, initial=False):
        initial_part = ""
        if (initial):
            initial_part = "_initial"
        csv_path = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/%s%s.csv" % (
        self.initials, session, image_id, initial_part)

        gaze_df = pd.read_csv(csv_path)
        x = gaze_df["x"]
        y = gaze_df["y"]

        gaze_list = list(zip(x, y))
        return gaze_list

    ######
    def createGazeCsvForSubjectIfMissing(self, df_path):
        if not os.path.exists(df_path):
            print("Creating gaze csv from trials first for %s..." % self.initials)
            self.createSummarizedGazeCsvs()
            print("DONE! Creating heatmaps now!")
            print("")

    ######
    def createSummarizedGazeCsvs(self):
        self.loadSessionData()
        all_session_long_file = None

        for session in self.sessionData:
            session_data = self.sessionData[session]
            for image_data in session_data.stimulusData.values():
                image_data: StimulusData = image_data
                image_id = image_data.image_id

                gaze_data_summarized = None
                gaze_data_summarized_initial = None

                image_long_df = None
                print("Valid trials: %s" % (len(image_data.get_valid_trials())))
                for trial in image_data.get_valid_trials():
                    trial: TrialData = trial
                    if trial.is_valid():
                        trial_number = trial.get_trial_id()

                        # Full
                        processed_gaze_df, pg_long_df = trial.get_processed_gaze()
                        #print(pg_long_df)
                        processed_initial_gaze_df, pg_initial_long_df = trial.get_processed_gaze(only_initial_gaze=True)

                        # save trial data to file:
                        save_path_trial = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/trials/" % (
                        self.initials, session)
                        os.makedirs(save_path_trial, exist_ok=True)
                        processed_gaze_df.to_csv(save_path_trial + "img_%s_trial_%s.csv" % (image_id, trial_number),
                                                 index=False, mode="w+")
                        processed_gaze_df.to_csv(
                            save_path_trial + "img_%s_trial_%s_initial.csv" % (image_id, trial_number), index=False,
                            mode="w+")

                        if all_session_long_file is None:
                            all_session_long_file = pg_long_df
                        if gaze_data_summarized is None:
                            image_long_df = pg_long_df
                            gaze_data_summarized = processed_gaze_df
                            gaze_data_summarized_initial = processed_initial_gaze_df
                        else:
                            all_session_long_file = all_session_long_file.append(pg_long_df, ignore_index=True)
                            image_long_df = image_long_df.append(pg_long_df, ignore_index=True)
                            gaze_data_summarized = gaze_data_summarized.append(processed_gaze_df, ignore_index=True)
                            gaze_data_summarized_initial = gaze_data_summarized_initial.append(
                                processed_initial_gaze_df, ignore_index=True)

                save_path = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/" % (self.initials, session)
                os.makedirs(save_path, exist_ok=True)

                image_long_df.to_csv(save_path + "%s_long.csv" % image_id, index=False, mode="w+")
                gaze_data_summarized.to_csv(save_path + "%s.csv" % image_id, index=False, mode="w+")
                gaze_data_summarized_initial.to_csv(save_path + "%s_initial.csv" % image_id, index=False, mode="w+")

                sys.stdout.progressBar(
                    "Creating gaze CSV for %s - %s " % (self.initials, session),
                    image_id,
                    self.settings["NUMBER_OF_STIMULUS"])
        print("Saving LONG")
        save_path_long = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/" % (self.initials)
        all_session_long_file.to_csv(save_path_long + "%s_long.csv" % self.initials, index=False, mode="w+")

    ######
    def createResponseCsv(self, skipIfExisting):
        self.loadSessionData()

        save_path = self.paths["RESULT_DIR"] + 'subjects/%s/' % self.initials
        file_path = save_path + "response_results.csv"
        if skipIfExisting:
            if os.path.exists(file_path):
                print("%s Skipped - response CSV already found" % self.initials)
                return
        print("Creating response CSV for %s" % self.initials)
        os.makedirs(save_path, exist_ok=True)

        with open(file_path, 'w+', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['image_name', 'yes_rate', "yes", "no"])
            for key in self.sessionData:
                intensity1 = self.sessionData[key].get_intensity_response_data(1)
                intensity2 = self.sessionData[key].get_intensity_response_data(2)
                intensity3 = self.sessionData[key].get_intensity_response_data(3)
                intensity4 = self.sessionData[key].get_intensity_response_data(4)
                filewriter.writerow(['%s_intensity1' % (key), intensity1[0], intensity1[1], intensity1[2]])
                filewriter.writerow(['%s_intensity2' % (key), intensity2[0], intensity2[1], intensity2[2]])
                filewriter.writerow(['%s_intensity3' % (key), intensity3[0], intensity3[1], intensity3[2]])
                filewriter.writerow(['%s_intensity4' % (key), intensity4[0], intensity4[1], intensity4[2]])

                session_data: SessionData = self.sessionData[key]
                for image in session_data.stimulusData.values():
                    image: StimulusData = image
                    yesRate = image.get_yes_rate()
                    yes = image.get_yes_count()
                    no = image.get_no_count()
                    filewriter.writerow(['%s_%s' % (key, image.image_id), str(yesRate), str(yes), str(no)])

    ######
    def getResultDir(self):
        return self.paths["RESULT_DIR"] + "subjects/%s/" % self.initials

    ######
    def getGazeDistributionCsv(self, initial=False):
        initial_part = ""
        if initial:
            initial_part = "_initial"

        result_dir = self.getResultDir() + "gaze_distribution/%s_aoi%s.csv"

        detailed_path = result_dir % ("detailed", initial_part)
        rectangular_path = result_dir % ("rectangular", initial_part)

        detailed = pd.read_csv(detailed_path)
        rectangular = pd.read_csv(rectangular_path)
        return detailed, rectangular

    def getConditionData(self, key):
        return self.sessionData[key]
