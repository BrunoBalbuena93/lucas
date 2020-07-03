import sqlite3
import datetime as dt
from os.path import isfile
from pandas import DataFrame, concat, Series
from requests import get
from json import loads, load, dump

"""
Nombres de las tablas:
wCoin [id, coin]: Nombre de monedas trabajadas
wTrades [id, initial, final]: Tipo de transacción de moneda
trades [id, type(wTrade), initial, final, cost, date,]
balances [coin, amount, valuation]
"""
with open('settings.json', 'r') as f:
    settings = load(f)


class DataManager():
    def __init__(self, name='records/records.db', test=False):
        super(DataManager, self).__init__()
        if not isfile(name):
            print('Inicializando base de datos')
            Initializer(path=name)
        if test:
            print('Corriendo en modo de prueba. Sin escritura en DB')
        self.name = name
        self.conn = sqlite3.connect(name)
        self.cursor = self.conn.cursor()
        self.test = test
    

    # Funciones de escritura
    # Agregando transacción
    def addTrade(self, trade):
        """
        Funcion para agregar transacción hecha
        trade: {init: [cantidad, moneda], final: [cantidad, moneda], 'addFund': bool}
        """
        
        # Agregamos fondos en caso que sea necesario
        if trade['addFunds'] == 1:
            # Agregando candado, pero no tendría porque salir error
            if 'mxn' in trade['init'][1] :
                self.addFund(trade['init'][0])
        # Primero obtenemos las monedas
        involved_coins = []
        for entry in ['init', 'final']:
            try:
                involved_coins.append(self.getCoin(trade[entry][1]))
            except:
                print("add")
                self.addCoin(trade[entry][1])
                involved_coins.append(self.getCoin(trade[entry][1]))
        init_coin = involved_coins[0]
        final_coin = involved_coins[1]
        # Obtenemos los symbols para requests que puedan ser necesarias
        symbols = [settings['coin-symbol'][trade[s][1]] for s in ['init', 'final'] if 'mxn' not in trade[s][1]]
        # Se obtiene el tipo de trade
        tradeType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={}'.format(init_coin, final_coin))[0][0]

        money = [trade['init'][0], trade['final'][0]]
        # Se obtiene la valuacion
        if len(symbols) == 1:
            # MXN <=> coin
            valuation = self.getValuation(symbols[0])
        else:
            # coin1 <=> coin2
            raise NotImplementedError
        
        # Calculando valuación [MXN => USD => coin]
        if 1 == init_coin:
            coin_valuation = (money[0] / valuation[0]) / money[1]
        if 1 == final_coin:
            coin_valuation = (money[1] / valuation[0]) / money[0]

        # Se agrega el timestamp
        date = dt.datetime.now().isoformat()

        # Se escribe en la base
        command = "INSERT INTO trades (type, init, final, coinusd, mxnusd, date) VALUES (?, ?, ?, ?, ?, ?);"
        self.write(command, params=[tradeType, money[0], money[1], coin_valuation, valuation[0], date])  
        print('Trade almacenado: {} {} => {} {}'.format(trade['init'][0], trade['init'][1], trade['final'][0], trade['final'][1]))
        # Actualizando el valor de balances    
        self.updateBalance(trade)
        # # Es retiro?
        # if 'mxn' in trade['final'][1]:
        #     self.addGains()
        # else:
        #     self.updateValuation()


    # Agregando fondos
    def addFund(self, fund:int or float):
        """
        fund = {amount: number, isInput: bool}
        """
        # Agregando fecha
        date = dt.datetime.now().isoformat()
        command = "INSERT INTO spei (amount, input, date) VALUES (?, ?, ?);"
        self.write(command, params=[fund, 1, date])
        print('Fondos almacenados correctamente')
        balance = self.retrieveBalance('mxn')
        balance += fund
        self.write('UPDATE balances SET amount = ? WHERE coin=?;', params=[balance, self.getCoin('mxn')])


    # Agregar monedas
    def addCoin(self, coin, symbol:str=''):
        # Se recogen las monedas existentes
        # Se agrega moneda
        coin_add = "INSERT INTO wCoin (coin) VALUES (?)"
        constrain = """SELECT id FROM wCoin WHERE coin = ?;"""
        if(self.uniqueWrite(coin_add, constrain, paramsCommand=[coin], paramsConstrain=[coin])):
            print('Moneda almacenada')
        coins = self.getCoins()
        # Agregando moneda a settings
        if len(symbol) == 0:
            symbol = input('Ingresa el simbolo de la moneda: ')
        with open('settings.json', 'r+') as f:
            settings = load(f)
            settings['coin-symbol'][coin] = symbol
            f.seek(0)
            dump(settings, f)
            f.truncate()
        new_coin_id = self.getCoin(coin)
        if new_coin_id in coins:
            coins.remove(new_coin_id) 
        # Se agregan los tipo de trade. Debe existir el que new_coin -> [coins] y [coins] -> new_coin
        for coin in coins:
            # Transaccion nueva a previas
            constrain = 'SELECT id from wTrade WHERE initial=? AND final=?;'
            add_trade = 'INSERT INTO wTrade (initial, final) VALUES (?, ?);'
            if(self.uniqueWrite(add_trade, constrain, paramsCommand=[coin, new_coin_id], paramsConstrain=[coin, new_coin_id])):
                print('Transacción {} => {} creada'.format(coin, new_coin_id))
            # Transaccion previas a nueva
            constrain = 'SELECT id from wTrade WHERE initial=? AND final=?;'
            add_trade = 'INSERT INTO wTrade (initial, final) VALUES (?, ?);'
            if(self.uniqueWrite(add_trade, constrain, paramsCommand=[new_coin_id, coin], paramsConstrain=[new_coin_id, coin])):
                print('Transacción {} => {} creada'.format(new_coin_id, coin))


    # Funciones de update
    # Balances
    def updateBalance(self, trade):
        """
        Función para actualizar montos. Recibe el mismo objeto trade {init: [cantidad, moneda], final: [cantidad, moneda], 'addFund': bool}
        """
        # Obteniendo valor de entrada
        _, balanceIn, mxnIn, valUSDIn, valMXNIn = self.retrieveBalance(trade['init'][1], many=True)
        _, balanceOut, mxnOut, valUSDOut, valMXNOut = self.retrieveBalance(trade['final'][1], many=True)
        balanceIn -= trade['init'][0]
        balanceOut += trade['final'][0]
        
        if 'mxn' in trade['init'][1]:
            rates = self.getValuation(trade['final'][1])
            # Agregar la nueva valuación al actual
            entryValuation = trade['init'][0] / trade['final'][0]
            # a1x1 + a2x2 = ax => x = (a1x1 + a2x2) / (a1 + a2)
            newMXNValuation = (trade['init'][0] + mxnOut) / (trade['init'][0] / entryValuation + mxnOut / valMXNOut) 
            newUSDValuation = newMXNValuation / rates[0]
            newMXNIn = mxnOut + trade['init'][0]
            # Escribiendo en MXN
            self.write('UPDATE balances SET amount=? WHERE coin=?;', [balanceIn, self.getCoin('mxn')])
            # Escribiendo en Moneda
            self.write('UPDATE balances SET amount=?, invested=?, valuationusd=?, valuationmxn=? WHERE coin=?;', 
            [balanceOut, newMXNIn, newUSDValuation, newMXNValuation, self.getCoin(trade['final'][1])])
        elif 'mxn' in trade['final'][1]:
            # Al salir no hacemos cambios en valuaciones, solo se retiran los fondos y se calcula la parte proporcional
            entryValuation = trade['final'][0] / trade['init'][0]
            factor = entryValuation / valMXNIn # Regresa el 1.x% extra generado
            newMXNIn = mxnIn - trade['final'][0] / factor
            # Escribiendo en MXN
            self.write('UPDATE balances SET amount=? WHERE coin=?;', [balanceOut, self.getCoin('mxn')])
            # Escribiendo en coin
            self.write('UPDATE balances SET amount=?, invested=? WHERE coin=?;', [balanceIn, newMXNIn, self.getCoin(trade['init'][1])])
        else:
            raise NotImplementedError('Aun no se configura el exchange entre monedas')

        print('Balances actualizados')
        

    # Valuation
    def updateValuation(self):
        '''
        This method is used in case there is an error in the regular calculation of valuations.
        Update the current valuation of the money invested. In other words, on average how much you paid for the amount
        of crypto 
        dot(A, X) = y
        au => término respecto a usd
        ax => término respecto a mxn
        '''
        # Retrieve the coins to find the trades
        coins = self.retrieveCoins()
        for coin in coins:
            # Retrieve the trades of a coin
            inv_trades, gain_trades = self.tradesOf(coin)
            # Calculation of valuation
            inv_trades['au'] = inv_trades['amount'] 
            inv_trades['xu'] = 1 / (inv_trades['valuecoinusd'] * inv_trades['valueusdmxn'])
            inv_trades['ax'] = inv_trades['amount'] / inv_trades['valueusdmxn']
            inv_trades['xx'] = 1 / inv_trades['valuecoinusd']
            
            gain_trades['au'] = - gain_trades['amount']
            gain_trades['xu'] = 1 / (gain_trades['valuecoinusd'] * gain_trades['valueusdmxn'])
            gain_trades['ax'] = - gain_trades['amount'] / gain_trades['valueusdmxn']
            gain_trades['xx'] = 1 / gain_trades['valuecoinusd']
            trades = concat([inv_trades, gain_trades])
            valuation_usd = 1 / ((trades['ax'] * trades['xx']).sum() / trades['ax'].sum())
            valuation_mxn = 1 / ((trades['au'] * trades['xu']).sum() / trades['au'].sum())
            # Otros datos de balances
            invested = float(inv_trades['amount'].sum() - gain_trades['amount'].sum())
            self.write('UPDATE balances SET invested=?, valuationusd = ?, valuationmxn= ? WHERE coin=?;', params=[invested, valuation_usd, valuation_mxn, self.getCoin(coin)])    


    # Gains
    def addGains(self):
        """
        Deprecated
        """
        # Obteniendo el trade anterior con id
        lastTrade = self.read('SELECT id, type, init, final, coinusd FROM trades ORDER BY date DESC LIMIT 1')[0]
        # Checa que no exista el registro antes
        try:
            self.read('SELECT * FROM gains WHERE trade_id={};'.format(lastTrade[0]))[0][0]
            print('That records is already in DB')
            return
        except IndexError:
            # Recuperando moneda
            coin_id = int(self.read('SELECT initial FROM wTrade WHERE id={};'.format(lastTrade[1]))[0][0])
            # Recuperando la valuacion
            currentValuation = self.retrieveValuation(coin_id)
            gain = float('{:.4f}'.format(100 * (lastTrade[4] - currentValuation) / currentValuation ))
            command = '''INSERT INTO gains (trade_id, amount, gain, date) VALUES (?, ?, ?, ?);'''
            params = [lastTrade[0], lastTrade[3], gain, dt.datetime.now().isoformat()]
            self.write(command, params)
            print('Ganancia de {}% almacenada correctamente'.format(gain))
     

    # Reading functions
    # Coins id
    def getCoins(self):
        try:
            return [value[0] for value in self.read('SELECT id FROM wCoin;')]
        except:
            return False
            

    def getCoin(self, coin:str):
        try:
            return self.read('SELECT id FROM wCoin WHERE coin=\"{}\"'.format(coin))[0][0]
        except IndexError:
            raise ValueError('La moneda no existe')


    def retrieveCoins(self):
        try:
            return [value[0] for value in self.read('SELECT coin FROM wCoin;') if 'mxn' not in value[0]]
        except:
            return None


    def retrieveBalance(self, coin:str, many=False):
        try:
            if many:
                return self.read('SELECT * FROM balances WHERE coin={};'.format(self.getCoin(coin)))[0]
            return self.read('SELECT amount FROM balances WHERE coin={};'.format(self.getCoin(coin)))[0][0]
        except IndexError:
            return False

    # This returns the current valuation or the many valuations and the current one
    def retrieveValuation(self, coin: str, out:str='usd'):
        try:
            if type(coin) == str:
                # In case the user sets the string
                coin = self.getCoin(coin)
            if 'usd' in out:
                return self.read('SELECT valuation{} FROM balances WHERE coin={}'.format(out, coin))[0][0]
            return self.read('SELECT valuationmxn FROM balances WHERE coin={}'.format(coin))[0][0]
        except IndexError:
            return None


    def retrieveLastValuation(self, coin: str, out:str = 'usd'):
        try:
            return self.read('SELECT coin{} FROM trades WHERE type=(SELECT id FROM wTrade WHERE final={}) ORDER BY date;'.format(out, self.getCoin(coin)))[0][0]
        except:
            return None


    def retrieveAmount(self, coin: str):
        wTrade = self.read('SELECT id FROM wTrade where final={};'.format(self.getCoin(coin)))[0][0]
        # Now retrieving all the investment trades
        inv_trades = Series([value[0] for value in self.read('SELECT init FROM trades where type={};'.format(wTrade))]).sum()
        # Retrieve the type of transaction
        wTrade = self.read('SELECT id FROM wTrade where initial={};'.format(self.getCoin(coin)))[0][0]
        # Now retrieving all the investment trades
        gain_trades = Series([value[0] for value in self.read('SELECT final FROM trades where type={};'.format(wTrade))]).sum()
        return inv_trades - gain_trades

    # Returns all trades related with 2 coins
    def tradesOf(self, coin:str, base:str='mxn'):
        wType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin(base), self.getCoin(coin)))[0][0]
        entries = DataFrame(self.read('SELECT init, final ,coinusd, mxnusd FROM trades WHERE type={};'.format(wType)), columns=['amount', 'coin', 'valuecoinusd', 'valueusdmxn'], index=[value[0] for value in self.read('SELECT date FROM trades WHERE type={};'.format(wType))])
        wType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin(coin), self.getCoin(base)))[0][0]
        outries = DataFrame(self.read('SELECT final, init, coinusd, mxnusd FROM trades WHERE type={};'.format(wType)), columns=['amount', 'coin' ,'valuecoinusd', 'valueusdmxn'], index=[value[0] for value in self.read('SELECT date FROM trades WHERE type={};'.format(wType))])
        return [entries, outries]

    def tradesGUI(self, coin: str):
        type_1 =self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin('mxn'), self.getCoin(coin)))[0][0]
        type_2 =self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin(coin), self.getCoin('mxn')))[0][0]
        data = self.read('SELECT init, final, coinusd, date FROM trades WHERE type={} OR type={} ORDER BY date DESC;'.format(type_1, type_2))
        return DataFrame([Series([value[0], value[1], value[2]], name=value[3]) for value in data])

    # Funciones de consulta
    def getSuggestion(self, coin, threshold):
        '''
        Sirve para sugerirte o no una compra denotando la ganancia en el momento actual
        '''
        raise NotImplementedError


    def getPastProfits(self, coin:str):
        '''
        Regresa los datos de la ultima transacción 
        coin: Divisa crypto que se desea observar
        '''
        # FIXME: Reformular función
        # Retornar el valor de la ultima con ese tipo de moneda
        tradeType = self.read('''SELECT id FROM wTrade WHERE initial={};'''.format(self.getCoin(coin)))[0][0]
        trades = self.read('''SELECT trades.init, trades.final, gains.gain, gains.date FROM trades JOIN gains WHERE gains.trade_id = trades.id AND trades.type={};'''.format(tradeType))
        [print('Vendiste: {} {}  por {} mxn a una ganancia de {:.4f}% el día {}'.format(trade[0], coin, trade[1], trade[2], trade[3][:trade[3].index('T')])) for trade in trades]
        return [list(trade) for trade in trades]

    # Funciones Auxiliares
    def getTables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print(self.cursor.fetchall())

    # Only writes if it's unique
    def uniqueWrite(self, command: str, constrain: str, paramsCommand: list, paramsConstrain: list):
        try:
            self.cursor.execute(constrain, paramsConstrain)
            result = self.cursor.fetchall()
            if len(result) <= 0:
                self.write(command, paramsCommand)
                return True
            else:
                print('El valor ya existe con id: {}'.format(result[0][0]))
                return False
        except sqlite3.Error as e:
            print(e)
            return False                

    # Writing
    def write(self, command:str, params):
        # try:
        if self.test:
            print(command.replace('?', '{}').format(*params))
        else:
            self.cursor.execute(command, params)
            self.conn.commit()
        # except sqlite3.Error as e:
        #     print(e)

    def read(self, c):
        self.cursor.execute(c)
        return self.cursor.fetchall()

    def getInverseTrade(self, trade):
        (x, y) = self.read('''SELECT initial, final FROM wTrade WHERE id = {};'''.format(trade))[0]
        return self.read('''SELECT id FROM wTrade WHERE initial = {} AND final = {};'''.format(y, x))[0][0]


    def close(self):
        self.conn.close()

    def testMode(self):
        self.test = not self.test
        print('Has cambiado el test a {}'.format(self.test))

    def __str__(self):
        return self.name

    # Valuation reports
    def reportCoin(self, coin, current=False):
        # Retrieve the data from balances
        data = self.read('SELECT amount, invested, valuationusd, valuationmxn FROM balances WHERE coin={}'.format(self.getCoin(coin)))[0]
        currentValuation = [1, 1]
        if current:
            currentValuation = self.getValuation(settings['coin-symbol'][coin])
        return {
            'coin': coin,
            'mxnvalue': data[1],
            'valuation': data[2],
            'currentvalue': data[0] * currentValuation[1] * currentValuation[0],
            'currentvaluation': currentValuation[1]
        }

    # Tells how much money it has been invested
    def reportMXN(self, separate:bool):
        # TODO: Separar ganancias por moneda
        # First, retrieve the data from the balances (invested)
        coinInvested = sum([value[0] for value in self.read('SELECT invested FROM balances WHERE coin>{};'.format(self.getCoin('mxn')))])
        nonInvested = self.read('SELECT amount FROM balances WHERE coin={};'.format(self.getCoin('mxn')))[0][0]      
        speiFunds = sum([value[0] for value in self.read('SELECT amount FROM spei WHERE input=1;')])
        if separate:
            for coin in ['eth']:#self.retrieveCoins():
                mIn, mOut = self.tradesOf(coin, dates=True)
                print(mIn)
                print(mOut)
        return {'invested': coinInvested + nonInvested, 'spei': speiFunds, 'gains': coinInvested + nonInvested - speiFunds}


    # Trade blueprint
    @staticmethod
    def Trade(income, outcome, funds=0):
        """
        Trade funciona similar a una interfaz de javascript. Es un modelo
        que debe respetarse
        income/outcome = [cantidad, 'acrónimo de moneda']
        funds = Se agregan nuevos fondos?
        """
        if type(income) != tuple:   income = tuple(income) 
        if type(outcome) != tuple:  outcome = tuple(outcome)

        output = dict()
        for (state, value) in set(zip(['init', 'final'],[income, outcome])):
            try:
                if len(value[1]) == 3:
                    output[state] = [float(value[0]), value[1].lower()]
                else:
                    print('La moneda de {} no está bien colocada ({})'.format(state, value[1]))
            except ValueError:
                print('El valor de {} no es valido como entrada'.format(value[0]))
                return None
        output['addFunds'] = funds
        return output

    @staticmethod
    def getValuation(symbol: str):
        '''
        This retrieves the value of the MXN/USD and coin/USD to calculate a valuation afterwards
        '''
        params = {
            'symbols': 'MXN=X',
            'fields': 'regularMarketPrice'
        }
        req = get('https://query1.finance.yahoo.com/v6/finance/quote', params=params)
        if req.ok:
            data = loads(req.content.decode())
            usdmxn = data['quoteResponse']['result'][0]['regularMarketPrice']
        else:
            usdmxn = None
        # Retrieving the amount of coins/usd
        params = {
            'symbols': symbol,
            'fields': 'regularMarketPrice'
        }
        req = get('https://query1.finance.yahoo.com/v6/finance/quote', params=params)
        if req.ok:
            data = loads(req.content.decode())
            coinusd = data['quoteResponse']['result'][0]['regularMarketPrice']
        else:
            coinusd = None
        return [usdmxn, coinusd]

        


