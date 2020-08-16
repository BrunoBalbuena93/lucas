from pandas import DataFrame, Series
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import BayesianRidge
from sklearn.svm import SVR
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import train_test_split
from scipy.ndimage import gaussian_filter1d

from .collector import Thunder

'''
Fire es la instancia que contiene todos los datos. 
Inicialmente se le da el valor de un día anterior.

+ df: Valor "historico" de 1 día
+ sma & ema: Indicadores
+ tendency: Valor de las ultimas 5h
'''

class Fire():
    def __init__(self, coin:str, df: DataFrame, window=12, test:bool=False):
        super(Fire, self).__init__()
        self.coin = coin
        # Initial data from 1 day
        self.df = df.dropna()
        self.windowSize = window
        # Generando SMA
        self.sma = self.getSMA(self.windowSize, self.df['close'])
        # Generando EMA
        self.ema = self.getEMA(self.windowSize, self.df['close'])
        # Obteniendo datos de las ultimas 5 horas
        self.setCurrent()


    def setCurrent(self):
        temp = Thunder.get5h(self.coin)['close'].dropna()
        N = len(temp)
        self.data = DataFrame([temp.values, self.ema.values[-N:], self.sma.values[-N:]], index=['price', 'ema', 'sma']).T


    def updateData(self, retValue=False):
        try:
            value = Thunder.getCoinValuation(self.coin)
            # Calculando EMA
            new_ema = value * (2 / (1 + self.windowSize)) + self.ema.values[-1] * (1 - (2/(1 + self.windowSize)))
            # Caluclando SMA
            new_sma = (self.data['price'].values[-self.windowSize + 1:].sum() + value) / self.windowSize
            # Agregando a data
            self.data = self.data.append({'price': value, 'ema': new_ema, 'sma': new_sma}, ignore_index=True)
            if retValue:    return Series({'price': value, 'ema': new_ema, 'sma': new_sma}, name=self.coin)
        except:
            pass

    # Retrieving data 
    def getData(self, t: int=0):
        return self.df[self.df.index > t]

    # Last value of the retrieved data
    def valueNow(self):
        return Series([self.df['close'].values[-1], self.sma.values[-1], self.ema.values[-1]], index=['close', 'sma', 'ema'])

    # Train models
    def trainModels(self, dates:np.array, scaler:MinMaxScaler):
        # First, splitting data
        x_train, x_test, y_train, y_test = train_test_split(scaler.transform(dates.reshape(-1, 1)), self.data_scaler.transform(self.tendency.values.reshape(-1 , 1)), test_size=0.2)
        x_train = np.vander(x_train.reshape(-1), self.n + 1, increasing=True)
        x_test = np.vander(x_test.reshape(-1), self.n + 1, increasing=True)
        # Bayesian Ridge
        bayRidge = BayesianRidge(tol=1e-6, compute_score=True)
        bayRidge.set_params(alpha_init=1, lambda_init=0.001)
        bayRidge.fit(x_train, y_train.reshape(-1))
        bayScore = bayRidge.score(x_test, y_test.reshape(-1))
        # SVR
        svr_rbf = SVR(kernel='rbf', C=1, gamma=0.25)
        svr_rbf.fit(x_train, y_train.reshape(-1))
        svr_score = svr_rbf.score(x_test, y_test.reshape(-1))
        return bayRidge, svr_rbf, np.array([bayScore, svr_score])
        

    def alertForecast(self, forecast:int):
        # Here we should give an opinion on how it develops
        # Configuring the data
        dates = np.append(np.array(self.tendency.index.astype(np.int64)), Fire.composeDates(forecast))
        date_scaler = MinMaxScaler().fit(dates.reshape(-1, 1))
        # First, we retrieve the models (SVR & Bayes)
        bayes, svr, scores = self.trainModels(dates[:-forecast], date_scaler)
        x = date_scaler.transform(dates.reshape(-1, 1))
        x = np.vander(x.reshape(-1), self.n + 1, increasing=True)
        y_bayes = self.data_scaler.inverse_transform(bayes.predict(x).reshape(-1,1)).reshape(-1)
        y_svr = self.data_scaler.inverse_transform(svr.predict(x).reshape(-1,1)).reshape(-1)
        # print('Bayes: {}  SVR: {}'.format(scores[0], scores[1]))
        # scores = scores.clip(min=0)
        calculateError = lambda y, fx: 1 - np.sqrt(sum((y - fx) ** 2)) / len(y)
        bayesError = calculateError(self.ema.values[-forecast:], y_bayes[-2*forecast:-forecast])
        svrError = calculateError(self.ema.values[-forecast:], y_svr[-2*forecast:-forecast])
        y_error = (y_bayes[-forecast:] * bayesError  + y_svr[-forecast:] * svrError) / (bayesError + svrError)
        y_score = (y_bayes[-forecast:] * scores[0] + y_svr[-forecast:] * scores[1]) / sum(scores)
        y_ = (y_error + y_score) / 2
        # plt.plot(self.tendency.index, self.tendency.values, label='real')
        # plt.plot(dates, y_bayes, label='bayes')
        # plt.plot(dates, y_svr, label='svr')
        # plt.plot(dates[-forecast:], y_, label='forecast')
        # plt.plot(self.ema.index, self.ema.values, label='ema')
        # plt.title(self.coin)
        # plt.legend()
        # plt.show()
        return Series(y_, index=dates[-forecast:])
    
    @staticmethod 
    def getEMA(window:int, data:Series):
        ema = [data[0:window].mean()]
        [ema.append(value * (2 / (1 + window)) + ema[-1] * (1 - (2/(1+window)))) for value in data[window:].values]
        return Series(ema, index=data.index[window-1:])


    @staticmethod
    def getSMA(window:int, data:Series):
        sma = [data[i:window + i].mean() for i in range(len(data)-window +1)]
        return Series(sma, index=data.index[window-1:])


    @staticmethod 
    def composeDates(forecast: int):
        # Create the data for the forecast in dates (in order to train and test the models)
        now = dt.datetime.now()
        return np.array([int((now + dt.timedelta(minutes= i*5 + 1)).timestamp()) for i in range(forecast)])
        
    def __str__(self):
        return self.coin

if __name__ == '__main__':
    print(Fire.composeDates(5))