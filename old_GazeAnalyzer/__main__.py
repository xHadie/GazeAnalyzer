import tkinter
from tkinter import Frame
from tkinter import messagebox

import sys
import yawningExperiment
import threading


class Application(Frame):
    subjects = None
    skip_if_existing = None
    only_selected = None

    plot_fullgaze_selected = None
    plot_initialgaze_selected = None

    heatmap_fullgaze_selected = None
    heatmap_initialgaze_selected = None

    t = None

    def __init__(self, parent):
        self.parent = parent
        self.t = None

        Frame.__init__(self, parent)
        self.subjects = tkinter.StringVar()
        self.subjects.set("WS_MS")

        def on_closing():
            global t

            if t is not None:
                print("\n\n"
                      "####################################################\n"
                      "WARNING: Cannot cancel - a process is still running\n"
                      "Cancel it first!\n"
                      "####################################################\n")
            else:
                parent.destroy()

        parent.protocol("WM_DELETE_WINDOW", on_closing)

        self.skip_if_existing = tkinter.BooleanVar()
        self.skip_if_existing.set(False)

        self.only_selected = tkinter.BooleanVar()

        self.heatmap_fullgaze_selected = tkinter.BooleanVar()
        self.heatmap_fullgaze_selected.set(True)

        self.heatmap_initialgaze_selected = tkinter.BooleanVar()
        self.heatmap_initialgaze_selected.set(True)

        self.plot_fullgaze_selected = tkinter.BooleanVar()
        self.plot_fullgaze_selected.set(True)

        self.plot_initialgaze_selected = tkinter.BooleanVar()
        self.plot_initialgaze_selected.set(True)

        self.master.grid_columnconfigure(0, weight=1, uniform="fred")
        self.master.grid_columnconfigure(1, weight=1, uniform="fred")
        self.master.grid_columnconfigure(2, weight=1, uniform="fred")

        # Row
        subject_info_label = tkinter.Label(self.master,
                                           text="Enter subject initials (seperated by comma), to run commands only for specified subjects. "
                                                "Leave empty to run for all subjects.")
        subject_info_label.grid(row=0, column=0, columnspan=2, sticky="we")

        # Row
        subject_label = tkinter.Label(self.master, text="Subjects (ex: AS_WW,WS_HA,AS_CHT):")
        subject_label.grid(row=1, column=0, sticky="we")

        subjectInput = tkinter.Entry(self.master, textvariable=self.subjects)
        subjectInput.grid(row=1, column=1, pady=10, padx=10, sticky="we")

        # Row
        skip_existing_cb = tkinter.Checkbutton(self.master, text="Skip if existing", variable=self.skip_if_existing,
                                               onvalue=True, offvalue=False)
        skip_existing_cb.grid(row=2, column=0, sticky="s")

        only_selected_cb = tkinter.Checkbutton(self.master, text="Only selected", variable=self.only_selected,
                                               onvalue=True, offvalue=False)
        only_selected_cb.grid(row=2, column=1, sticky="s")

        # Row
        generate_all = tkinter.Button(self.master, text="Generate All", background="white",
                                      command=lambda: btn_generate_combined_response_csvs())
        generate_all.grid(row=3, column=0, columnspan=3, pady=10, padx=10, sticky="nswe")

        ##################
        # FRAME
        reponse_frame = tkinter.LabelFrame(self.master, text="Reponse", background="lightgray")
        reponse_frame.grid(row=4, column=0, columnspan=1, pady=10, padx=10, sticky="nswe")
        reponse_frame.grid_columnconfigure(0, weight=1, uniform="fred")

        # Col
        response_individual_button = tkinter.Button(reponse_frame, text="Generate Individual Response CSVs",
                                                    command=lambda: btn_generate_individual_response_csvs())
        response_individual_button.grid(pady=10, padx=10, in_=reponse_frame, sticky="nswe")

        response_combined_button = tkinter.Button(reponse_frame, text="Generate Combined Response CSV",
                                                  command=lambda: btn_generate_combined_response_csvs())
        response_combined_button.grid(pady=10, padx=10, in_=reponse_frame, sticky="nswe")

        response_all_button = tkinter.Button(reponse_frame, text="Generate Response Time CSVs",
                                             command=lambda: btn_generate_response_time_csvs())
        response_all_button.grid(pady=10, padx=10, in_=reponse_frame,sticky="nswe")

        ##################
        # FRAME
        plot_frame = tkinter.LabelFrame(self.master, text="Gaze plots", background="lightgray")
        plot_frame.grid(row=4, column=1, columnspan=1, pady=10, padx=10, sticky="nswe")
        plot_frame.grid_columnconfigure(0, weight=1, uniform="fred")

        # Col
        plot_individual_button = tkinter.Button(plot_frame, text="Generate Individual plots",
                                                command=lambda: btn_generate_individual_plots())
        plot_individual_button.grid(pady=10, padx=10, in_=plot_frame, sticky="nswe")

        plot_combined_button = tkinter.Button(plot_frame, text="Generate Combined plots",
                                              command=lambda: btn_generate_combined_plots())
        plot_combined_button.grid(pady=10, padx=10, in_=plot_frame, sticky="nswe")

        heatmap_all_button = tkinter.Button(plot_frame, text="Generate Fixation Data",
                                            command=lambda: btn_generate_fixation_data())
        heatmap_all_button.grid(pady=10, padx=10, in_=plot_frame, sticky="nswe")

        saccade_data_button = tkinter.Button(plot_frame, text="Generate Saccade Data",
                                            command=lambda: btn_generate_saccade_data())
        saccade_data_button.grid(pady=10, padx=10, in_=plot_frame, sticky="nswe")

        plot_fullgaze_cb = tkinter.Checkbutton(plot_frame, background="lightgray", text="Full gaze",
                                               variable=self.plot_fullgaze_selected, onvalue=True, offvalue=False)
        plot_fullgaze_cb.grid(pady=10, padx=10, sticky="nswe")

        heatmap_initialgaze_cb = tkinter.Checkbutton(plot_frame, background="lightgray", text="Initial gaze",
                                                     variable=self.plot_initialgaze_selected, onvalue=True,
                                                     offvalue=False)
        heatmap_initialgaze_cb.grid(pady=10, padx=10, sticky="nswe")

        plot_all_button = tkinter.Button(plot_frame, text="ALL")
        plot_all_button.grid(pady=10, padx=10, in_=plot_frame, sticky="nswe")

        ##################
        # FRAME
        heatmap_frame = tkinter.LabelFrame(self.master, text="Heatmaps", background="lightgray")
        heatmap_frame.grid(row=4, column=2, columnspan=1, pady=10, padx=10, sticky="nswe")
        heatmap_frame.grid_columnconfigure(0, weight=1, uniform="fred")

        # Col
        heatmap_individual_button = tkinter.Button(heatmap_frame, text="Generate Individual Heatmaps",
                                                   command=lambda: btn_generate_individual_heatmaps())
        heatmap_individual_button.grid(pady=10, padx=10, in_=heatmap_frame, sticky="nswe")

        heatmap_combined_button = tkinter.Button(heatmap_frame, text="Generate Combined Heatmaps",
                                                 command=lambda: btn_generate_combined_heatmaps())
        heatmap_combined_button.grid(pady=10, padx=10, in_=heatmap_frame, sticky="nswe")

        heatmap_fullgaze_cb = tkinter.Checkbutton(heatmap_frame, background="lightgray", text="Full gaze",
                                                  variable=self.heatmap_fullgaze_selected, onvalue=True, offvalue=False)
        heatmap_fullgaze_cb.grid(pady=10, padx=10, sticky="nswe")

        heatmap_initialgaze_cb = tkinter.Checkbutton(heatmap_frame, background="lightgray", text="Initial gaze",
                                                     variable=self.heatmap_initialgaze_selected, onvalue=True,
                                                     offvalue=False)
        heatmap_initialgaze_cb.grid(pady=10, padx=10, sticky="nswe")

        # Row
        text = tkinter.Text(height=10)
        text.grid(column=0, row=6, columnspan=3, padx=10, sticky="WE")

        cancel_command = tkinter.Button(self.master, text="Cancel running process",
                                        command=lambda: cancelCurrentRunningThread())
        cancel_command.grid(column=2, row=7, pady=10, padx=10, sticky="s")

        printLogger = PrintLogger(text)
        sys.stdout = printLogger

        # put HERE the "onLoad()" code ###
        self.experiment = yawningExperiment.YawningExperiment()
        print("Loading subject data.")
        print("Please wait...")
        self.after(2000, func=lambda: initYawningExperiment())

        def initYawningExperiment():
            global t

            def worker():
                global t
                self.experiment.init()
                print("Loaded session data for all subjects!")
                done()
                t = None

            t = threading.Thread(target=lambda: worker())
            t.start()

        # RESPONSE
        def btn_generate_individual_response_csvs():
            runThreadedCommand(self.experiment.generateIndividualResponseCsv, getSubjects(),
                               self.skip_if_existing.get())

        def btn_generate_combined_response_csvs():
            runThreadedCommand(self.experiment.generateCombinedResponseCsv)

        def btn_generate_response_time_csvs():
            runThreadedCommand(self.experiment.generateResponseTimeCsv)

        # PLOTS
        def btn_generate_individual_plots():
            runThreadedCommand(self.experiment.generateIndividualAoiDics, getSubjects(), self.skip_if_existing.get(),
                               self.heatmap_fullgaze_selected.get(), self.heatmap_initialgaze_selected.get())

        def btn_generate_combined_plots():
            runThreadedCommand(self.experiment.generateAoiDataFromAllSubjects)

        def btn_generate_fixation_data():
            runThreadedCommand(self.experiment.generateFixationData, getSubjects())

        def btn_generate_saccade_data():
            runThreadedCommand(self.experiment.generate_saccade_data, getSubjects())
        # HEATMAPS
        def btn_generate_individual_heatmaps():
            runThreadedCommand(self.experiment.generateIndividualHeatmaps, getSubjects(), self.skip_if_existing.get(),
                               self.heatmap_fullgaze_selected.get(), self.heatmap_initialgaze_selected.get())

        def btn_generate_combined_heatmaps():
            runThreadedCommand(self.experiment.generateCombinedHeatmaps, self.skip_if_existing.get(),
                               self.heatmap_fullgaze_selected.get(), self.heatmap_initialgaze_selected.get())

        ###### HELPERS ######
        def cancelCurrentRunningThread():
            def worker():
                global t
                if t is not None:
                    yawningExperiment.KILL_THREAD = True
                    t.join()
                    print("--- CANCELLED ---")
                    yawningExperiment.KILL_THREAD = False
                t = None

            thread_killer_thread = threading.Thread(target=lambda: worker())
            thread_killer_thread.start()

        def runThreadedCommand(function, *args):
            if not self.experiment.ready:
                return

            global t

            if t is not None:
                print("INFO: Could not run command - Wait until current process is finished.")
                return

            def worker():
                global t
                clear()
                function(*args)
                done()
                t = None

            t = threading.Thread(target=lambda: worker())
            t.start()

        def done():
            print("")
            print("----------------DONE-----------------")

        def clear():
            sys.stdout.clear()

        def getSubjects():
            subjectString = self.subjects.get()
            subjectString = subjectString.replace(" ", "")
            subjectList = subjectString.split(",")
            try:
                subjectList.remove("")
            except ValueError:
                pass
            return subjectList


class PrintLogger:  # create file like object

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.tag_configure("last_insert")

    def write(self, the_string):
        self.text_widget.configure(state="normal")
        self.text_widget.tag_remove("last_insert", "1.0", "end")
        self.text_widget.insert("end", the_string, "last_insert")
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def overwrite(self, the_string):
        self.text_widget.configure(state="normal")
        last_insert = self.text_widget.tag_ranges("last_insert")
        self.text_widget.delete(last_insert[0], last_insert[1])
        self.write(the_string)

    def flush(self):  # needed for file like object
        pass

    def clear(self):
        self.text_widget.configure(state="normal")
        self.text_widget.delete('1.0', tkinter.END)

    def progressBar(self, message, value, endvalue, bar_length=20):
        percent = float(value) / endvalue
        arrow = '=' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(arrow))

        self.overwrite("\n\r[{1}] {2}% - {0}".format(message, arrow + spaces, int(round(percent * 100))))
        if endvalue == value:
            print("")


if __name__ == '__main__':
    root = tkinter.Tk()

    app = Application(root)
    app.master.title('Yawning Experiment - Data Analyzer')

    app.mainloop()
