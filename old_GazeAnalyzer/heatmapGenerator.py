from heatmappy import Heatmapper
from PIL import Image, ImageFilter
import pandas as pd
import math
import numpy as np
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter

from mpl_toolkits.axes_grid1 import make_axes_locatable
import random
import glob, os
import sys
import yawningExperiment

aspectHeight = 3
aspectWidth = 4
imageWidth = 1024
imageHeight = 768
newImageWidth = imageHeight / aspectHeight * aspectWidth
screenHeight = imageHeight;
screenWidth = (imageHeight / imageWidth) * screenHeight
xOffset = (newImageWidth - imageWidth) / 2

COLOR_MAP = None
from matplotlib.colors import LinearSegmentedColormap


def initColorMap():  # get colormap
    global COLOR_MAP
    ncolors = 256
    color_array = plt.get_cmap('viridis')(range(ncolors))

    # change alpha values
    alpha_end_point = ncolors // 4
    alphas = np.linspace(0.5, 1.0, alpha_end_point)
    for i in range(alpha_end_point):
        color_array[:, -1][i] = alphas[i]

    color_array[:, -1] = np.linspace(1.0, 1.0, ncolors)
    color_array[:, -1][0] = 0

    # create a colormap object
    COLOR_MAP = LinearSegmentedColormap.from_list(name='viridis_alpha', colors=color_array)