def Initializer(path='records/records.db'):
    """
    Aqui se inicializa la base de datos en caso de no existir
    """
    # Creando la base de datos
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    # Creando tabla wCoin
    wCoin = '''CREATE TABLE IF NOT EXISTS wCoin (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        coin TEXT
    );'''
    # Tabla de tipos de trade
    wTrade = '''CREATE TABLE IF NOT EXISTS wTrade (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        initial INTEGER,
        final INTEGER
    );'''
    # spei
    spei = '''CREATE TABLE IF NOT EXISTS spei (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        amount NUMERIC,
        input INTEGER,
        date TEXT
    );'''
    # Balances
    balances = '''CREATE TABLE IF NOT EXISTS balances (
        coin INTEGER PRIMARY KEY,
        amount NUMERIC,
        invested NUMERIC,
        valuationusd NUMERIC,
        valuationmxn NUMERIC
    );'''
    # trades
    trades = '''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        type INTEGER,
        init NUMERIC,
        final NUMERIC,
        coinusd NUMERIC,
        mxnusd NUMERIC,
        date TEXT
    );'''
    # retornos
    gains = '''CREATE TABLE IF NOT EXISTS gains (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        trade_id INTEGER,
        gain NUMERIC,
        date TEXT
    );'''

    [cursor.execute(com) for com in [wCoin, wTrade, spei, balances, trades, gains]]
    conn.commit()
    conn.close()






if __name__ == '__main__':
    db = DataManager(test=True)
    db.addTrade(DataManager.Trade([0.03830258, 'eth'], [200, 'mxn']))

