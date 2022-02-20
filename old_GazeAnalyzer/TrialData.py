import pandas as pd
import StimulusData as SD
import sessionData as SesD
import yawningExperiment as exp
from aoiCalculator import get_aoi_for_gaze_point, get_aoi_for_session_and_id
import responseTimeAnalyzer

ALLOWED_INVALID_RATIO = 80


def string_to_tuple(tuple_str):
    tuple_str = tuple_str.replace("(", "")
    tuple_str = tuple_str.replace(")", "")
    tuple_str = tuple_str.replace(" ", "")
    values = tuple_str.split(',')
    if values[0] == "nan":
        return None
    if values[1] == "nan":
        return None
    return float(values[0]), (float(values[1]))


class TrialData:
    YES_RESPONSE = "YES"
    NO_RESPONSE = "NO"

    def __init__(self, stimulus, row, appearance_index):
        self.__valid = None
        self.stimulus = stimulus
        self.block_rep_n = int(row['%s_block_loop.thisRepN' % stimulus.session.blockName])
        self.block_rep_trial_n = int(row['%s_block_loop.thisTrialN' % stimulus.session.blockName])
        self.overall_trial_n = int(row['%s_block_loop.thisN' % stimulus.session.blockName]) + 1
        self.response_time = float(row['key_resp_%s.rt' % stimulus.session.blockName])
        self.response = self.__key_to_response(row['key_resp_%s.keys' % stimulus.session.blockName])
        self.appearance_index = appearance_index
        self.loaded = False
        self.gaze_df = None

    def get_gaze_df(self):
        if not self.loaded:
            try:
                self.gaze_df = pd.read_csv(self.get_trial_file_path(), skipinitialspace=True,
                                           usecols=["timestamp", "left_eye_gp", "right_eye_gp"])

            except pd.errors.ParserError:
                print("Failed to load trial data: %s%s_%s " % (
                    self.stimulus.session.blockName, self.stimulus.image_id, self.get_trial_id()))
                exit(-1)
        return self.gaze_df

    def unload_gaze(self):
        if self.loaded:
            del self.gaze_df
            self.loaded = False

    def get_trial_file_path(self):
        gaze_data_filename = "et_imgNameIndex%s_trial%s.csv" % (self.stimulus.image_id, self.get_trial_id())
        session_data: SesD.SessionData = self.stimulus.session
        return session_data.get_data_dir() + gaze_data_filename

    def is_valid(self):
        if self.__valid is None:
            # Check response-time validity:
            self.__valid = responseTimeAnalyzer.is_trial_valid(self.stimulus.session.subject,
                                                               self.stimulus.session.blockName,
                                                               self.stimulus.image_id,
                                                               self.appearance_index)
            # Check gaze-ratio validity:
            if self.__valid:
                self.__valid = self.__check_if_gaze_data_valid()

            # Stat counter:
            if self.is_valid():
                exp.count_valid()
            else:
                exp.count_excluded()
            self.loaded = True
        return self.__valid

    def excluded(self):
        return not self.is_valid()

    def __key_to_response(self, key):
        if key == "n" or key == "s":
            return self.NO_RESPONSE
        if key == "y" or key == "l":
            return self.YES_RESPONSE

    def get_trial_id(self):
        return self.overall_trial_n

    def __check_if_gaze_data_valid(self):
        sample_df = self.get_gaze_df()["left_eye_gp"]
        size = len(sample_df)

        invalid_count = 0
        for i in range(size):
            if string_to_tuple(sample_df[i]) is None:
                invalid_count = invalid_count + 1

        return (invalid_count / size) * 100 <= ALLOWED_INVALID_RATIO

    def get_processed_gaze(self, only_initial_gaze=False):
        df = self.get_gaze_df()
        trial_number = self.get_trial_id()
        image = self.stimulus
        session = image.session
        image_id = image.image_id
        image_intensity = image.intensity

        if self.excluded():
            print("Should not process excluded trial.")
            exit(-1)

        if only_initial_gaze:
            # Initial
            beginning = df["timestamp"][0]
            df = df[~(df['timestamp'] > beginning + 1000000 * exp.INITIAL_GAZE_SEC)]

        final_gaze_points = []
        final_gaze_points_for_big_file = []

        new_image_width = exp.STIMULUS_HEIGHT / exp.ASPECT_HEIGHT * exp.ASPECT_WIDTH
        x_offset = (new_image_width - exp.STIMULUS_WIDTH) / 2

        left = df["left_eye_gp"]
        right = df["right_eye_gp"]
        timestamps = df["timestamp"]

        size = len(left)

        # Roi
        rgb_im_detailed = get_aoi_for_session_and_id(self.stimulus.session.blockName, self.stimulus.image_id,
                                                     image_type="RGB")

        for i in range(size):
            left_tuple = string_to_tuple(left[i])
            right_tuple = string_to_tuple(right[i])
            system_time = timestamps[i]
            regions = {
                "left_eye": 0,
                "right_eye": 0,
                "between_eyes": 0,
                "nose":0,
                "mouth":0,
                "other_face":0,
                "out_of_image":0,
            }
    
            
            if left_tuple is not None and right_tuple is not None:
                average_tuple = ((left_tuple[0] + right_tuple[0]) / 2.0, (left_tuple[1] + right_tuple[1]) / 2.0)
                # fit image range/coord
                avg_gaze_x = (average_tuple[0] * new_image_width) - x_offset
                avg_gaze_y = (average_tuple[1] * exp.STIMULUS_HEIGHT)

                roi_detailed_name, roi_detailed_id = get_aoi_for_gaze_point(avg_gaze_x, avg_gaze_y,
                                                                            rgb_im_detailed)
                regions[roi_detailed_name] = 1
                if avg_gaze_x < exp.STIMULUS_WIDTH and avg_gaze_y < exp.STIMULUS_HEIGHT:
                    final_gaze_points.append(
                        (system_time, avg_gaze_x, avg_gaze_y,
                         roi_detailed_name, roi_detailed_id,
                         left_tuple[0], left_tuple[1], right_tuple[0], right_tuple[1]))

                    final_gaze_points_for_big_file.append(
                        (system_time, avg_gaze_x, avg_gaze_y,
                         trial_number, session.blockName, image_id, image_intensity,
                         roi_detailed_name, roi_detailed_id,
                               regions["left_eye"],
                               regions["right_eye"],
                               regions["between_eyes"],
                               regions["nose"],
                               regions["mouth"],
                               regions["other_face"],
                               regions["out_of_image"],
                         left_tuple[0], left_tuple[1], right_tuple[0], right_tuple[1]))

        gaze_df = pd.DataFrame(final_gaze_points, columns=["timestamp", "x", "y",
                                                           "roi_detailed", "roi_detailed_id",
                                                           "left_eye_screen_x", "left_eye_screen_y",
                                                           "right_eye_screen_x", "right_eye_screen_y"])

        long_format_df = pd.DataFrame(final_gaze_points_for_big_file, columns=["timestamp", "x", "y",
                                                                               "trial_number", "expression",
                                                                               "image_id", "expression_intensity",
                                                                               "roi_detailed", "roi_detailed_id",
                                                                               "roi_left_eye",
                                                                                "roi_right_eye",
                                                                                "roi_between_eyes",
                                                                                "roi_nose",
                                                                                "roi_mouth",
                                                                                "roi_other_face",
                                                                                "roi_out_of_image",
                                                                               "left_eye_screen_x",
                                                                               "left_eye_screen_y",
                                                                               "right_eye_screen_x",
                                                                               "right_eye_screen_y"])
        return gaze_df, long_format_df

    def to_string(self):
        return "Trial - id: %s; image: %s; rk: %s; rt: %s" % (
            self.overall_trial_n, self.stimulus.image_id, self.response, self.response_time)
