# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'model.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!

from json import load
from sys import exit, argv
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
from json import load

from gui.dialog import OpenDialog
from gui.graphs import PlotCanvas
from gui.visualizer import Freeze

with open('settings.json', 'r') as f:
    settings = load(f)

app = QtWidgets.QApplication(argv)
MainWindow = QtWidgets.QMainWindow()
    

class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db, thunder):
        super().__init__()
        # Lucas Variables
        self.db = db
        self.thunder = thunder
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(795, 556)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Triangular)
        with open('settings.json', 'r') as f:
            data = load(f)
            self.symbols = data['coin-symbol']
            params = data['gui']
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        # Configurando color
        self.centralwidget.setStyleSheet("background-color: \"{}\";".format(params['colors']['background']))
        # Tabs
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(6, 9, 771, 501))
        self.tabWidget.setObjectName("tabWidget")
        self.status = QtWidgets.QWidget()
        self.status.setObjectName("status")
        # Status Tab
        self.addTrade = QtWidgets.QPushButton(self.status)
        self.addTrade.setGeometry(QtCore.QRect(30, 420, 101, 28))
        self.addTrade.setObjectName("addTrade")
        self.tableWidget = QtWidgets.QTableWidget(self.status)
        self.tableWidget.setGeometry(QtCore.QRect(30, 270, 331, 131))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.comboBox = QtWidgets.QComboBox(self.status)
        self.comboBox.setGeometry(QtCore.QRect(20, 10, 211, 31))
        self.comboBox.setMaxVisibleItems(4)
        self.comboBox.setFrame(True)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.activated.connect(self.drawStatus)
        self.Graph1 = PlotCanvas(self.status)
        self.Graph1.setGeometry(QtCore.QRect(420, 30, 321, 171))
        self.Graph1.setObjectName("Graph1")
        self.Graph2 = PlotCanvas(self.status, False)
        self.Graph2.setGeometry(QtCore.QRect(420, 240, 321, 151))
        self.Graph2.setObjectName("Graph2")
        self.addFunds = QtWidgets.QPushButton(self.status)
        self.addFunds.setGeometry(QtCore.QRect(150, 420, 101, 28))
        self.addFunds.setObjectName("addFunds")
        self.line = QtWidgets.QFrame(self.status)
        self.line.setGeometry(QtCore.QRect(30, 240, 341, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        # Etiquetas
        self.lbl_totalAmount = QtWidgets.QLabel(self.status)
        self.lbl_totalAmount.setGeometry(QtCore.QRect(40, 60, 91, 21))
        self.lbl_totalAmount.setObjectName("lbl_totalAmount")
        self.lbl_valueNow = QtWidgets.QLabel(self.status)
        self.lbl_valueNow.setGeometry(QtCore.QRect(40, 90, 91, 21))
        self.lbl_valueNow.setObjectName("lbl_valueNow")
        self.lbl_valuation = QtWidgets.QLabel(self.status)
        self.lbl_valuation.setGeometry(QtCore.QRect(40, 120, 111, 21))
        self.lbl_valuation.setObjectName("lbl_valuation")
        self.Update = QtWidgets.QPushButton(self.status)
        self.Update.setGeometry(QtCore.QRect(520, 420, 101, 28))
        self.Update.setObjectName("Update")
        self.totalAmount = QtWidgets.QLabel(self.status)
        self.totalAmount.setGeometry(QtCore.QRect(160, 60, 200, 16))
        self.totalAmount.setObjectName("totalAmount")
        self.currentValue = QtWidgets.QLabel(self.status)
        self.currentValue.setGeometry(QtCore.QRect(160, 90, 200, 16))
        self.currentValue.setObjectName("currentValue")
        self.valuation = QtWidgets.QLabel(self.status)
        self.valuation.setGeometry(QtCore.QRect(160, 120, 90, 16))
        self.valuation.setObjectName("valuation")
        self.lbl_change = QtWidgets.QLabel(self.status)
        self.lbl_change.setGeometry(QtCore.QRect(40, 160, 111, 21))
        self.lbl_change.setObjectName("lbl_change")
        self.lbl_change_2 = QtWidgets.QLabel(self.status)
        self.lbl_change_2.setGeometry(QtCore.QRect(40, 190, 111, 21))
        self.lbl_change_2.setObjectName("lbl_change_2")
        self.changeAll = QtWidgets.QLabel(self.status)
        self.changeAll.setGeometry(QtCore.QRect(160, 160, 200, 16))
        self.changeAll.setObjectName("changeAll")
        self.changeLast = QtWidgets.QLabel(self.status)
        self.changeLast.setGeometry(QtCore.QRect(160, 190, 70, 16))
        self.changeLast.setObjectName("changeLast")
        self.ChangeDates = QtWidgets.QPushButton(self.status)
        self.ChangeDates.setGeometry(QtCore.QRect(400, 420, 101, 28))
        self.ChangeDates.setObjectName("ChangeDates")
        self.addExit = QtWidgets.QPushButton(self.status)
        self.addExit.setGeometry(QtCore.QRect(640, 420, 101, 28))
        self.addExit.setObjectName("addExit")
        self.tabWidget.addTab(self.status, "")
        self.predict = QtWidgets.QWidget()
        self.predict.setAutoFillBackground(False)
        self.predict.setObjectName("predict")
        self.comboBox_3 = QtWidgets.QComboBox(self.predict)
        self.comboBox_3.setGeometry(QtCore.QRect(20, 10, 211, 31))
        self.comboBox_3.setMaxVisibleItems(4)
        self.comboBox_3.setFrame(True)
        self.comboBox_3.setObjectName("comboBox_3")
        self.widget = QtWidgets.QWidget(self.predict)
        self.widget.setGeometry(QtCore.QRect(450, 20, 301, 151))
        self.widget.setObjectName("widget")
        self.widget_2 = QtWidgets.QWidget(self.predict)
        self.widget_2.setGeometry(QtCore.QRect(450, 200, 301, 151))
        self.widget_2.setObjectName("widget_2")
        self.lbl_model1 = QtWidgets.QLabel(self.predict)
        self.lbl_model1.setGeometry(QtCore.QRect(40, 70, 71, 21))
        self.lbl_model1.setObjectName("lbl_model1")
        self.lbl_model2 = QtWidgets.QLabel(self.predict)
        self.lbl_model2.setGeometry(QtCore.QRect(40, 120, 71, 21))
        self.lbl_model2.setObjectName("lbl_model2")
        self.lbl_model3 = QtWidgets.QLabel(self.predict)
        self.lbl_model3.setGeometry(QtCore.QRect(40, 170, 71, 21))
        self.lbl_model3.setObjectName("lbl_model3")
        self.lbl_model4 = QtWidgets.QLabel(self.predict)
        self.lbl_model4.setGeometry(QtCore.QRect(40, 220, 71, 21))
        self.lbl_model4.setObjectName("lbl_model4")
        self.model1 = QtWidgets.QLabel(self.predict)
        self.model1.setGeometry(QtCore.QRect(120, 70, 71, 21))
        self.model1.setObjectName("model1")
        self.model2 = QtWidgets.QLabel(self.predict)
        self.model2.setGeometry(QtCore.QRect(120, 120, 71, 21))
        self.model2.setObjectName("model2")
        self.model3 = QtWidgets.QLabel(self.predict)
        self.model3.setGeometry(QtCore.QRect(120, 170, 71, 21))
        self.model3.setObjectName("model3")
        self.model4 = QtWidgets.QLabel(self.predict)
        self.model4.setGeometry(QtCore.QRect(120, 220, 71, 21))
        self.model4.setObjectName("model4")
        self.lbl_other = QtWidgets.QLabel(self.predict)
        self.lbl_other.setGeometry(QtCore.QRect(230, 70, 71, 21))
        self.lbl_other.setObjectName("lbl_other")
        self.other = QtWidgets.QLabel(self.predict)
        self.other.setGeometry(QtCore.QRect(340, 70, 71, 21))
        self.other.setObjectName("other")
        self.tabWidget.addTab(self.predict, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 795, 22))
        self.menubar.setDefaultUp(False)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHerramientas = QtWidgets.QMenu(self.menubar)
        self.menuHerramientas.setObjectName("menuHerramientas")
        self.menuAcciones = QtWidgets.QMenu(self.menubar)
        self.menuAcciones.setObjectName("menuAcciones")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        # self.actionExportar = QtWidgets.QAction(MainWindow)
        # self.actionExportar.setObjectName("actionExportar")
        self.actionSalir = QtWidgets.QAction(MainWindow)
        self.actionSalir.setObjectName('actionSalir')
        self.actionSalir.triggered.connect(self.CloseGUI)
        self.actionShell = QtWidgets.QAction(MainWindow)
        self.actionShell.setObjectName("actionShell")
        self.addNewTrade = QtWidgets.QAction(MainWindow)
        self.addNewTrade.setObjectName("addNewTrade")
        self.addNewTrade.triggered.connect(partial(self.addNewTradeOperation, 'trade'))
        self.addNewFunds = QtWidgets.QAction(MainWindow)
        self.addNewFunds.setObjectName("addNewFunds")
        self.addNewFunds.triggered.connect(partial(self.addNewTradeOperation, 'fund'))
        self.addNewCoin = QtWidgets.QAction(MainWindow)
        self.addNewCoin.setObjectName("addNewCoin")
        self.addNewCoin.triggered.connect(self.addNewCoinOperation)
        self.addNewAlert = QtWidgets.QAction('addNewAlert')
        self.addNewAlert.setObjectName('addNewAlert')
        self.addNewAlert.triggered.connect(self.addNewAlertOperation)
        self.menuFile.addAction(self.actionSalir)
        self.menuHerramientas.addAction(self.actionShell)
        self.menuAcciones.addAction(self.addNewTrade)
        self.menuAcciones.addAction(self.addNewFunds)
        self.menuAcciones.addAction(self.addNewCoin)
        self.menuAcciones.addAction(self.addNewAlert)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHerramientas.menuAction())
        self.menubar.addAction(self.menuAcciones.menuAction())
        # Llenando las tags y esas cosas
        self.retranslateUi(MainWindow)

        # Definiendo funciones de botones
        self.addExit.clicked.connect(self.CloseGUI)
        self.addTrade.clicked.connect(partial(self.addNewTradeOperation, 'trade'))
        self.addFunds.clicked.connect(partial(self.addNewTradeOperation, 'fund'))
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Lucas, tu auxiliar con criptomonedas"))
        self.addTrade.setText(_translate("MainWindow", "Nuevo Trade"))
        self.addFunds.setText(_translate("MainWindow", "Agregar Fondos"))
        self.lbl_totalAmount.setText(_translate("MainWindow", "Monto total:"))
        self.lbl_valueNow.setText(_translate("MainWindow", "Valor Actual:"))
        self.lbl_valuation.setText(_translate("MainWindow", "Token"))
        self.Update.setText(_translate("MainWindow", "Actualizar"))
        self.comboBox.addItem('Selecciona una moneda')
        self.comboBox_3.addItem('Selecciona una moneda')
        # Seleccionando monedas
        coins = self.db.retrieveCoins()
        self.comboBox.addItems(coins)
        self.comboBox_3.addItems(coins)
        self.totalAmount.setText(_translate("MainWindow", ""))
        self.currentValue.setText(_translate("MainWindow", ""))
        self.valuation.setText(_translate("MainWindow", ""))
        self.lbl_change.setText(_translate("MainWindow", "Max / Min"))
        self.lbl_change_2.setText(_translate("MainWindow", "Recomendación"))
        self.changeAll.setText(_translate("MainWindow", ""))
        self.changeLast.setText(_translate("MainWindow", ""))
        self.ChangeDates.setText(_translate("MainWindow", "&Cambiar fechas"))
        self.addExit.setText(_translate("MainWindow", "&Salir"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.status), _translate("MainWindow", "status"))
        self.lbl_model1.setText(_translate("MainWindow", "Modelo 1"))
        self.lbl_model2.setText(_translate("MainWindow", "Modelo 2"))
        self.lbl_model3.setText(_translate("MainWindow", "Modelo 3"))
        self.lbl_model4.setText(_translate("MainWindow", "Modelo 4"))
        self.model1.setText(_translate("MainWindow", ""))
        self.model2.setText(_translate("MainWindow", ""))
        self.model3.setText(_translate("MainWindow", ""))
        self.model4.setText(_translate("MainWindow", ""))
        self.lbl_other.setText(_translate("MainWindow", "other"))
        self.other.setText(_translate("MainWindow", "other"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.predict), _translate("MainWindow", "params"))
        self.menuFile.setTitle(_translate("MainWindow", "Archivo"))
        self.menuHerramientas.setTitle(_translate("MainWindow", "Herramientas"))
        self.menuAcciones.setTitle(_translate("MainWindow", "Acciones"))
        # self.actionExportar.setText(_translate("MainWindow", "Exportar"))
        self.actionSalir.setText(_translate("MainWindow", "Salir"))
        self.actionShell.setStatusTip(_translate("MainWindow", "Salir de la aplicación"))
        self.actionSalir.setShortcut(_translate("MainWindow", "Esc"))
        self.actionShell.setText(_translate("MainWindow", "Shell"))
        self.actionShell.setStatusTip(_translate("MainWindow", "Iniciar una shell en lucas"))
        self.actionShell.setShortcut(_translate("MainWindow", "Ctrl+Alt+S"))
        self.addNewTrade.setText(_translate("MainWindow", "Nuevo Trade"))
        self.addNewTrade.setStatusTip(_translate("MainWindow", "Agregar una operación"))
        self.addNewTrade.setShortcut(_translate("MainWindow", "Ctrl+T"))
        self.addNewFunds.setText(_translate("MainWindow", "Agregar Fondos"))
        self.addNewFunds.setStatusTip(_translate("MainWindow", "Agregar fondos"))
        self.addNewFunds.setShortcut(_translate("MainWindow", "Ctrl+F"))
        self.addNewCoin.setText(_translate("MainWindow", "Agregar Moneda"))
        self.addNewFunds.setStatusTip(_translate("MainWindow", "Agregar moneda"))
        self.addNewAlert.setText(_translate("MainWindow", "Nueva Alerta"))
        self.addNewAlert.setStatusTip(_translate('MainWindow', 'Inicia una alerta'))
        self.addNewAlert.setShortcut(_translate('MainWindow', 'Ctrl+A'))
        
    def addNewTradeOperation(self, operation:str):
        OpenDialog(operation, self.db)
        
    def drawStatus(self):
        # Retrieving the coin
        coin = self.comboBox.currentText()
        # Ploting the graphs
        historical = self.thunder.getHistorical(coin)
        self.Graph1.plot(coin, data=self.thunder.get5h(settings['coin-symbol'][coin]))
        self.Graph2.plot(coin, data=historical)
        # Retrieval of variables
        _, coinAmount, totalAmount, dbValuationUSD, dbValuationMXN = self.db.retrieveBalance(coin, many=True)
        dbLastValuationUSD = self.db.retrieveLastValuation(coin)
        requestValuation = self.thunder.getCoinValuation(self.symbols[coin])
        USDMXN = self.thunder.getUSDValuation()
        # Now loading the data into the labels
        _translate = QtCore.QCoreApplication.translate
        self.totalAmount.setText(_translate("MainWindow", '{:.2f} mxn @ {:.3f} usd/{}'.format(totalAmount, dbValuationUSD, coin)))
        self.currentValue.setText(_translate("MainWindow", '{:.2f} mxn | {:.4f}%'.format(USDMXN * requestValuation * coinAmount, (requestValuation - dbValuationUSD) * 100 / dbValuationUSD)))
        self.valuation.setText(_translate("MainWindow", '{:.6f} {}'.format(coinAmount, coin)))
        self.changeAll.setText(_translate("MainWindow", '{:.4f} / {:.4f}'.format(historical['close'].max(), historical['close'].min())))
        self.changeLast.setText(_translate("MainWindow", '{}'.format('Pendiente')))
        # Populating table
        data = self.db.tradesGUI(coin)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(len(data))
        # Headers
        self.tableWidget.setHorizontalHeaderLabels(['Inicial', 'Final', 'Valuación'])
        self.tableWidget.setVerticalHeaderLabels([value[2:10] for value in data.index])
        for i in range(len(data)):
            [self.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(data[j].iloc[i]))) for j, col in enumerate(data.iloc[i])]
        self.tableWidget.resizeColumnsToContents()


    def addNewCoinOperation(self):
        raise NotImplementedError('Agregar moneda')

    def addNewAlertOperation(self):
        raise NotImplementedError('Configurar la alerta')

    def CloseGUI(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText('¿Ya quieres salir?')
        msg.setWindowTitle('Salir')
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        choice = msg.exec_()
        if choice == QtWidgets.QMessageBox.Yes:
            MainWindow.close()



def startGUI(db, thunder):
    ui = Ui_MainWindow(db, thunder)
    p = MainWindow.palette()
    p.setColor(MainWindow.backgroundRole(), QtGui.QColor(173, 181, 189))
    MainWindow.setPalette(p)
    MainWindow.show()
    exit(app.exec_())


        
if __name__ == "__main__":
    startGUI(None, None)