
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


import random
import matplotlib.colors as clr
import glob, os

PLOTS_DIR_ROOT = "%splots_gaze_distribution/%s_roi%s/"


def getSavePath(save_path,aoi_type,initial,session_name,df_type):
    initial_part = ""
    if initial:
        initial_part = "_initial"

    save_path_dir = PLOTS_DIR_ROOT % (save_path, aoi_type, initial_part)
    save_path_file = save_path_dir + "%s_%s_%s.png" % (aoi_type,df_type,session_name)
    return save_path_dir, save_path_file


def plotAllImagesDetailed(df,savePath,subject,sessionName,skipIfExists, initial = False, n=0):
    save_path_dir, save_path_file = getSavePath(savePath,"detailed",initial,sessionName, "images")
    if skipIfExists and os.path.exists(save_path_file):
        return
    os.makedirs(save_path_dir, exist_ok=True)

    #####
    fig, ax = plt.subplots()
    bars = [
        ((df["eyes"])/df["gaze_time_sec"], "white", "EYES"),
        (df["nose"]/df["gaze_time_sec"], "grey", "NOSE"),
        (df["mouth"] / df["gaze_time_sec"], "black", "MOUTH")
    ]
    if n==0:
        configureAx(ax, bars, "Image Number", sessionName, "Subject: %s" % subject, 12)
    else:
        label = "Ethnicity: %s (n = %s)" % (subject, n)
        configureAx(ax, bars, "Image Number", sessionName, label, 12)
    #####

    plt.savefig(save_path_file)
    plt.close('all')

def plotIntensityDetailed(df,savePath,subject,sessionName,skipIfExists, initial = False, n = 0):
    save_path_dir, save_path_file = getSavePath(savePath,"detailed",initial,sessionName, "intensity")

    if skipIfExists and os.path.exists(save_path_file):
        return
    os.makedirs(save_path_dir, exist_ok=True)

    #####
    fig, ax = plt.subplots()
    bars = [
        ((df["eyes"])/df["gaze_time_sec"], "white", "EYES"),
        (df["nose"]/df["gaze_time_sec"], "grey", "NOSE"),
        (df["mouth"] / df["gaze_time_sec"], "black", "MOUTH")
    ]
    if n==0:
        configureAx(ax,bars,"Intensity",sessionName,"Subject: %s" % subject,4)
    else:
        label = "Ethnicity: %s (n = %s)" % (subject, n)
        configureAx(ax,bars,"Intensity",sessionName,label,4)
    #####

    plt.savefig(save_path_file)
    plt.close('all')

def configureAx(ax,bars, xlabel,title,description,indexCount,ylabel="%",ylim=100.0):
    bar_width = 0.20
    index = np.arange(indexCount)

    iteration = 0
    for bar in bars:
        ax.bar(index + bar_width*iteration, bar[0]*100, bar_width, color=bar[1], edgecolor='black', label=bar[2])
        iteration = iteration + 1

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0.0,ylim)
    ax.set_title(title)
    ax.set_xticks(index + bar_width)

    ticklabel = list(range(1, indexCount+1))
    ticklabel = [str(l) for l in ticklabel]
    ax.set_xticklabels(ticklabel)
    ax.legend(prop={'size': 13})
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95,description, transform=ax.transAxes, fontsize=13,verticalalignment='top', bbox=props)
