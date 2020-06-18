from pandas import DataFrame, Series
from json import load
from time import sleep, time
from sched import scheduler
from datetime import datetime

from .collector import Thunder
from .messenger import sendEmail

with open('settings.json', 'r') as f:
    settings = load(f)
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
                coins = input('¿Qué monedas quieres observar? Separalas por una coma o \'all\' para todas: ').replace(' ', '')
                delta_high = float(input('¿Qué cambio porcentual por arriba deseas que se te avise?: '))
                delta_low = -1 * float(input('¿Qué cambio porcentual por debajo deseas que se te avise?: '))
                valuation = input('¿A que valuación? \nall => General\nlast => ultima\n')
                period = float(input('¿Cada cuantos minutos quieres ver los cambios?: '))
                prompt = input('Observar monedas \'{}\' cada {} minutos y notificar en caso de un cambio de +{}% o {}% en la valuación \'{}\'   [Y, n]'.format(coins, period, delta_high, delta_low, valuation))
                params_set = True if prompt.lower() == 's' or prompt == ''  else False
            self.coins = {coin: self.db.retrieveValuation(coin) for coin in coins}
            self.myValuation = {coin: self.db.retrieveValuation(coin) if 'all' in valuation else self.db.retrieveLastValuation(coin) for coin in coins}
            self.delta = [delta_high, delta_low]
            self.period = period
        # Default params
        else:
            # Default params
            self.coins = settings['alert']['coins']
            self.myValuation = {coin: self.db.retrieveValuation(coin) for coin in self.coins}
            self.delta = settings['alert']['delta']
            self.period = settings['alert']['period']
        print(self.__str__())
        # Configuring the event
        self.looper = scheduler(time, sleep)
        self.checkStocks()

    def setCheck(self):
        self.looper.enter(60 * self.period, 1, self.checkStocks)
        self.looper.run()
        
    def checkStocks(self):
        # Would be good have a log of it...
        currentValuation = {coin: Thunder.getCoinValuation(symbols[coin]) for coin in self.coins}
        df = DataFrame([self.myValuation, currentValuation])
        # First, calculating the changes
        change = ( df.iloc[1] - df.iloc[0] ) * 100 / df.iloc[0]
        # TODO: Insert fire to predict cool stuff even though it is not over threshold
        # Retrieve those which are the trigger
        sell = change[change > self.delta[0]] if len(change[change > self.delta[0]]) > 0 else None
        buy = change[change < self.delta[1]] if len(change[change < self.delta[1]]) > 0 else None
        # Enviando el mensaje de alerta
        self.compose({'sell': sell, 'buy': buy, 'tendencies': None}, change)
        self.setCheck()

    def compose(self, params, changes:Series):
        send = False
        temp_msg = 'Hola! Un mensaje de Lucas!'
        quickValuate = lambda coin: self.db.retreiveBalance(self.db.getCoin(coin)) * self.db.retrieveValuation(self.db.getCoin(coin), 'mxn')
        if params['sell']:
            send = True
            temp_msg += '\nVENTA:\n'
            data = params['sell']
            # Moneda, cambio%, cantidad invertida => cantidad con valuación actual
            temp_msg += '\n'.join(['{}: {:.3f}%  {:.2f} => +{:.2f}'.format(data.index[i], value,quickValuate(data.index[i]), (value / 100) * quickValuate(data.index[i])) for (i, value) in enumerate(data)]) + '\n'
        if params['buy']:
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
        resume_string = '[{}] Cambios presentados => '.format(datetime.now().strftime('%H:%M'))
        return resume_string + " ".join(['{}: {:.3f}%  '.format(change.index[i], value) for (i, value) in enumerate(change)])


    def __str__(self):
        return 'Observar monedas {} cada {} minutos y notificar en caso de un cambio de +{}% o {}% sobre tu valuación'.format(', '.join(self.coins), self.period, self.delta[0], self.delta[1]) 

