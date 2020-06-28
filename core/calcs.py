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
'''
Fire is the instance which has all the data
Here we make all the approaches and ML necessary 
I first thought to merge this one with Thunder, but since the processes are different
it may be good praxis to separate them (even thought they share the same data)
Afterwards, treat Thunder as a service and migrate everything of data to Fire

'''

class Fire():
    def __init__(self, coin:str, df: DataFrame, test:bool=False):
        super(Fire, self).__init__()
        self.coin = coin
        self.df = df.dropna()
        y_ = df.apply(lambda x: x[['close', 'open']].mean(), axis=1).dropna(axis=0)
        y_ = gaussian_filter1d(y_, y_.std() / 8)
        self.tendency = Series(y_)#, index=df.index)
        self.sma = self.getSMA(12, self.df['close']).dropna()
        self.ema = self.getEMA(12, self.df['close']).dropna()
        # Este es el escalador de precios (y)
        # self.findChanges()  
        self.data_scaler = MinMaxScaler().fit(self.tendency.values.reshape(-1, 1))   
        self.n = 4  
   

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
        

if __name__ == '__main__':
    print(Fire.composeDates(5))