def initColorMapDiverging():  # get colormap
    global COLOR_MAP
    ncolors = 256
    color_array = plt.get_cmap('PiYG')(range(ncolors))

    # change alpha values
    color_array[:, -1] = np.linspace(1.0, 1.0, ncolors)
    color_array[:, -1][ncolors//2] = 0

    # create a colormap object
    COLOR_MAP = LinearSegmentedColormap.from_list(name='viridis_alpha', colors=color_array)



def getGazeListFromCsv(csvPath):
    gaze_df = pd.read_csv(csvPath)
    x = gaze_df["x"]
    y = gaze_df["y"]

    gaze_list = list(zip(x, y))
    return gaze_list


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


PRINTED = False


def calcSkipForGazeType(settingSkipIfExisting, settingCreateFull, settingCreateInitial, fullSavePath, initialSavePath):
    skipFull = False
    skipInitial = False
    if settingSkipIfExisting:
        if settingCreateFull:
            if os.path.exists(fullSavePath):
                skipFull = True
        else:
            skipFull = True

        if settingCreateInitial:
            if os.path.exists(initialSavePath):
                skipInitial = True
        else:
            skipInitial = True

    return skipFull, skipInitial


def getImageForSessionAndId(sessionName, imageId, imageScale, newSize):
    STIMULI_DIR = "./stimulus/"
    imageNameBase = ""
    if sessionName == "smile":
        imageNameBase = STIMULI_DIR + "StiSmile/smile_"
    if sessionName == "angry":
        imageNameBase = STIMULI_DIR + "StiAngry/angry_"
    if sessionName == "yawn":
        imageNameBase = STIMULI_DIR + "StiYawn/yawning_"
    image = Image.open(imageNameBase + str(imageId) + ".jpg")

    image = image.resize(newSize)
    image = resize_canvas(image, canvas_width=newSize[0], canvas_height=newSize[1])
    return image


class HeatmapGenerator(Heatmapper):
    def __init__(self, paths, settings):
        super().__init__(point_diameter=90,  # the size of each point to be drawn
                         point_strength=0.025,  # the strength, between 0 and 1, of each point to be drawn
                         opacity=0.9,  # the opacity of the heatmap layer
                         colours='default',  # 'default' or 'reveal'
                         # OR a matplotlib LinearSegmentedColorMap object
                         # OR the path to a horizontal scale image
                         grey_heatmapper='PIL'  # The object responsible for drawing the points
                         )
        self.settings = settings
        self.paths = paths

    def normalizePixelCountMatrix(self, m):
        max_value = m.max()
        m = np.true_divide(m, max_value)
        return m

    def makeIntensityDics(self):
        intensity_gaze_dic = {}
        intensity_gaze_dic_initial = {}

        for i in range(self.settings["NUMBER_OF_INTENSITIES"]):
            intensity_gaze_dic[str(i)] = []
            intensity_gaze_dic_initial[str(i)] = []

        return intensity_gaze_dic, intensity_gaze_dic_initial

    def createHeatmapForEthnicities(self, subjectList, skipIfExisting, createFullGazeHeatmaps, createInitialGazeHeatmaps):
        if not createFullGazeHeatmaps and not createInitialGazeHeatmaps:
            print("WARNING: No gaze version selected for heatmap generation!")
            return

        ethnicity_dic = {}
        ethnicity_dic_initial = {}

        for ethnicity in self.settings["ethnicities"]:
            print("Creating heatmaps for ethnicity %s " % ethnicity)
            ethnicity_dic[ethnicity] = {}
            ethnicity_dic_initial[ethnicity] = {}
            subject_n = 0
            count_subjects = True
            for sessionName in self.settings["conditions"]:
                ethnicity_dic[ethnicity][sessionName] = {"intensity" :{}, "image": {}}
                ethnicity_dic_initial[ethnicity][sessionName] = {"intensity" :{}, "image": {}}


                save_path = self.paths["RESULT_DIR"] + "ethnicties/%s/heatmaps/%s/" % (ethnicity, sessionName)
                save_path_initial = self.paths["RESULT_DIR"] + "ethnicties/%s/heatmaps/%s_initial/" % (
                    ethnicity, sessionName)

                if createFullGazeHeatmaps:
                    os.makedirs(save_path, exist_ok=True)

                if createInitialGazeHeatmaps:
                    os.makedirs(save_path_initial, exist_ok=True)

                intensity_gaze_dic, intensity_gaze_dic_initial = self.makeIntensityDics()

                for imageId in range(self.settings["NUMBER_OF_STIMULUS"]):
                    intensity_dic_key = str(imageId % self.settings["NUMBER_OF_INTENSITIES"])

                    whole_gaze_points = []
                    initial_gaze_points = []

                    current_image_id = imageId + 1
                    # Setup paths
                    image_heatmap_file_name = "%s_%s - %s.png" % (sessionName, current_image_id, ethnicity)
                    full_save_path = save_path + image_heatmap_file_name
                    full_save_path_initial = save_path_initial + image_heatmap_file_name

                    skipFull, skipInitial = calcSkipForGazeType(skipIfExisting, createFullGazeHeatmaps,
                                                                createInitialGazeHeatmaps, full_save_path,
                                                                full_save_path_initial)

                    if skipFull and skipInitial:
                        continue

                    for subject in subjectList:
                        subject.loadSessionData()
                        if subject.nationality.startswith(ethnicity):
                            if count_subjects:
                                subject_n = subject_n + 1

                            subject_name = subject.initials

                            if yawningExperiment.KILL_THREAD:
                                yawningExperiment.cancelInfo()
                                return

                            whole_gaze_data_path = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/%s.csv" % (
                                subject_name, sessionName, current_image_id)
                            initial_gaze_data_path = self.paths[
                                                         "RESULT_DIR"] + "subjects/%s/gaze_results/%s/%s_initial.csv" % (
                                subject_name, sessionName, current_image_id)

                            subject.createGazeCsvForSubjectIfMissing(whole_gaze_data_path)

                            if not skipFull:
                                gaze_list = getGazeListFromCsv(whole_gaze_data_path)
                                whole_gaze_points.extend(gaze_list)
                                intensity_gaze_dic[intensity_dic_key].extend(gaze_list)

                            if not skipInitial:
                                gaze_list = getGazeListFromCsv(initial_gaze_data_path)
                                initial_gaze_points.extend(gaze_list)
                                intensity_gaze_dic_initial[intensity_dic_key].extend(gaze_list)

                    count_subjects = False

                    IMAGE_SCALE = 1.0
                    if not skipFull:
                        ethnicity_dic[ethnicity][sessionName]["image"][imageId] = whole_gaze_points
                        success = self.savePixelArrayHeatmap(current_image_id, sessionName, IMAGE_SCALE,
                                                            full_save_path, ethnicity,gaze_list=whole_gaze_points, n=subject_n)
                        if not success:
                            return

                    if not skipInitial:
                        ethnicity_dic_initial[ethnicity][sessionName]["image"][imageId] = initial_gaze_points
                        success = self.savePixelArrayHeatmap(current_image_id, sessionName, IMAGE_SCALE,
                                                            full_save_path_initial, ethnicity,gaze_list=initial_gaze_points, n=subject_n)
                        if not success:
                            return

                    self.printProgress(ethnicity, sessionName, current_image_id)


                for i in intensity_gaze_dic:
                    intensity_file_name = "intensity_%s_%s - %s.png" % (sessionName, i, ethnicity)
                    full_save_path = save_path + intensity_file_name
                    full_save_path_initial = save_path_initial + intensity_file_name

                    skipFull, skipInitial = calcSkipForGazeType(skipIfExisting, createFullGazeHeatmaps,
                                                                createInitialGazeHeatmaps, full_save_path,
                                                                full_save_path_initial)

                    if not skipFull:
                        gaze_list = intensity_gaze_dic[i]
                        ethnicity_dic[ethnicity][sessionName]["intensity"][i] = gaze_list
                        success = self.savePixelArrayHeatmap(int(i) + 1, sessionName, IMAGE_SCALE,
                                                             full_save_path, ethnicity, intensity=True, gaze_list=gaze_list, n=subject_n)
                        if not success:
                            return

                    if not skipInitial:
                        gaze_list = intensity_gaze_dic_initial[i]
                        ethnicity_dic_initial[ethnicity][sessionName]["intensity"][i] = gaze_list

                        success = self.savePixelArrayHeatmap(int(i) + 1, sessionName, IMAGE_SCALE,
                                                             full_save_path_initial, ethnicity, intensity=True, gaze_list=gaze_list, n=subject_n)
                        if not success:
                            return

                    self.printProgress(ethnicity, sessionName, self.settings["NUMBER_OF_STIMULUS"] + int(i) + 1)


        if not skipFull:
            save_path = self.paths["RESULT_DIR"] + "ethnicties/difference/%s/%s/"
            self.compareEnthicities(ethnicity_dic,save_path)

        if not skipInitial:
            save_path_initial = self.paths["RESULT_DIR"] + "ethnicties/difference/%s/%s_initial/"
            self.compareEnthicities(ethnicity_dic_initial, save_path_initial)

    def get_dif_matrix(self,gaze_list_1,gaze_list_2):
        matrix_1 = self.gazeListToScaledMatrix(gaze_list_1)
        matrix_2 = self.gazeListToScaledMatrix(gaze_list_2)

        # normalize values between 0-1
        matrix_1 = self.normalizePixelCountMatrix(matrix_1)
        matrix_2 = self.normalizePixelCountMatrix(matrix_2)

        dif_matrix = matrix_1

        for x in range(len(matrix_1)):
            for y in range(len(matrix_1)):
                dif_matrix[x][y] = dif_matrix[x][y] - matrix_2[x][y]

        return dif_matrix

    def compareEnthicities(self, ethnicityDic, save_path):

        compared = []

        for e1 in ethnicityDic:
            for e2 in ethnicityDic:
                comb_key_name = e1 + "-" + e2
                comb_key_name2 = e2 + "-" + e1
                if e2 == "JP":
                    continue
                if e1 != e2 and comb_key_name not in compared and comb_key_name2 not in compared:
                    print("Creating DIF heatmap between %s and %s" % (e1,e2))
                    compared.append(comb_key_name)

                    for condition in ethnicityDic[e1]:
                        print("For cond: %s" % condition)

                        fina_save_path = save_path % (comb_key_name,condition)
                        os.makedirs(fina_save_path, exist_ok=True)

                        for image in ethnicityDic[e1][condition]["image"]:
                            image_file_name = "%s_%s - %s.png" % (condition, image, comb_key_name)

                            image_gaze_list_1 = ethnicityDic[e1][condition]["image"][image]
                            image_gaze_list_2 = ethnicityDic[e2][condition]["image"][image]
                            image_dif_matrix = self.get_dif_matrix(image_gaze_list_1, image_gaze_list_2)
                            image_dif_matrix[0][0] = 1.0
                            image_dif_matrix[0][1] = -1.0


                            print("done for %s - %s" % (condition, image))
                            self.savePixelArrayHeatmap(int(image) + 1, condition, 1.0, fina_save_path + image_file_name, comb_key_name, gaze_matrix=image_dif_matrix)

                        for intensity in ethnicityDic[e1][condition]["intensity"]:
                            intensity_file_name = "intensity_%s_%s - %s.png" % (condition, intensity, comb_key_name)

                            intensity_gaze_list_1 = ethnicityDic[e1][condition]["intensity"][intensity]
                            intensity_gaze_list_2 = ethnicityDic[e2][condition]["intensity"][intensity]
                            intensity_dif_matrix = self.get_dif_matrix(intensity_gaze_list_1, intensity_gaze_list_2)
                            intensity_dif_matrix[0][0] = 1.0
                            intensity_dif_matrix[0][1] = -1.0
                            self.savePixelArrayHeatmap(int(intensity) + 1, condition, 1.0, fina_save_path + intensity_file_name, comb_key_name, intensity=True, gaze_matrix=intensity_dif_matrix)

                            print("done for %s - %s" % (condition, intensity))



    def createHeatmapForSubjects(self, subjectList, skipIfExisting, createFullGazeHeatmaps, createInitialGazeHeatmaps):
        if not createFullGazeHeatmaps and not createInitialGazeHeatmaps:
            print("WARNING: No gaze version selected for heatmap generation!")
            return
        for subject in subjectList:
            subject.loadSessionData()
            print("Creating heatmaps for %s " % subject.initials)
            subject_name = subject.initials

            for sessionName in subject.sessionData:
                save_path = self.paths["RESULT_DIR"] + "subjects/%s/heatmaps/%s/" % (subject_name, sessionName)
                save_path_initial = self.paths["RESULT_DIR"] + "subjects/%s/heatmaps/%s_initial/" % (
                    subject_name, sessionName)

                if createFullGazeHeatmaps:
                    os.makedirs(save_path, exist_ok=True)

                if createInitialGazeHeatmaps:
                    os.makedirs(save_path_initial, exist_ok=True)

                # INTESNITY SETUP

                intensity_gaze_dic, intensity_gaze_dic_initial = self.makeIntensityDics()

                session_data = subject.sessionData[sessionName]
                image_scale = 1.0
                for imageId in range(self.settings["NUMBER_OF_STIMULUS"]):
                    if yawningExperiment.KILL_THREAD:
                        yawningExperiment.cancelInfo()
                        return

                    current_image_id = imageId + 1
                    # Setup paths
                    image_heatmap_file_name = "%s_%s - %s.png" % (sessionName, current_image_id, subject_name)
                    full_save_path = save_path + image_heatmap_file_name
                    full_save_path_initial = save_path_initial + image_heatmap_file_name

                    skipFull, skipInitial = calcSkipForGazeType(skipIfExisting, createFullGazeHeatmaps,
                                                                createInitialGazeHeatmaps, full_save_path,
                                                                full_save_path_initial)
                    if skipFull and skipInitial:
                        continue

                    whole_gaze_data_path = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/%s.csv" % (
                        subject_name, sessionName, current_image_id)
                    initial_gaze_data_path = self.paths["RESULT_DIR"] + "subjects/%s/gaze_results/%s/%s_initial.csv" % (
                        subject_name, sessionName, current_image_id)

                    subject.createGazeCsvForSubjectIfMissing(whole_gaze_data_path)

                    intensity_dic_key = str(imageId % self.settings["NUMBER_OF_INTENSITIES"])
                    if not skipFull:
                        gaze_list = getGazeListFromCsv(whole_gaze_data_path)
                        success = self.savePixelArrayHeatmap(current_image_id, sessionName, image_scale,
                                                             full_save_path, subject_name, gaze_list=gaze_list)

                        intensity_gaze_dic[intensity_dic_key].extend(gaze_list)

                        if not success:
                            return

                    if not skipInitial:
                        gaze_list = getGazeListFromCsv(initial_gaze_data_path)
                        success = self.savePixelArrayHeatmap(current_image_id, sessionName, image_scale,
                                                             full_save_path_initial, subject_name, gaze_list=gaze_list)

                        intensity_gaze_dic_initial[intensity_dic_key].extend(gaze_list)

                        if not success:
                            return

                    self.printProgress(subject_name, sessionName, current_image_id)

                for i in intensity_gaze_dic:
                    intensity_file_name = "intensity_%s_%s - %s.png" % (sessionName, i, subject_name)
                    full_save_path = save_path + intensity_file_name
                    full_save_path_initial = save_path_initial + intensity_file_name

                    skipFull, skipInitial = calcSkipForGazeType(skipIfExisting, createFullGazeHeatmaps,
                                                                createInitialGazeHeatmaps, full_save_path,
                                                                full_save_path_initial)

                    if not skipFull:
                        gaze_list = intensity_gaze_dic[i]
                        success = self.savePixelArrayHeatmap(int(i) + 1, sessionName, image_scale, full_save_path,
                                                             subject_name, intensity=True, gaze_list=gaze_list)
                        if not success:
                            return

                    if not skipInitial:
                        gaze_list = intensity_gaze_dic_initial[i]
                        success = self.savePixelArrayHeatmap(int(i) + 1, sessionName, image_scale,
                                                             full_save_path_initial, subject_name,
                                                             intensity=True, gaze_list=gaze_list)
                        if not success:
                            return

                    self.printProgress(subject_name, sessionName, self.settings["NUMBER_OF_STIMULUS"] + int(i) + 1)

            print("")

    def printProgress(self, subjectName, sessionName, progress):
        sys.stdout.progressBar(
            "Create heatmaps for %s - %s" % (subjectName, sessionName), progress,
            self.settings["NUMBER_OF_STIMULUS"] + self.settings["NUMBER_OF_INTENSITIES"])


    def createAndSaveHeatmaps(self, image, gaze_list, savePath):
        x = 1.0 / float(len(gaze_list))
        Heatmapper.point_strength.fset(self, 0.005)
        heatmap = self.heatmap_on_img(gaze_list, image)
        heatmap = heatmap.filter(ImageFilter.BLUR)
        try:
            heatmap.save(savePath)
            return True
        except PermissionError:
            print("\n\n"
                  "################################################################\n"
                  "!!ERROR!! - Could not save heatmap (permission error)\n"
                  "Make sure you don't have any heatmap image opened and try again \n"
                  "################################################################\n\n")
            return False

    def getFullGazeTime(self, gazeList, intensity=False):
        frequency = 300.0
        ms_per_gaze_point = 1000.0 / frequency

        val = len(gazeList) / float(self.settings["LOOPS_PER_IMAGE"]) * ms_per_gaze_point
        if intensity:
            val = val / float(self.settings["IMAGES_PER_INTENSITY"])
        return val


    def gazeListToGazeMilliseconds(self, m, intensity=False, n=1):
        frequency = 300.0
        ms_per_gaze_point = 1000.0 / frequency
        m = np.true_divide(m, n)
        m = np.true_divide(m, float(self.settings["LOOPS_PER_IMAGE"]))
        if intensity:
            m = np.true_divide(m, float(self.settings["IMAGES_PER_INTENSITY"]))
        m = np.multiply(m, ms_per_gaze_point)
        return m

    def gazeListToScaledMatrix(self,gaze_list):
        scale_rate = self.settings["HEATMAP_IMAGE_SCALE"]
        gaze_list = [(x, y) for (x, y) in gaze_list if x < imageWidth and y < imageHeight]
        gaze_list = [(x / scale_rate, y / scale_rate) for (x, y) in gaze_list]

        gaze_matrix = np.zeros((imageHeight, imageWidth))

        for gazeTuple in gaze_list:

            difX = gazeTuple[0] - math.floor(gazeTuple[0])
            difY = gazeTuple[1] - math.floor(gazeTuple[1])

            x = None
            y = None

            if difX >= 0.5:
                x = math.ceil(gazeTuple[0])
            else:
                x = math.floor(gazeTuple[0])

            if difY >= 0.5:
                y = math.ceil(gazeTuple[1])
            else:
                y = math.floor(gazeTuple[1])

            x = int(x)
            y = int(y)

            gaze_matrix[y][x] = gaze_matrix[y][x] + 1.0

        return gaze_matrix

    def savePixelArrayHeatmap(self, image_id, condition, image_scale, savePath, subjectName, intensity=False, gaze_list=None, gaze_matrix=None, n = 1):
        scale_rate = self.settings["HEATMAP_IMAGE_SCALE"]
        using_difference_data = gaze_matrix is not None
        new_width = int(imageWidth * image_scale / scale_rate)
        new_height = int(imageHeight * image_scale / scale_rate)

        title = ""
        intensity_part = ""
        colorbar_format = "%.2f"
        colorbar_label = "difference between ethnicites"
        color_map = "PiYG"

        if intensity:
            intensity_part = "intensity-"

        if using_difference_data:

            title = "gaze difference (%s) on %s" % (subjectName, ("'%s-%s%s'" % (condition,intensity_part, image_id)))

        if not using_difference_data:
            gaze_matrix = self.gazeListToScaledMatrix(gaze_list)
            gaze_matrix = self.gazeListToGazeMilliseconds(gaze_matrix, intensity,n=n)

            initColorMap()
            colorbar_label = "gaze duration (milliseconds)"
            colorbar_format = "%.2f ms"
            title = "mean gaze duration for %s on %s:\n %.2f ms" % (subjectName, ("'%s-%s%s'" % (condition, intensity_part, image_id)), (self.getFullGazeTime(gaze_list, intensity) / n))

            color_map = COLOR_MAP

        max_value = gaze_matrix.max()
        min_value = gaze_matrix.min()

        # PLOT:
        fig, ax = plt.subplots()
        cax = make_axes_locatable(ax).append_axes('right', size='5%', pad=0.05)

        overlay_image = getImageForSessionAndId(condition, image_id, image_scale, (new_width, new_height))
        if not using_difference_data:
            ax.imshow(overlay_image, alpha=0.7)

        pix = ax.imshow(gaze_matrix, cmap=plt.get_cmap(color_map))

        if using_difference_data:
            ax.imshow(overlay_image, alpha=0.3)

        ax.set_title(title)
        ax.set_xlabel("width")
        ax.set_ylabel("height")

        # CROP TO INTERESTING IMAGE REGION:
        x_offset = 0.27
        y_offset = 0.04
        ax.set_xlim(0 + new_width * x_offset, new_width - new_width * x_offset)
        ax.set_ylim(new_height - new_height * y_offset, 0 + new_height * y_offset)

        # ADD SUBJECT INFO BOX:
        props_subject = dict(facecolor='white', alpha=0.5)
        ax.text(0.05, 0.95, "Subject: %s" % subjectName, transform=ax.transAxes, fontsize=10, verticalalignment='center', bbox=props_subject)


        # ADD COLORBAR
        ticks_list =  [min_value, (min_value + max_value) / 2.0, max_value]
        cbar = fig.colorbar(pix, cax=cax, format=colorbar_format, orientation='vertical',
                            ticks=ticks_list, label=colorbar_label)
        cbar.ax.set_yticklabels(ticks_list)
        cbar.draw_all()

        plt.savefig(savePath)
        plt.close('all')
        return True
