from json import load, loads
from pandas import DataFrame, Series, concat

import requests
import datetime as dt

'''
Aqui se implementa el observador de precios. 
En settings:
symbols: ['BTC-USD'] (Array de criptomonedas a dolar)
interval: 15m (15 minutos por default)
period: 5d (Cantidad de días atrás en los que te deseas fijar)

'''

# TODO: Migrar todo lo que tiene que ver con datos a Fire. Aqui solo son los parámetros de las requests

with open('settings.json', 'r') as f:
    symbols = load(f)['symbols']

class Thunder():
    def __init__(self):
        '''
        :param test: Bool que define si esta probando 
        :param deep: Incluir análisis a largo plazo?
        '''
        super(Thunder, self).__init__()
        # Retrieve settings from json
        with open('settings.json', 'r') as f:
            rawData = load(f)
        data = rawData['thunder']
        # Definiendo términos
        # Las divisas que se están observando
        self.symbols = Series(symbols, index=[value[:3].lower() for value in symbols])
        # A corto plazo:
        # El tamaño de ventana que se toma
        self.period = data['period']
        # Sensibilidad del intervalo
        self.regularInterval = data['interval']
        self.interval = data['interval']
        # Sensibilidad extraordinaria
        self.pinchInterval = data['pinch-interval']
        # Por default, el intervalo es normal
        self.isPinch = False
        # Propiedades a largo plazo
        data = data['long']
        # Periodo a recuperar
        self.longPeriod = data['period']
        # Rango de tiempo a recuperar
        self.longRange = data['range']
        # Sensibilidad a largo plazo
        self.longInterval = data['interval']

    # Setting dates for a certain request
    def getFromDates(self, coin:str, date_top: dt.datetime, date_bottom: dt.datetime=None, timespan:dict=None):
        '''
        To retrieve data from a different point in time. It works either with 2 dates or
        with an intial date and a timespan to the past. 
        '''
        # First, check if the entries are correct
        if not date_bottom and not timespan:
            print('Incomplete data, you must write a date or a timespan')
            return
        if date_bottom:
            print('Date based selected')
            date2 = date_top
            date1 = date_bottom
        if timespan:
            print('Timespan selected')
            date2 = date_top
            tm = list(timespan.keys())[0]
            if tm in ['days', 'hours', 'minutes']:
                date1 = date_top - dt.timedelta(tm=timespan[tm])
        return self.makeRequest('', self.symbols[coin], date2, date1)


    # Request para solicitar el historico
    def getHistorical(self, symbol):
        return self.makeRequest('hist', self.symbols[coin])
        

    # Request to retrieve the data window 
    def getWindow(self, coin:str):
        return self.makeRequest('window', self.symbols[coin])
  
    def getInterval(self):
        return self.interval
   
    def makeRequest(self, option:str, symbol: str, date2: dt.datetime=None, date1: dt.datetime=None):
        # For regular update
        if not date1 and not date2:
            if 'window' in option:
                # ventana de semana
                period2 = dt.datetime.now()
                period1 = period2 - dt.timedelta(days=int(self.period[:-1]))
                interval = self.interval
            elif 'hist' in option:
                period2 = dt.datetime.now()
                period1 = period2 - dt.timedelta(weeks=4*int(self.longPeriod[:-2]))
                interval = self.longInterval
            else:
                print('No has seleccionado una opcion valida')
                return
        else:
            # Retrieving between certain dates
            period2 = date2
            period1 = date1
            interval = self.interval
        # Configuring params for the query
        params = {
            'symbols': symbol,
            'period1': int(period1.timestamp()),
            'period2': int(period2.timestamp()),
            'interval': interval,
            'lang': 'en-US',
            'region': 'US',
            'corsDomain': 'finance.yahoo.com'
        }
        print('Collecting {}'.format(symbol[:3].lower()))
        req = requests.get('https://query1.finance.yahoo.com/v8/finance/chart/{}'.format(symbol), params=params)
        if req.ok:
            try:
                # Construyendo dataframe
                data = loads(req.content.decode())
                t = data['chart']['result'][0]['timestamp']
                indicators = data['chart']['result'][0]['indicators']['quote'][0]
                # Asignando el valor al diccionario
                return DataFrame([Series(indicators[key], index=t, name=key) for key in indicators.keys()]).T
            except KeyError:
                return None
        else:
            return None



def ToDT(date:str, startYear:bool=False):
    '''
    str(date) => datetime object
    '''
    current_year = dt.date.today().strftime('%Y')
    c = date[:-2] + current_year if current_year not in date else date
    return dt.datetime.strptime(c, '%d-%m-%Y')

if __name__ == "__main__":
    CM2CU(0.5)
