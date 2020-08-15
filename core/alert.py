from pandas import DataFrame, Series, concat
from json import load
from time import sleep, time
from sched import scheduler
from datetime import datetime
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from .collector import Thunder
from .messenger import sendEmail
from .calcs import Fire

with open('settings.json', 'r') as f:
    settings = load(f)
default = settings['alert']
symbols = settings['coin-symbol']


class Alert():
    def __init__(self, options: list, DB):
        super(Alert, self).__init__()
        # DB Connection
        self.db = DB
        # Setting custom params
        if 'custom' in options:
            print('Using the defaults of alert_settings.json')
            with open('alert_settings.json','r') as f:
                params = load(f)
            metrics = params['params']
            self.coins = params['coins']
            self.myValuation = params['valuation']
            self.period = params['period']
            self.actions = params['actions']
            self.forecast = params['forecast']
            growth = DataFrame(params['growth'])
            dif = DataFrame(params['dif'])
            day = DataFrame(params['day'])
            custom = DataFrame(params['custom'])
            self.actions = params['actions']
            self.upperLimit = DataFrame([S.loc['over'] for S in [growth, dif, day, custom]], index=['growth', 'dif', 'day', 'custom'])
            self.lowerLimit = DataFrame([S.loc['under'] for S in [growth, dif, day, custom]], index=['growth', 'dif', 'day', 'custom'])
            
        # Default params
        else:
            metrics = settings['alert']['params']
            self.coins = default['coins']
            self.myValuation = default['valuation']
            self.period = default['period']
            self.forecast = default['forecast']
            self.actions = default['actions']
            growth = DataFrame(default['growth'])
            dif = DataFrame(default['dif'])
            day = DataFrame(default['day'])
            custom = DataFrame(default['custom'])
            self.upperLimit = DataFrame([S.loc['over'] for S in [growth, dif, day, custom]], index=['growth', 'dif', 'day', 'custom'])
            self.lowerLimit = DataFrame([S.loc['under'] for S in [growth, dif, day, custom]], index=['growth', 'dif', 'day', 'custom'])
            self.actions = default['actions']
            
        try:
            # Configure the thing in memory
            thunder = Thunder()
            self.avg = Series({coin: thunder.getWindow(coin)['close'].mean() for coin in self.coins})
            self.history = DataFrame([Series({coin: 0 for coin in self.coins}, name=param) for param in metrics], index=metrics)
            # Configuring the event
            self.canSend = False
            self.looper = scheduler(time, sleep)
            self.checkStocks()
        except AttributeError or TypeError:
            print('Hubo un error, intentalo de nuevo')

    def setCheck(self):
        self.canSend = True
        self.looper.enter(60 * self.period, 1, self.checkStocks)
        self.looper.run()
        
    def checkStocks(self):
        '''
        Condiciones que debería cumplir para avisar:
        Brincos grandes de valuación (|growth| > 2 %)
        Cuando la valuación respecto a la mía sea de X% (propuesta datos externos)

        '''
        # TODO: Fix en caso de que la data venga incompleta (Cosa del Fire)
        # try:
        # Would be good have a log of it...
        data = {coin: Fire(coin, Thunder.get5h(symbols[coin])) for coin in self.coins}
        
        df = DataFrame({coin: data[coin].valueNow() for coin in self.coins}).append(Series({coin: self.db.retrieveValuation(coin) if 'all' in self.myValuation else self.db.retrieveLastValuation(coin) for coin in self.coins}, name='self'))
        print(df)
        # Indica si se generan cambios súbitos con respecto a la tendencia actual mediante EMA
        df.loc['growth'] = (df.loc['close'] - df.loc['ema']) * 100 / df.loc['ema']
        # Indica si se generan cambios súbitos con respecto a la tendencia actual mediante SMA
        df.loc['slow'] = (df.loc['close'] - df.loc['sma']) * 100 / df.loc['sma']
        # Diferencia entre el valor actual y mi valuación
        df.loc['dif'] = (df.loc['close'] - df.loc['self']) * 100 / df.loc['self']
        # Comparativa con lo esperado durante 1 día
        df.loc['day'] = (df.loc['close'] - self.avg) * 100 / self.avg
        # TODO: Aquí va la magia de esto
        # try:
        # Starting with ML
        # predict = DataFrame([data[coin].alertForecast(self.forecast) for coin in self.coins], index=self.coins).T
        # print(predict)
        # except:
        #     pass
        # TODO: Guardar el historial como un diccionario local aquí!!

        # Is it a big leap?
        send, msg = self.compareValues(df)
        # Enviando el mensaje de alerta
        self.compose(send, msg)
        self.resume(df.loc[['close', 'dif']].T)
        # # except:
        # #     print('Ocurrió un error al recibir los datos')
        self.setCheck()


    def compareValues(self, df: DataFrame):
        '''
        Comparamos los resultados individuales
        '''
        tol = 0.3
        msg = []
        new_data = []
        for label in ['growth', 'dif', 'day']:
            # Change from alert
            change = concat([df.loc[label][df.loc[label] > self.upperLimit.loc[label]], 
                            df.loc[label][df.loc[label] < -self.upperLimit.loc[label]]])
            # Retrieve the past changes
            temp_change = self.history.loc[label]
            new_change = Series([change[coin] if coin in change.index and abs((temp_change[coin] - change[coin])) > tol else temp_change[coin] for coin in temp_change.index], index=temp_change.index, name=label)
            # las que se van a mensaje:
            change = change[new_change != temp_change]
            if len(change) > 0: 
                msg.append(change)
            new_data.append(new_change)
        
        # Para los customs
        # Change from alert
        change = concat([df.loc['close'][df.loc['close'] > self.upperLimit.loc['custom']], 
                        df.loc['close'][df.loc['close'] < -self.upperLimit.loc['custom']]])
        # Retrieve the past changes
        temp_change = self.history.loc['custom']
        new_change = Series([change[coin] if coin in change.index and abs((temp_change[coin] - change[coin]) * 100 / temp_change[coin]) > tol else temp_change[coin] for coin in temp_change.index], index=temp_change.index, name='custom')
        # las que se van a mensaje:
        change = change[new_change != temp_change]
        if len(change) > 0: 
            msg.append(change)
        new_data.append(new_change)
        new_data = DataFrame(new_data)
        self.history = DataFrame(new_data)
        if len(msg) > 0:
            return True, DataFrame(msg)
        return False, DataFrame([])


    def compose(self, send:bool, msg:DataFrame):
        temp_msg = 'Hola! Un mensaje de Lucas!\n'
        header = {'growth': 'crecimiento inesperado', 'dif': 'cambio respecto a valuacion', 'day': 'cambio con respecto al promedio de hoy', 'close': 'cambio Custom', 'custom': 'cambio Custom'}
        quickValuate = lambda coin: self.db.retrieveBalance(coin, many=True)[2]
        for kind in msg.index:
            # Tiramos los na
            data = msg.loc[kind].dropna()
            # Si hay mensaje?
            if len(data) > 0:
                send = True
                temp_msg += '\nHubo un {}:\n'.format(header[kind])
                temp_msg += '\n'.join(['{}: {:.3f}%  {:.2f} => {:.2f}'.format(data.index[i], value,quickValuate(data.index[i]), (value / 100) * quickValuate(data.index[i])) for (i, value) in enumerate(data)]) + '\n'

        temp_msg += '\nTe sugiero checar las gráficas, no tengo implementado el ML'  
        if send and self.canSend:
            sendEmail('Lucas Alert!', temp_msg)
        

    def resume(self, change, tendency=None):
        resume_string = '[{}] => '.format(datetime.now().strftime('%H:%M'))
        print(resume_string + " ".join(['{}: {:.3f} | {:.2f}%'.format(change.index[i], change['close'].iloc[i], change['dif'].iloc[i]) for i in range(len(change))]))


    def __str__(self):
        return 'Observar cada {} minutos y notificar si los cambios son por encima de:\n{}\nO debajo de:\n{}'.format(self.period, self.upperLimit, self.lowerLimit)

