# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'atomsidentify.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(324, 539)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.TheTable = QtWidgets.QTableWidget(Dialog)
        self.TheTable.setObjectName("TheTable")
        self.TheTable.setColumnCount(0)
        self.TheTable.setRowCount(0)
        self.verticalLayout.addWidget(self.TheTable)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setAcceptDrops(False)
        self.okButton.setObjectName("okButton")
        self.verticalLayout.addWidget(self.okButton)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Spesify atoms types"))
        self.okButton.setText(_translate("Dialog", "PushButton"))

