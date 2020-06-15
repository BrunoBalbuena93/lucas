from PyQt4 import QtGui,QtCore
import sys
import numpy as np
import pyqtgraph as pg
import cv2
    
class Graphs(QtGui.QWidget):
    def __init__(self,parent=None):
        super(Graphs,self).__init__(parent)
        ## Poner graficas
        from scipy.signal import butter
        self.plot_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_burg = pg.PlotWidget(title="Burg PSD")
        self.plot_burg.setYRange(-40,20)
        self.plot_burg.setXRange(0,50)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.plot_raw)
        self.layout.addWidget(self.plot_burg)
        self.setGeometry(20,10,550,600)
        nyq = 0.5*160 ##Fs
        fcut = [2/nyq,40/nyq]
        fnot = [50/nyq,70/nyq]
        self.b,self.a = butter(4,fcut,btype='band')
        self.bcut,self.acut = butter(4,fnot,btype='bandstop')
        self.t = np.array([float(i)/160 for i in range(320)])
        self.findCOM()
        
    def RefreshGraph(self):
        self.plot_raw.clear()
        self.plot_raw.showGrid(x=1,y=1,alpha=1)
        self.plot_burg.clear()
        self.plot_burg.showGrid(x=1,y=1,alpha=1)
        self.ReadCOM()
        try:
            X_burg,F = self.GetBurg(self.signal)
            self.plot_raw.plot(self.t,self.signal,pen='c',width=2)
            self.plot_burg.plot(F,X_burg,pen='w',width=2)
        except ZeroDivisionError:
            pass
    def findCOM(self):
        import serial
        import time
        k = 0
        while k < 9:
            k = k+1
            try:
                self.COM = 'COM'+str(k)
                self.ser = serial.Serial(self.COM,115200,timeout=1)
                print self.COM +' port available'
                break
            except serial.serialutil.SerialException:
                self.COM = 0
        if self.COM == 0:
            sys.exit()
        print 'Opening port '+self.COM
        self.ser.close()
        self.ser.open()
##        time.sleep(1.5)

    def ReadCOM(self):
        from scipy.signal import lfilter
        Values = self.ser.readlines()
        X = [float(val.replace('\r\n',''))for val in Values]
##        X = X[-160:-1]
        self.ser.write('10')    #aqui
##        if  len(X)>160:
##            X = X[-160:-1]
##            X.append(0)
        fs = 160
##        X = [x-3 for x in X]
        self.signal = lfilter(self.b,self.a,X)
##        self.signal = lfilter(self.bcut,self.acut,self.signal)
##        self.signal = X
        [register.append(value) for value in self.signal]
    def GetBurg(self,X):
        import spectrum
        AR,rho,ref = spectrum.arburg(X, order=20)
        psd = spectrum.arma2psd(AR, rho=rho, NFFT=4096)
        psd = psd[len(psd):len(psd)/2:-1]
        p = 10*np.log(abs(psd)*2./(2.*np.pi))
        F = spectrum.linspace(0,80,len(p))
        return p,F
    def CloseCOM(self):
        self.ser.close()
        print 'Closing '+self.COM
class ADD(QtGui.QDialog):
    def __init__(self,parent=None):
        super(ADD,self).__init__(parent)
        self.setGeometry(50,50,230,150)
        self.setWindowTitle("Add User")
        lbl_name = QtGui.QLabel('Name: ',self)
        self.name = QtGui.QLineEdit()
        fbox = QtGui.QFormLayout()
        fbox.addRow(lbl_name,self.name)
        btn_save = QtGui.QPushButton("Save",self)
        btn_save.clicked.connect(self.save)
        btn_save.resize(95,25)
        btn_cancel = QtGui.QPushButton("Cancel",self)
        btn_cancel.resize(95,25)
        btn_cancel.clicked.connect(self.close)
        btn_save.move(10,100)
        btn_cancel.move(115,100)
        self.setLayout(fbox)
        self.show()
    def save(self):
        import datetime
        path = 'C:/Users/Bruno/Desktop/Escuela/Escuela/TT/Base de datos EEG/Base/GUI/'
        now = datetime.datetime.now()
        self.date = now.strftime("%d%m%Y")
        new = self.date+'_'+self.name.text()
        t_file = open(path+new+'.txt','w')
        [t_file.write(str(val)+'\n') for val in register]
        t_file.close()
        print new
        self.close()
        
class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window,self).__init__()
        self.setGeometry(40,40,600,650)
        self.setWindowTitle("Testing Module")
        self.setWindowIcon(QtGui.QIcon('C:\Users\Bruno\Desktop\Escuela\Escuela\TT\GUI\UPIITA.png'))
        self.Graphs = Graphs(self)
        self.setButtons()
        global register
        register = []
        self.T = [0,0]
        self.Delay = []
        self.home()
    def home(self):
        self.T[0] =(cv2.getTickCount())
        self.Graphs.RefreshGraph()
        self.T[1] = cv2.getTickCount()
        self.Delay =((self.T[-1]-self.T[-2])/cv2.getTickFrequency())
        print '{:.3f}'.format(self.Delay)+ 's  Muestras perdidas = '+'{:.2f}'.format(self.Delay*160)
        self.show()
    def setButtons(self):
        btn_save = QtGui.QPushButton("&Save",self)
        btn_exit = QtGui.QPushButton("&Exit",self)
        btn_save.resize(btn_save.minimumSizeHint())
        btn_exit.resize(btn_exit.minimumSizeHint())
        btn_save.move(400,620)
        btn_exit.move(500,620)
        btn_save.clicked.connect(self.save_data)
        btn_exit.clicked.connect(self.close_application)
    def save_data(self):
        AddNew = ADD()
        AddNew.exec_()
        print 'save data'
    def close_application(self):
        choice = QtGui.QMessageBox.question(self,'Exit',"Would you like to save?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            self.save_data()
        print 'close application'
        self.Graphs.CloseCOM()
        self.close()
def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    timer = QtCore.QTimer()
    timer.timeout.connect(GUI.home)
    timer.start(2500)
    GUI.show()
    sys.exit(app.exec_())
run()
        
