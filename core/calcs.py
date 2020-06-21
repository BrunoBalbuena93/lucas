from pandas import DataFrame, Series
from numpy import c_

import matplotlib.pyplot as plt

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
        self.df = df
        self.tendency = df.apply(lambda x: x[['close', 'open']].mean(), axis=1).dropna(axis=0)
        self.sma = self.getSMA(24, self.df['close']).dropna()
        self.ema = self.getEMA(24, self.df['close']).dropna()   
        
   
    # Retrieving data 
    def getData(self, t: int=0):
        return self.df[self.df.index > t]

    def valueNow(self):
        return Series([self.df['close'].values[-1], self.sma.values[-1], self.ema.values[-1]], index=['close', 'sma', 'ema'])

    def forecast(self):
        raise NotImplementedError
        

    @staticmethod 
    def getEMA(window:int, data:Series):
        ema = [data[0:window].mean()]
        [ema.append(value * (2 / (1 + window)) + ema[-1] * (1 - (2/(1+window)))) for value in data[window:].values]
        return Series(ema, index=data.index[window-1:])

    @staticmethod
    def getSMA(window:int, data:Series):
        sma = [data[i:window + i].mean() for i in range(len(data)-window +1)]
        return Series(sma, index=data.index[window-1:])

    # @staticmethod 
    # def getMACD(window1: int, window2: int, data: Series):
    #     ema_w1 = self.getEMA(window1, data)
    #     ema_w2 = self.getEMA(window2)[-len(ema_w1):]
    #     macd = Series([(e2 - e1) for (e2, e1) in nc_[ema_w2.values, ema_w1.values]], index=ema_w1.index)
    #     sigline = self.getEMA(9, macd)
    #     hist = Series([(e2 - e1) for (e2, e1) in nc_[macd.values[-len(sigline):], sigline.values]], index=sigline.index)
    #     return macd, sigline, hist