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
    def __init__(self, test=False, deep=False):
        '''
        :param test: Bool que define si esta probando 
        :param deep: Incluir análisis a largo plazo?
        '''
        super(Thunder, self).__init__()
        # Retrieve settings from json
        self.setSettings()
        if test:
            self.getWindow('BTC-USD')
        else:
            # Now, request the window for each coin
            [self.getWindow(coin) for coin in self.symbols]
            if deep:
                [self.getHistorical(coin) for coin in self.symbols]
        

    def setSettings(self):
        '''
        Retrieve paramaters from json
        '''
        with open('settings.json', 'r') as f:
            rawData = load(f)
        data = rawData['thunder']
        # Definiendo términos
        # Las divisas que se están observando
        self.symbols = symbols
        # Nombre de las monedas
        self.coins = [entry[:3].lower() for entry in self.symbols]
        
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
        # Diccionario donde se tendrán los datos
        self.data = dict()

        # Propiedades a largo plazo
        data = data['long']
        # Periodo a recuperar
        self.longPeriod = data['period']
        # Rango de tiempo a recuperar
        self.longRange = data['range']
        # Sensibilidad a largo plazo
        self.longInterval = data['interval']
        # Data
        self.longData = dict()   

    # Request para solicitar el historico
    def getHistorical(self, symbol, ret=False):
        self.longData[symbol[:3].lower()] = self.makeRequest('hist', symbol)
        if ret:
            return self.longData[symbol[:3].lower()]

    def refHistorical(self, symbol, ret=False):
        temp = self.makeRequest('refresh', symbol)
        if len(temp) > 0:
            # Comparando y haciendo cambios
            X: DataFrame = self.data[symbol[:3].lower()].copy()
            # Buscando a partir de que indice se cumple la continuidad. Medida preventiva
            try:
                idx = [i for i in temp.index if i > X.index[-1]][0]
                self.data[symbol[:3].lower()] = concat([X.iloc[idx + 1:], temp.iloc[idx:]])
            except IndexError:
                print('No hay datos nuevos')
        else:
            print('No hay datos nuevos')
        
        if ret:
            return self.data[symbol[:3].lower()]

    # Request to retrieve the data window 
    def getWindow(self, symbol, ret=False):
        self.data[symbol[:3].lower()] = self.makeRequest('window', symbol)
        if ret:
            return self.data[symbol[:3].lower()]

    # Request para hacer update de ventana
    def refreshWindow(self, symbol, ret=False):
        temp = self.makeRequest('update', symbol)
        try:
            # Comparando y haciendo cambios
            X: DataFrame = self.data[symbol[:3].lower()].copy()
            # Buscando a partir de que indice se cumple la continuidad. Medida preventiva
            try:
                idx = [i for i in temp.index if i > X.index[-1]][0]
                self.data[symbol[:3].lower()] = concat([X.iloc[idx + 1:], temp.iloc[idx:]])
            except IndexError:
                print('No hay datos nuevos')
        except:
            print('No hay datos nuevos')
        
        if ret:
            return self.data[symbol[:3].lower()]      
   
    def makeRequest(self, option:str, symbol: str):
        if 'window' in option:
            # ventana de semana
            period2 = dt.datetime.now()
            period1 = period2 - dt.timedelta(days=int(self.period[:-1]))
            interval = self.interval
        elif 'update' in option:
            period2 = dt.datetime.now()
            period1 = period2 - dt.timedelta(minutes=int(self.interval[:-1]))
            interval = self.interval
            # First, retrieve the new data
        elif 'hist' in option:
            period2 = dt.datetime.now()
            period1 = period2 - dt.timedelta(weeks=4*int(self.longPeriod[:-2]))
            interval = self.longInterval
        elif 'refresh' in option:
            period2 = dt.datetime.now()
            period1 = period2 - dt.timedelta(days=1)
            interval = self.longInterval
        else:
            print('No has seleccionado una opcion valida')
            return
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

    def getData(self, coin:str, window=0):
        df = self.data[coin]
        return df[df.index > window]

    def getDeepData(self, coin:str):
        return self.longData[coin]


def CM2CU(x1, divisor: str='usd'):
    params = {
            'symbols': 'MXN=X',
            'fields': 'regularMarketPrice'
        }
    req = requests.get('https://query1.finance.yahoo.com/v6/finance/quote', params=params)
    if req.ok:
        data = loads(req.content.decode())
        # x2 [=] MXN/USD
        x2 = data['quoteResponse']['result'][0]['regularMarketPrice']
        return 1 / (x1 * x2)
    else:
        return 0

    


if __name__ == "__main__":
    CM2CU(0.5)
