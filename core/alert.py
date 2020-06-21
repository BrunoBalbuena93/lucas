from pandas import DataFrame, Series
from json import load
from time import sleep, time
from sched import scheduler
from datetime import datetime

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
            params_set = False
            while not params_set:
                coins = input('¿Qué monedas quieres observar? Separalas por una coma o \'all\' para todas: ').replace(' ', '').split(',')
                # Handling deltas
                if 'all' in coins:  coins = self.db.retrieveCoins()
                deltas = {coin: {X: float(entry) for X,entry in zip(['over', 'under'], input('Indica el cambio porcentual separados por un espacio por arriba y por debajo de la moneda {}: '.format(coin)).split())} for coin in coins}
                valuation = input('¿A que valuación? \nall => General\nlast => ultima\n')
                period = float(input('¿Cada cuantos minutos quieres ver los cambios?: '))
                msg = 'Observar cada {} minutos y notificar si los cambios son de:\n'.format(period) + '\n'.join(['{}: +{}%  -{}%'.format(key, deltas[key]['over'], deltas[key]['under']) for key in deltas.keys()]) 
                prompt = input(msg)
                params_set = True if prompt.lower() == 's' or prompt == ''  else False
            self.coins = {coin: self.db.retrieveValuation(coin) for coin in coins}
            self.myValuation = valuation
            self.delta = DataFrame(deltas)
            self.period = period
        # Default params
        else:
            # Default params
            self.coins = default['coins']
            self.myValuation = default['valuation']
            self.delta = DataFrame(default['limits'])
            self.period = default['period']
        print(self.__str__())
        # Configure the thing in memory

        # Configuring the event
        self.looper = scheduler(time, sleep)
        self.checkStocks()

    def setCheck(self):
        self.looper.enter(60 * self.period, 1, self.checkStocks)
        self.looper.run()
        
    def checkStocks(self):
        # Would be good have a log of it...
        data = {coin: Fire(coin, Thunder.get5h(symbols[coin])) for coin in self.coins}
        
        df = DataFrame({coin: data[coin].valueNow() for coin in self.coins}).append(Series({coin: self.db.retrieveValuation(coin) if 'all' in self.myValuation else self.db.retrieveLastValuation(coin) for coin in self.coins}, name='self'))
        # Calculate differences (%) between reality and indicator
        df.loc['growth'] = (df.loc['close'] - df.loc['ema']) * 100 / df.loc['ema']
        # Calculate differences (%) in the slow growth
        df.loc['slow'] = (df.loc['close'] - df.loc['sma']) * 100 / df.loc['sma']
        # Calculate differences (%) between reality and own valuation
        df.loc['dif'] = (df.loc['close'] - df.loc['self']) * 100 / df.loc['self']
        # TODO: Insert fire to predict cool stuff even though it is not over threshold

        # TODO: Guardar el historial como un diccionario local aquí!!


        # Is it a big leap?
        sell = df.loc['growth'][df.loc['growth'] > self.delta.loc['over']] if len(df.loc['growth'][df.loc['growth'] > self.delta.loc['over']]) > 0 else None
        buy = df.loc['growth'][df.loc['growth'] < -1 * self.delta.loc['under']] if len(df.loc['growth'][df.loc['growth'] < -1 * self.delta.loc['under']]) > 0 else None
        # TODO: Guardar en memoria si este aviso ya fue dado
        # Enviando el mensaje de alerta
        self.compose({'sell': sell, 'buy': buy, 'tendencies': None}, df.loc[['growth', 'dif']].T)
        self.setCheck()

    def compose(self, params, changes:DataFrame):
        send = False
        temp_msg = 'Hola! Un mensaje de Lucas!'
        quickValuate = lambda coin: self.db.retreiveBalance(self.db.getCoin(coin)) * self.db.retrieveValuation(self.db.getCoin(coin), 'mxn')
        if type(params['sell']) == Series:
            send = True
            temp_msg += '\nVENTA:\n'
            data = params['sell']
            # Moneda, cambio%, cantidad invertida => cantidad con valuación actual
            temp_msg += '\n'.join(['{}: {:.3f}%  {:.2f} => +{:.2f}'.format(data.index[i], value,quickValuate(data.index[i]), (value / 100) * quickValuate(data.index[i])) for (i, value) in enumerate(data)]) + '\n'
        if type(params['buy']) == Series:
            send = True
            temp_msg += '\nCOMPRA:\n'
            data = params['buy']
            # Moneda, cambio%, cantidad invertida => cantidad con valuación actual
            temp_msg += '\n'.join(['{}: {:.3f}%  {:.2f} => {:.2f}'.format(data.index[i], value, quickValuate(data.index[i]), (value / 100) * quickValuate(data.index[i])) for (i, value) in enumerate(data)]) + '\n'
        if not params['tendencies']:
            temp_msg += '\nTe sugiero checar las gráficas, no tengo implementado el ML'            
        if send:
            sendEmail('Lucas Alert!', temp_msg)
        print(self.resume(changes))
        

    def resume(self, change, tendency=None):
        resume_string = '[{}] => '.format(datetime.now().strftime('%H:%M'))
        return resume_string + " ".join(['{}: {:.2f} | {:.2f} '.format(change.index[i], change['growth'].iloc[i], change['dif'].iloc[i]) for i in range(len(change))])


    def __str__(self):
        return 'Observar cada {} minutos y notificar si los cambios son de:\n'.format(self.period) + '\n'.join(['{}: +{}%  -{}%'.format(key, self.delta[key]['over'], self.delta[key]['under']) for key in self.delta.keys()]) 

