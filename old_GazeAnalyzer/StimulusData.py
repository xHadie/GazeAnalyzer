import pandas as pd
import TrialData as TD
import yawningExperiment
import statistics


class StimulusData:
    def __init__(self, image_id, stimulus_data, session):
        self.image_id = image_id
        self.session = session
        self.stimulus_data = stimulus_data
        self.trials = []
        self.intensity = self.__calc_intensity()

        appearance_index = 1
        for index, row in stimulus_data.iterrows():
            self.trials.append(
                TD.TrialData(self, row, appearance_index))
            appearance_index = appearance_index + 1

    def get_valid_trials(self):
        return [t for t in self.trials if not t.excluded()]

    def get_yes_rate(self):
        yes_count = self.get_yes_count()
        valid_trials = len(self.get_valid_trials())
        if valid_trials == 0:
            return 0
        return yes_count / valid_trials

    def get_yes_count(self):
        return sum(1 for trial in self.get_valid_trials() if trial.response == TD.TrialData.YES_RESPONSE)

    def get_no_count(self):
        return sum(1 for trial in self.get_valid_trials() if trial.response == TD.TrialData.NO_RESPONSE)

    def __calc_intensity(self):
        """
        :return intensity in [1,2,3,4,5]
        """
        intensity_index = ((self.image_id - 1) % yawningExperiment.NUMBER_OF_INTENSITIES) + 1
        return intensity_index

    def get_response_time_mean(self, exclude_trials=False):
        if exclude_trials:
            return statistics.mean([trial.response_time for trial in self.get_valid_trials()])
        else:
            return statistics.mean([trial.response_time for trial in self.trials])
