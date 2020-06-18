# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(QtWidgets.QDialog):
    def __init__(self, kind:str, db):
        super().__init__()
        # Esto se debe cambiar al retrieve de la database
        coins = ['mxn', 'btc', 'eth', 'xrp']
        self.DB = db
        # coins = self.DB.retrieveCoins()
        Dialog.setObjectName('Dialog')
        Dialog.resize(390, 222)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 170, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.coin_initial = QtWidgets.QComboBox(Dialog)
        self.coin_initial.setGeometry(QtCore.QRect(280, 60, 81, 24))
        self.coin_initial.setObjectName("coin_initial")
        self.coin_final = QtWidgets.QComboBox(Dialog)
        self.coin_final.setGeometry(QtCore.QRect(280, 110, 81, 24))
        self.coin_final.setObjectName("coin_final")
        [combo.addItems(coins) for combo in [self.coin_initial, self.coin_final]]

        self.amount_initial = QtWidgets.QLineEdit(Dialog)
        self.amount_initial.setGeometry(QtCore.QRect(110, 60, 151, 28))
        self.amount_initial.setObjectName("amount_initial")
        self.amount_final = QtWidgets.QLineEdit(Dialog)
        self.amount_final.setGeometry(QtCore.QRect(110, 110, 151, 28))
        self.amount_final.setObjectName("amount_final")
        self.lbl_init = QtWidgets.QLabel(Dialog)
        self.lbl_init.setGeometry(QtCore.QRect(30, 70, 59, 16))
        self.lbl_init.setObjectName("lbl_init")
        self.lbl_final = QtWidgets.QLabel(Dialog)
        self.lbl_final.setGeometry(QtCore.QRect(30, 120, 59, 16))
        self.lbl_final.setObjectName("lbl_final")
        self.title = QtWidgets.QLabel(Dialog)
        self.title.setGeometry(QtCore.QRect(130, 20, 121, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.title.setFont(font)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setObjectName("title")
        if 'trade' in kind:
            windowName = 'Nuevo Trade'
            txt_label_init = 'Inicial'
            txt_label_final = 'Finial'
            self.status = 1
        else:
            windowName = 'Agregar Fondos'
            txt_label_init = 'Cantidad'
            txt_label_final = ''
            self.status = 0
            self.coin_final.setVisible(False)
            self.amount_final.setVisible(False)
            self.lbl_init.setGeometry(QtCore.QRect(30, 100, 59, 16))
            self.coin_initial.setGeometry(QtCore.QRect(280, 90, 81, 24))
            self.amount_initial.setGeometry(QtCore.QRect(110,90, 151, 28))
                

        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", windowName))
        self.lbl_init.setText(_translate("Dialog", txt_label_init))
        self.lbl_final.setText(_translate("Dialog", txt_label_final))
        self.title.setText(_translate("Dialog", windowName))
        # Modificar esta funcion
        self.buttonBox.accepted.connect(self.AddTrade)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)


    def AddTrade(self):
        # Retrieve the amount
        try:
            if self.status == 1:
                # Trade
                trade = {
                    'init': [float(self.amount_initial.text()) , str(self.coin_initial.currentText())],
                    'final': [float(self.amount_final.text()) , str(self.coin_final.currentText())],
                }
                self.DB.addTrade(trade)
            else:
                # add Funds to DB
                self.DB.addFund(float(self.amount_initial.text()))
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText('Operación completada')
            msg.setWindowTitle('Completado')
            msg.exec_()
            Dialog.accept()

        except ValueError:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('No colocaste toda la información')
            msg.setWindowTitle("Error")
            msg.exec_()
        


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog('fund', None)
    p = Dialog.palette()
    p.setColor(Dialog.backgroundRole(), QtGui.QColor("#adb5bd"))
    Dialog.setPalette(p)
    Dialog.show()
    sys.exit(app.exec_())
