import sys
import pandas as pd
import irsdk
import os
import matplotlib
import pyautogui
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import queue
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
import time
import tkinter as tk
from tkinter import filedialog


class State:
    ir_connected = False


def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset your State variables
        state.last_car_setup_tick = -1
        # we are shutting down ir library (clearing all internal variables)
        ir.shutdown()
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        fig.tight_layout()


class LHP_LIVE_BRAKE_APP(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi('main.ui', self)
        self.resize(1000, 800)
        QtWidgets.QMainWindow.setWindowTitle(self, 'LHP Analytics Braking Tester')
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("LHP_Logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.threadpool = QtCore.QThreadPool()
        self.vehicles_list = ['USF Pro 2000', 'USF 2000', 'Formula 4', 'Formula Vee']

        self.vehicleBox.addItems(self.vehicles_list)
        self.vehicleBox.currentIndexChanged['QString'].connect(self.update_now)
        self.vehicleBox.setCurrentIndex(0)

        self.selectedVehicle = self.vehicles_list[self.vehicles_list.index(self.vehicleBox.currentText())]
        self.tracks_list = []
        try:
            with open('lap_path.txt') as f:
                contents = f.read()
                self.path = contents + "/"
        except:
            tk.Tk().withdraw()
            file_path = filedialog.askdirectory(title="File Location of baseline laps")
            with open('lap_path.txt', 'w') as f:
                f.write(file_path)
            self.path = file_path + "/"
        raw_tracks = os.listdir(self.path + self.selectedVehicle)
        for track in raw_tracks:
            self.tracks_list.append(track.replace('.csv', ''))

        self.trackBox.addItems(self.tracks_list)
        self.trackBox.setCurrentIndex(0)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas2 = MplCanvas(self, width=5, height=4, dpi=100)
        self.ui.gridLayout_4.addWidget(self.canvas, 2, 1, 1, 1)
        self.ui.gridLayout_4.addWidget(self.canvas2, 3, 1, 1, 1)
        self.reference_plot = None
        self.reference_plot2 = None
        self.q = queue.Queue(maxsize=20)

        self.vehicle = self.vehicles_list[0]
        self.window_length = 1000
        self.tolerance = 10
        self.channels = [1]
        self.interval = 10

        self.braking_zone_success = True

        length = 100

        self.plotdata = np.zeros((length, len(self.channels)))
        self.plotdata2 = np.zeros((length, len(self.channels)))

        self.update_plot()
        self.timer = QtCore.QTimer()
        # self.timer.setInterval(self.interval)  # msec
        # self.timer.timeout.connect(self.update_plot)
        # self.timer.start()
        self.lineEdit_3.textChanged['QString'].connect(self.update_tolerance)
        self.pushButton.clicked.connect(self.start_worker)
        self.reference_df = None

    def start_worker(self):
        worker = Worker(self.start_stream, )
        self.threadpool.start(worker)

    def start_stream(self):
        check_iracing()

        if state.ir_connected:
            has_braked = False
            braking_zone_saved = False
            selectedTrack = self.tracks_list[self.trackBox.currentIndex()]
            self.reference_df = pd.read_csv(self.path + self.selectedVehicle + "/" + selectedTrack + ".csv")
            self.lineEdit_3.setEnabled(False)
            self.vehicleBox.setEnabled(False)
            self.trackBox.setEnabled(False)
            self.pushButton.setEnabled(False)
            braking_zone_dist = 0
            while True:
                self.q.put(1)
                if not braking_zone_saved:
                    df_upcoming = self.reference_df.iloc[(self.reference_df['LapDist'] - (ir['LapDist'] + 200)).abs().argsort()[:1]]
                    if list(df_upcoming['Brake'])[0] > 1 and ir['Lap'] > 0:
                        has_braked = False
                        braking_zone_saved = True
                        braking_zone_dist = ir['LapDist']
                        pyautogui.typewrite('1')
                        pyautogui.typewrite('1')
                        pyautogui.typewrite('1')
                        pyautogui.typewrite('1')
                        self.braking_zone_success = True
                elif not has_braked:
                    has_braked = ir['Brake']*100 > 5
                elif has_braked and braking_zone_saved and ir['LapDist'] - braking_zone_dist > 150 and not self.braking_zone_success\
                        and not ir['LapDist'] - braking_zone_dist > 1000 and not ir['LapDist'] < braking_zone_dist:
                    df = self.reference_df[(self.reference_df['LapDist'] >= ir['LapDist'] - 150) &
                                           (self.reference_df['LapDist'] <= ir['LapDist'] + 150)]
                    A = list(df['Lat'])[0]
                    B = list(df['Lon'])[0]
                    C = list(df['Lat'])[::-1][0]
                    D = list(df['Lon'])[::-1][0]

                    index = list(df['Lat']).index(min(df['Lat']))
                    E = list(df['Lat'])[index]
                    F = list(df['Lon'])[index]
                    if ((B - D) / (A - C)) * (E - A) + B + 0.0002 > F > ((B - D) / (A - C)) * (E - A) + B - 0.0002:
                        index = list(df['Lat']).index(max(df['Lat']))
                        E = list(df['Lat'])[index]
                        F = list(df['Lon'])[index]
                        if ((B - D) / (A - C)) * (E - A) + B + 0.0002 > F > ((B - D) / (A - C)) * (E - A) + B - 0.0002:
                            index = list(df['Lon']).index(min(df['Lon']))
                            E = list(df['Lat'])[index]
                            F = list(df['Lon'])[index]
                            if ((B - D) / (A - C)) * (E - A) + B + 0.0002 > F > ((B - D) / (A - C)) * (
                                    E - A) + B - 0.0002:
                                index = list(df['Lon']).index(max(df['Lon']))
                                E = list(df['Lat'])[index]
                                F = list(df['Lon'])[index]
                                if ((B - D) / (A - C)) * (E - A) + B + 0.0002 > F > ((B - D) / (A - C)) * (
                                        E - A) + B - 0.0002:
                                    if ir['Brake'] * 100 < 1:
                                        pyautogui.typewrite('2')
                                        pyautogui.typewrite('2')
                                        pyautogui.typewrite('2')
                                        pyautogui.typewrite('2')
                                        has_braked = False
                elif ir['LapDist'] - braking_zone_dist > 1000 or ir['LapDist'] < braking_zone_dist:
                    braking_zone_saved = False
                self.update_plot()

    def update_now(self, value):
        self.vehicle = self.vehicles_list.index(value)
        self.selectedVehicle = value
        self.tracks_list = []
        raw_tracks = os.listdir(self.path + self.selectedVehicle)
        for track in raw_tracks:
            self.tracks_list.append(track.replace('.csv', ''))
        self.trackBox.clear()
        self.trackBox.addItems(self.tracks_list)
        self.trackBox.setCurrentIndex(0)

    def update_tolerance(self, value):
        self.tolerance = int(value)

    def update_plot(self):
        try:
            data = [0]

            while True:
                try:
                    data = self.q.get_nowait()
                except queue.Empty:
                    break
                df_closest = self.reference_df.iloc[(self.reference_df['LapDist'] - ir['LapDist']).abs().argsort()[:1]]
                data = [ir['Brake']*100]
                data2 = [list(df_closest['Brake'])[0]]
                shift = len(data)
                self.plotdata = np.roll(self.plotdata, -shift, axis=0)
                self.plotdata[-shift:, :] = data
                self.ydata = self.plotdata[:]
                self.canvas.axes.set_facecolor((0, 0, 0))

                shift2 = len(data2)
                self.plotdata2 = np.roll(self.plotdata2, -shift2, axis=0)
                self.plotdata2[-shift2:, :] = data2
                self.ydata2 = self.plotdata2[:]
                self.canvas2.axes.set_facecolor((0, 0, 0))

                if abs(data[0] - data2[0]) >= self.tolerance and ir['Lap'] > 0:
                    self.braking_zone_success = False
                    self.canvas.axes.set_facecolor((1, 0, 0))
                    self.canvas2.axes.set_facecolor((1, 0, 0))

                if self.reference_plot is None:
                    plot_refs = self.canvas.axes.plot(self.ydata, color=(0, 1, 0.29))
                    self.reference_plot = plot_refs[0]
                else:
                    self.reference_plot.set_ydata(self.ydata)

                if self.reference_plot2 is None:
                    plot_refs2 = self.canvas2.axes.plot(self.ydata2, color=(0, 1, 0.29))
                    self.reference_plot2 = plot_refs2[0]
                else:
                    self.reference_plot2.set_ydata(self.ydata2)

            self.canvas.axes.yaxis.grid(True, linestyle='--')
            start, end = self.canvas.axes.get_ylim()
            self.canvas.axes.yaxis.set_ticks(np.arange(start, end, 10))
            self.canvas.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))
            self.canvas.axes.set_ylim(ymin=-10, ymax=110)
            self.canvas.draw()

            self.canvas2.axes.yaxis.grid(True, linestyle='--')
            start2, end2 = self.canvas2.axes.get_ylim()
            self.canvas2.axes.yaxis.set_ticks(np.arange(start, end, 10))
            self.canvas2.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))
            self.canvas2.axes.set_ylim(ymin=-10, ymax=110)
            self.canvas2.draw()
        except:
            pass


class Worker(QtCore.QRunnable):

    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)


ir = irsdk.IRSDK()
ir.startup()
state = State()
app = QtWidgets.QApplication(sys.argv)
mainWindow = LHP_LIVE_BRAKE_APP()
mainWindow.show()
sys.exit(app.exec_())