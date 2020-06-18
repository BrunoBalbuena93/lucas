
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from gui.visualizer import Freeze


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import random

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, shortTerm:bool=True):
        self.isShortTerm = shortTerm
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor=Freeze.getFigureColor())
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        plt.rcParams.update({'font.size': 6})
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


    def plot(self, coin:str, data):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.set_frame_on(False)
        f = Freeze(ax, coin, isGui=True)
        f.plot2Gui(df=data)
        self.draw()
