#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

"""
File name: main.py
Author: Arnaud Bourget
Date created: 09/10/2018
Date last modified: 23/10/2018
Python Version: 3.6
"""

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QComboBox, QDoubleSpinBox, QGridLayout, QCalendarWidget
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

from decimal import Decimal
from datetime import timedelta

from urllib.request import urlretrieve
import zipfile

import pyqtgraph as pg


class CurrencyConverter(QDialog):
    """
    Currency Converter using PyQt5
    The exchange rates are updated every days with Euro as reference
    """

    def __init__(self):
        """
        CurrencyConverter class initialization

        Set all the class variables like the labels and comboboxes that will be used in the initUI method
        """

        super().__init__()

        self.rates = dict()
        self.currencies = list()
        self.getData()  # Fetch the data from the csv online file

        # Initialization of the currencies choice dropdown boxes
        self.from_currency = QComboBox()
        self.from_currency.addItems(self.currencies)
        self.to_currency = QComboBox()
        self.to_currency.addItems(self.currencies)

        self.from_amount = QDoubleSpinBox()
        self.from_amount.setRange(0.01, 10000000.00)
        self.from_amount.setValue(1.00)
        self.to_amount = QLabel('1.00')
        self.from_currency_label = QLabel('From Currency:')
        self.to_currency_label = QLabel('To Currency:')
        self.from_amount_label = QLabel('Amount to convert:')
        self.to_amount_label = QLabel('Result of conversion based on most recent rates:')

        self.from_calendar = QCalendarWidget()
        self.to_calendar = QCalendarWidget()
        self.rates_plot = pg.PlotWidget()
        self.from_date = QDate()
        self.to_date = QDate()
        self.last_clicked = ""

        hint_font = QFont()
        hint_font.setItalic(True)
        self.graph_hint = QLabel('Hint: you can interact with the graph using your mouse')
        self.graph_hint.setFont(hint_font)


        self.initUI()

    def initUI(self):
        """
        Positioning our differents widgets in our Layout and connect the widgets to their handler
        """

        grid = QGridLayout()
        grid.addWidget(self.from_currency_label, 0, 0, Qt.AlignRight)
        grid.addWidget(self.from_currency, 0, 1)
        grid.addWidget(self.to_currency_label, 0, 2, Qt.AlignRight)
        grid.addWidget(self.to_currency, 0, 3)
        grid.addWidget(self.from_amount_label, 1, 0)
        grid.addWidget(self.from_amount, 1, 1)
        grid.addWidget(self.to_amount_label, 1, 2)
        grid.addWidget(self.to_amount, 1, 3)

        grid.addWidget(self.from_calendar, 2, 0, 1, 2)
        grid.addWidget(self.to_calendar, 2, 2, 1, 2)

        grid.addWidget(self.rates_plot, 3, 0, 1, 4)
        grid.addWidget(self.graph_hint, 4, 0, 1, 4)

        self.rates_plot.showGrid(x=True, y=True)
        self.rates_plot.setLabel('left', 'Rate')
        self.rates_plot.setLabel('bottom', 'Days')
        self.legend = self.rates_plot.addLegend()

        self.setLayout(grid)
        self.setWindowTitle('Currency Converter - Assignment 1 - Arnaud Bourget - 2981151')

        self.from_currency.currentIndexChanged.connect(self.updateUI)
        self.to_currency.currentIndexChanged.connect(self.updateUI)
        self.from_amount.valueChanged.connect(self.fromAmountHandler)
        self.from_calendar.selectionChanged.connect(self.fromCalendarHandler)
        self.to_calendar.selectionChanged.connect(self.toCalendarHandler)

        self.show()

    def fromAmountHandler(self):
        """
        PyQt5 DoubleSpinBox Widget handler
        Allow to know that nothing in relationship with the graph changed
        """

        self.last_clicked = "amount"
        self.updateUI()
        self.last_clicked = ""

    def fromCalendarHandler(self):
        """
        PyQt5 Calendar Widget handler
        Allow to know which calendar was the last one used
        """

        self.last_clicked = "from"
        self.updateUI()

    def toCalendarHandler(self):
        """
        PyQt5 Calendar Widget handler
        Allow to know which calendar was the last one used
        """

        self.last_clicked = "to"
        self.updateUI()

    def updateUI(self):
        """
        PyQt5 Widgets handler

        This method fetches the information provided by the user and process
        them to get the conversion and the exchange rate graph
        """

        try:
            # Getting the values selected by the user
            from_ = self.from_currency.currentText()
            to = self.to_currency.currentText()
            from_amt = Decimal(self.getMostRecentRelevantRate(self.rates[from_]))
            to_amt = Decimal(self.getMostRecentRelevantRate(self.rates[to]))
            amt = Decimal(self.from_amount.value())

            # Calculating the new conversion value
            amount = (to_amt / from_amt) * amt
            self.to_amount.setText('%.02f' % amount)

            # Getting the dates selected by the user
            self.from_date = self.from_calendar.selectedDate().toPyDate()
            self.to_date = self.to_calendar.selectedDate().toPyDate()

            # Updating the graph only if something in relationship with it changes
            if self.last_clicked != 'amount':
                # Update the dates selected according to the user selection if the user selects a negative range
                if self.to_date < self.from_date:
                    if self.last_clicked == 'from':
                        date = self.from_calendar.selectedDate()
                        self.to_calendar.setSelectedDate(date)
                        self.to_date = date.toPyDate()
                    else:
                        date = self.to_calendar.selectedDate()
                        self.from_calendar.setSelectedDate(date)
                        self.from_date = date.toPyDate()

                # Getting and calculating the currencies rates according to the range selected by the user
                from_rates = self.getRatesInRange(self.rates[from_])
                to_rates = self.getRatesInRange(self.rates[to])
                conv_rates = self.getConvRates(from_rates, to_rates)

                # Getting the number of days included in the range
                nb_days = (self.to_date - self.from_date).days + 1
                date_range = range(0, nb_days)

                # Clearing the graph and the legend
                self.rates_plot.clear()
                self.legend.scene().removeItem(self.legend)
                self.legend = self.rates_plot.addLegend()

                # Updating the graph with our new values
                self.rates_plot.setXRange(0, nb_days)
                self.rates_plot.setYRange(0, max(from_rates + to_rates + conv_rates))
                self.rates_plot.plot(date_range, from_rates, pen='b', symbol='x', symbolPen='b', symbolBrush=0.2, name=from_)
                self.rates_plot.plot(date_range, to_rates, pen='r', symbol='o', symbolPen='r', symbolBrush=0.2, name=to)
                self.rates_plot.plot(date_range, conv_rates, pen='g', symbol='+', symbolPen='g', symbolBrush=0.2, name='conversion rate')
        except Exception as e:
            print('Failed to update UI')
            print(e)

    def getConvRates(self, from_rates, to_rates):
        """
        Calculation of the conversion rates from from_rates to to_rates

        :param from_rates: (list) The rates of the currency we're conversing from
        :param to_rates: (list) The rates to the currency we're conversing to
        :return: (list) The conversion rates
        """

        conv_rates = list()
        try:
            for i in range(len(from_rates)):
                conv_rates.append(to_rates[i] / from_rates[i] if from_rates[i] != 0 else 0)
        except Exception as e:
            print('Could not calculate the conversion rate')
            print(e)

        return conv_rates

    def getMostRecentRelevantRate(self, currency_rates, reference_date=QDate.currentDate().toPyDate()):
        """
        Retrieve the most recent relevant rate from the rates provided and according to the reference date

        :param currency_rates: (dictionary) The different rates of a currency ordered by date
        :param reference_date: (datetime.date, optional) The reference date that defines from when we're looking for
        :return: (string) The first relevant rate of the rates provided
        """

        try:
            for date in currency_rates:
                if QDate.fromString(date, "yyyy-MM-dd").toPyDate() <= reference_date and currency_rates[date] != 'N/A':
                    return currency_rates[date]
        except Exception as e:
            print('Could not retrieve any relevant rate')
            print(e)

    def getRatesInRange(self, currency_rates):
        """
        For each date between from_date and to_date, we retrieve the most recent rate

        :param currency_rates: (dictionary) The different rates of a currency ordered by date
        :return: (list) The list of the rates for everyday between from_date and to_date
        """

        rates = list()
        try:
            date = self.from_date
            while date <= self.to_date:
                rates.append(float(self.getMostRecentRelevantRate(currency_rates, date)))
                date += timedelta(days=1)
        except Exception as e:
            print('Could not retrieve rates')
            print(e)

        rates.reverse()
        return rates

    def getData(self):
        """
        Download the currency rates zipfile and process it into a dict
        """

        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip'
        try:
            file, _ = urlretrieve(url)
            zip_file_object = zipfile.ZipFile(file, 'r')
            first_file = zip_file_object.namelist()[0]
            file = zip_file_object.open(first_file)

            file_handler = []
            for row in file:
                file_handler.append(row.decode())

            # getting the currency headers into header_list
            header_list = []
            notFound = True
            x = 0
            while notFound:
                if file_handler[x].startswith('Date'):
                    header = file_handler[x].split(',')
                    for col in header:
                        header_list.append(col.strip())
                    notFound = False
                x += 1
            self.currencies = list(filter(None, header_list))
            self.currencies.append('EUR')
            self.currencies = self.currencies[1:]  # Removing the "Date" entry

            data = []
            for row in file_handler[x:]:
                if row.startswith('`\n'):
                    break
                else:
                    data.append(list(filter(None, [x.replace('\n', '') for x in row.split(',')])))  # Removing any empty extra columns at the end of each rows

            # filling my self.rates with the currency in the format {CURR: {date: rate, ...}, ...}
            for row in data:
                for i in range(len(self.currencies)):
                    try:
                        if self.currencies[i] not in self.rates:
                            self.rates[self.currencies[i]] = {row[0]: row[i + 1]}
                        else:
                            self.rates[self.currencies[i]].update({row[0]: row[i + 1]})
                    except IndexError:
                        # We reached the EUR section
                        if self.currencies[i] not in self.rates:
                            self.rates[self.currencies[i]] = {row[0]: '1.0000'}
                        else:
                            self.rates[self.currencies[i]].update({row[0]: '1.0000'})

            self.currencies.sort()

        except Exception as e:
            print('Failed to process the data')
            print(e)
        finally:
            file.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    currencyConverter = CurrencyConverter()
    sys.exit(app.exec_())