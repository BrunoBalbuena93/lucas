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
            self.metrics = params['params']
            self.coins = params['coins']
            self.myValuation = params['valuation']
            self.period = params['period']
            self.actions = params['actions']
            self.forecast = params['forecast']
            metrics = [DataFrame(params[metric]) for metric in self.metrics]
            growth = DataFrame(params['growth'])
            dif = DataFrame(params['dif'])
            day = DataFrame(params['day'])
            custom = DataFrame(params['custom'])
            self.actions = params['actions']
            self.upperLimit = DataFrame([S.loc['over'] for S in metrics], index=self.metrics)
            self.lowerLimit = DataFrame([S.loc['under'] for S in metrics], index=self.metrics)
            
        # Default params
        else:
            self.metrics = settings['alert']['params']
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
            # Generando el colector
            thunder = Thunder()
            # Generando los fire
            self.fires = {coin: Fire(coin, thunder.getWindow(coin)) for coin in self.coins}
            # DataFrame de apoyo
            self.history = DataFrame([Series({coin: 0 for coin in self.coins}, name=param) for param in self.metrics], index=self.metrics)
            # Configuring the event
            self.canSend = False
            self.looper = scheduler(time, sleep)
            self.checkStocks()
        except UnboundLocalError:
            print('Hubo un error, intentalo de nuevo')

    def setCheck(self):
        self.canSend = True
        self.looper.enter(60 * self.period, 1, self.checkStocks)
        self.looper.run()
        
    def checkStocks(self):
        '''
        
        '''
        # Actualizando datos
        df = DataFrame([f.updateData(True) for f in self.fires.values()]).T.append(Series({coin: self.db.retrieveValuation(coin) if 'all' in self.myValuation else self.db.retrieveLastValuation(coin) for coin in self.coins}, name='self'))      
        # Indica si se generan cambios súbitos con respecto a la tendencia actual mediante EMA
        df.loc['growth'] = (df.loc['price'] - df.loc['ema']) * 100 / df.loc['ema'] if 'growth' in self.metrics else [0] * len(self.coins)
        # Diferencia entre el valor actual y mi valuación
        df.loc['dif'] = (df.loc['price'] - df.loc['self']) * 100 / df.loc['self'] if 'dif' in self.metrics else [0] * len(self.coins)
        # Comparativa con lo esperado durante 1 día
        df.loc['day'] = (df.loc['price'] - df.loc['sma']) * 100 / df.loc['sma'] if 'day' in self.metrics else [0] * len(self.coins)
        # Custom que es lo mismo que price
        df.loc['custom'] = df.loc['price'] if 'custom' in self.metrics else [0] * len(self.coins)
        # print(self.metrics)
        # TODO: Aquí va la magia de esto
        # try:
        # Starting with ML
        # predict = DataFrame([data[coin].alertForecast(self.forecast) for coin in self.coins], index=self.coins).T
        # print(predict)
        # except:
        #     pass
        # TODO: Guardar el historial como un diccionario local aquí!!

        # Is it a big leap?
        msg = self.compareValues(df.loc[self.metrics])
        # Enviando el mensaje de alerta
        self.compose(msg)
        self.resume(df.loc[['price', 'dif']].T)
        # # except:
        # #     print('Ocurrió un error al recibir los datos')
        self.setCheck()


    def compareValues(self, df: DataFrame):
        '''
        Comparamos los resultados individuales
        '''
        # TODO: Configurar tolerancia desde los settings
        tol = 0.3
        
        # Calculando diferencias respecto al threshold
        up = DataFrame([Series(np.where(df.loc[metric] >= self.upperLimit.loc[metric], df.loc[metric], 0), name=metric) for metric in self.metrics])
        do = DataFrame([Series(np.where(-df.loc[metric] > self.lowerLimit.loc[metric], -df.loc[metric], 0), name=metric) if 'custom' not in metric else Series(np.where(df.loc[metric] < self.lowerLimit.loc[metric], df.loc[metric], 0), name=metric) for metric in self.metrics])
        temp = up - do
        temp.columns = self.coins
        # temp tiene los cambios que valen la pena notificar, ahora se compara con history
        transition = DataFrame([Series(np.where(np.abs(temp.loc[metric] - self.history.loc[metric]) > tol, temp.loc[metric], self.history.loc[metric]), name=metric) for metric in self.metrics])
        transition.columns = self.coins
        msg = None if transition.equals(self.history) else transition
        # print('History:\n{}\nTransition:\n{}\nHistory == Transition {}'.format(self.history, transition, transition.equals(self.history)))
        self.history = transition
        return msg

        
    def compose(self, msg:DataFrame or None):
        '''
        
        '''
        if msg is None:
            return
        temp_msg = 'Hola! Un mensaje de Lucas!\n'
        header = {'growth': 'crecimiento inesperado', 'dif': 'cambio respecto a valuacion', 'day': 'cambio con respecto al promedio de hoy', 'price': 'cambio Custom', 'custom': 'cambio Custom'}
        quickValuate = lambda coin: self.db.retrieveBalance(coin, many=True)[2]
        for kind in msg.index:
            # Tiramos los na
            data = msg.loc[kind][msg.loc[kind] != 0]
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
        print(resume_string + " ".join(['{}: {:.3f} | {:.2f}%'.format(change.index[i], change['price'].iloc[i], change['dif'].iloc[i]) for i in range(len(change))]))


    def __str__(self):
        return 'Observar cada {} minutos y notificar si los cambios son por encima de:\n{}\nO debajo de:\n{}'.format(self.period, self.upperLimit, self.lowerLimit)

