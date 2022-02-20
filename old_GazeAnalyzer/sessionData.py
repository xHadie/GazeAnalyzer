import yawningExperiment
from PIL import Image
import math
import pandas as pd
import statistics
import StimulusData as SD


class SessionData:
    YES_RESPONSE = "YES"
    NO_RESPONSE = "NO"

    def __keyToResponse(self, key):
        if key == "n" or key == "s" or key == "f":
            return self.NO_RESPONSE
        if key == "y" or key == "l" or key == "j":
            return self.YES_RESPONSE
        raise BaseException("NOT HANDLED KEY %s in %s for %s" % (key, self.blockName, self.subject.initials))

    def _get_condition_dir_from_key(self):
        if self.blockName == "smile":
            return "/1/"

        if self.blockName == "angry":
            return "/2/"

        if self.blockName == "yawn":
            return "/3/"

    def get_data_dir(self):
        return yawningExperiment.DATA_PATH + self.subject.initials + self._get_condition_dir_from_key()

    def __init__(self, subject, data, blockName):

        self.rawData = data
        self.subject = subject
        if "imageSizeScale" in data:
            self.imageScale = data["imageSizeScale"][2]
        else:
            self.imageScale = 1.0
        self.data = {}
        self.responseTimeData = {}
        self.stimulusData = {}
        self.gazeData = {}
        self.blockName = blockName

        if self.blockName == "yawn":
            self.blockId = 3

        if self.blockName == "angry":
            self.blockId = 2

        if self.blockName == "smile":
            self.blockId = 1

        # Create StimulusData instance per image:
        for i in range(yawningExperiment.NUMBER_OF_STIMULUS):
            try:
                image_index = i + 1
                stimulus_data = data[data['%s_block_loop.thisIndex' % blockName] == image_index-1]
                self.stimulusData[image_index] = SD.StimulusData(image_index, stimulus_data, self)
            except KeyError:
                print("error loading session data for subject "+ self.subject.initials + " at image index " + str(image_index))

        for index, row in data.iterrows():
            response = self.__keyToResponse(row['key_resp_%s.keys' % blockName])
            imageIndex = row['%s_block_loop.thisIndex' % blockName]

            if "%s" % (imageIndex) not in self.data:
                self.data["%s" % imageIndex] = {self.NO_RESPONSE: 0, self.YES_RESPONSE: 0}
                self.responseTimeData[int(imageIndex)] = {}

            responseTime = float(row['key_resp_%s.rt' % blockName])
            repeat_number = int(row['%s_block_loop.thisRepN' % blockName])
            self.responseTimeData[int(imageIndex)][repeat_number] = responseTime
            self.data["%s" % imageIndex][response] += 1

    def get_stimulus_data(self, index):
        return self.stimulusData[index]

    def get_intensity_response_data(self, intensity):
        """
        :param intensity: 1,2,3,4 are valid input
        :return:
        """
        yes = 0
        no = 0
        if intensity not in [1, 2, 3, 4]:
            print("Invalid intensity %s" % intensity)
            exit(-1)

        for image in self.stimulusData.values():
            if image.intensity == intensity:
                yes = yes + image.get_yes_count()
                no = no + image.get_no_count()
        try:
            yes_rate = yes / (yes + no)
        except ZeroDivisionError:
            print("DIVISION ERROR")
            for image in self.stimulusData.values():
                if image.intensity == intensity:
                    print("For image: yes (%s) no (%s)" % (image.get_yes_count(),image.get_no_count()))
            raise ZeroDivisionError("For intensity %s - %s using yes: %s and no: %s" % (self.blockName, intensity, yes, no))
        return yes_rate, yes, no

    def getImageScaling(self):
        return self.imageScale

    def createResponseTimeSeries(self):
        response_time_dic = {}

        for index, row in self.rawData.iterrows():
            imageIndex = int(row['%s_block_loop.thisIndex' % self.blockName]) + 1
            if imageIndex not in response_time_dic:
                response_time_dic[imageIndex] = []

            responseTime = float(row['key_resp_%s.rt' % self.blockName])
            response_time_dic[imageIndex].append(responseTime)

        subject_column_dic = {}
        all_trials_rts = []  # all rt, needed for calculating stdv etc
        included_all_tials_rts = []  # only included, needed for calc values like final mean

        # Create overall list of rt for stat vars:
        for key in sorted(response_time_dic.keys()):
            for response_time in response_time_dic[key]:
                all_trials_rts.append(response_time)

        # statistical vars:
        std_dv = statistics.stdev(all_trials_rts)
        mean_all = statistics.mean(all_trials_rts)
        n = len(all_trials_rts)
        inclusion_threshold = mean_all + 2.5 * std_dv

        # Calc num excluded trials:
        excluded = 0
        for rt in all_trials_rts:
            if rt > inclusion_threshold:
                excluded = excluded + 1

        int_1_trials_sum = 0
        int_1_trials_n = 0

        int_2_trials_sum = 0
        int_2_trials_n = 0

        int_3_trials_sum = 0
        int_3_trials_n = 0

        int_4_trials_sum = 0
        int_4_trials_n = 0
        # Response time per image / per trial iteration:
        for key in sorted(response_time_dic.keys()):
            iter = 1
            image_trials_rts = []

            sum_for_image_only_included = 0
            image_n = 0
            for response_time in response_time_dic[key]:
                image_trials_rts.append(response_time)
                subject_column_dic["%s%s_%s" % (self.blockName, key, iter)] = response_time
                iter += 1

                if response_time < inclusion_threshold:
                    included_all_tials_rts.append(response_time)
                    sum_for_image_only_included = sum_for_image_only_included + response_time
                    image_n = image_n + 1

            subject_column_dic["%s%s_mean" % (self.blockName, key)] = statistics.mean(image_trials_rts)

            # Do something for intensities:
            intensity_index = (key - 1) % yawningExperiment.settings["NUMBER_OF_INTENSITIES"]
            if intensity_index == 0:
                int_1_trials_sum = int_1_trials_sum + sum_for_image_only_included
                int_1_trials_n = int_1_trials_n + image_n
            elif intensity_index == 1:
                int_2_trials_sum = int_2_trials_sum + sum_for_image_only_included
                int_2_trials_n = int_2_trials_n + image_n
            elif intensity_index == 2:
                int_3_trials_sum = int_3_trials_sum + sum_for_image_only_included
                int_3_trials_n = int_3_trials_n + image_n
            elif intensity_index == 3:
                int_4_trials_sum = int_4_trials_sum + sum_for_image_only_included
                int_4_trials_n = int_4_trials_n + image_n

        # Create end columns:
        subject_column_dic["%s_n" % self.blockName] = n
        subject_column_dic["%s_mean" % self.blockName] = mean_all
        subject_column_dic["%s_mean_included" % self.blockName] = statistics.mean(included_all_tials_rts)
        subject_column_dic["%s_SD" % self.blockName] = std_dv
        subject_column_dic["%s_2SD" % self.blockName] = 2 * std_dv
        subject_column_dic["%s_2.5SD" % self.blockName] = 2.5 * std_dv
        subject_column_dic["%s_3SD" % self.blockName] = 3 * std_dv
        subject_column_dic["%s_M+SD" % self.blockName] = mean_all + std_dv
        subject_column_dic["%s_M+2SD" % self.blockName] = mean_all + 2 * std_dv
        subject_column_dic["%s_M+2.5SD" % self.blockName] = mean_all + 2.5 * std_dv
        subject_column_dic[("%s_excluded_count" % self.blockName)] = excluded
        subject_column_dic[("%s_excluded_" % self.blockName) + "%"] = (excluded / n) * 100
        subject_column_dic["%s_M+3SD" % self.blockName] = mean_all + 3 * std_dv
        subject_column_dic["%s_intensity_1_n" % self.blockName] = int_1_trials_n
        subject_column_dic["%s_intensity_1_mean" % self.blockName] = int_1_trials_sum / int_1_trials_n
        subject_column_dic["%s_intensity_2_n" % self.blockName] = int_2_trials_n
        subject_column_dic["%s_intensity_2_mean" % self.blockName] = int_2_trials_sum / int_2_trials_n
        subject_column_dic["%s_intensity_3_n" % self.blockName] = int_3_trials_n
        subject_column_dic["%s_intensity_3_mean" % self.blockName] = int_3_trials_sum / int_3_trials_n
        subject_column_dic["%s_intensity_4_n" % self.blockName] = int_4_trials_n
        subject_column_dic["%s_intensity_4_mean" % self.blockName] = int_4_trials_sum / int_4_trials_n

        response_time_series = pd.Series(subject_column_dic)
        return response_time_series


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
