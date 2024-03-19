# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd_gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1166, 999)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_widget.setGeometry(QtCore.QRect(10, 10, 1141, 941))
        self.tab_widget.setObjectName("tab_widget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.summary_table = QtWidgets.QTableView(self.tab)
        self.summary_table.setGeometry(QtCore.QRect(3, 8, 1121, 401))
        font = QtGui.QFont()
        font.setFamily("Ubuntu")
        font.setPointSize(11)
        self.summary_table.setFont(font)
        self.summary_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.summary_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.summary_table.setSortingEnabled(True)
        self.summary_table.setObjectName("summary_table")
        self.summary_table.verticalHeader().setVisible(False)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_2.setGeometry(QtCore.QRect(0, 470, 391, 431))
        self.groupBox_2.setObjectName("groupBox_2")
        self.transaction_summary_table = QtWidgets.QTableView(self.groupBox_2)
        self.transaction_summary_table.setGeometry(QtCore.QRect(5, 25, 381, 401))
        self.transaction_summary_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.transaction_summary_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.transaction_summary_table.setObjectName("transaction_summary_table")
        self.transaction_summary_table.verticalHeader().setVisible(False)
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(390, 470, 741, 431))
        self.groupBox_3.setObjectName("groupBox_3")
        self.dividend_summary_table = QtWidgets.QTableView(self.groupBox_3)
        self.dividend_summary_table.setGeometry(QtCore.QRect(4, 26, 731, 401))
        self.dividend_summary_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.dividend_summary_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.dividend_summary_table.setObjectName("dividend_summary_table")
        self.dividend_summary_table.verticalHeader().setVisible(False)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_4.setGeometry(QtCore.QRect(0, 410, 1121, 61))
        self.groupBox_4.setObjectName("groupBox_4")
        self.main_filter = QtWidgets.QLineEdit(self.groupBox_4)
        self.main_filter.setGeometry(QtCore.QRect(940, 30, 171, 25))
        self.main_filter.setObjectName("main_filter")
        self.show_closed_positions = QtWidgets.QCheckBox(self.groupBox_4)
        self.show_closed_positions.setGeometry(QtCore.QRect(720, 30, 201, 23))
        self.show_closed_positions.setObjectName("show_closed_positions")
        self.search_all_columns = QtWidgets.QCheckBox(self.groupBox_4)
        self.search_all_columns.setGeometry(QtCore.QRect(510, 30, 181, 23))
        self.search_all_columns.setObjectName("search_all_columns")
        self.tab_widget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.calendar_details_table = QtWidgets.QTableView(self.tab_2)
        self.calendar_details_table.setGeometry(QtCore.QRect(650, 30, 481, 871))
        self.calendar_details_table.setObjectName("calendar_details_table")
        self.calendar_details_table.verticalHeader().setVisible(False)
        self.groupBox = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 631, 411))
        self.groupBox.setObjectName("groupBox")
        self.before_tax_radio = QtWidgets.QRadioButton(self.groupBox)
        self.before_tax_radio.setGeometry(QtCore.QRect(10, 30, 111, 23))
        self.before_tax_radio.setObjectName("before_tax_radio")
        self.after_tax_radio = QtWidgets.QRadioButton(self.groupBox)
        self.after_tax_radio.setGeometry(QtCore.QRect(120, 30, 111, 23))
        self.after_tax_radio.setChecked(True)
        self.after_tax_radio.setObjectName("after_tax_radio")
        self.dividend_calendar = QtWidgets.QTableView(self.groupBox)
        self.dividend_calendar.setGeometry(QtCore.QRect(10, 60, 621, 341))
        self.dividend_calendar.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.dividend_calendar.setObjectName("dividend_calendar")
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_5.setGeometry(QtCore.QRect(10, 480, 631, 371))
        self.groupBox_5.setObjectName("groupBox_5")
        self.investment_calendar = QtWidgets.QTableView(self.groupBox_5)
        self.investment_calendar.setGeometry(QtCore.QRect(0, 30, 621, 331))
        self.investment_calendar.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.investment_calendar.setObjectName("investment_calendar")
        self.ym_label = QtWidgets.QLabel(self.tab_2)
        self.ym_label.setGeometry(QtCore.QRect(660, 10, 121, 17))
        self.ym_label.setObjectName("ym_label")
        self.tab_widget.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1166, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tab_widget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Transactions"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Dividends"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Filtering"))
        self.main_filter.setPlaceholderText(_translate("MainWindow", "Filter rows..."))
        self.show_closed_positions.setText(_translate("MainWindow", "F3: Show closed positions"))
        self.search_all_columns.setText(_translate("MainWindow", "F2: Search all columns"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab), _translate("MainWindow", "Summary"))
        self.groupBox.setTitle(_translate("MainWindow", "Dividend calendar"))
        self.before_tax_radio.setText(_translate("MainWindow", "Before tax"))
        self.after_tax_radio.setText(_translate("MainWindow", "After tax"))
        self.groupBox_5.setTitle(_translate("MainWindow", "Investment calendar"))
        self.ym_label.setText(_translate("MainWindow", "TextLabel"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_2), _translate("MainWindow", "Calendar"))