import sqlite3
import datetime as dt
from os.path import isfile
from pandas import DataFrame, concat
from requests import get
from json import loads, load

"""
Nombres de las tablas:
wCoin [id, coin]: Nombre de monedas trabajadas
wTrades [id, initial, final]: Tipo de transacción de moneda
trades [id, type(wTrade), initial, final, cost, date,]
balances [coin, amount, valuation]
"""


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
        init_coin = self.getCoin(trade['init'][1])
        final_coin = self.getCoin(trade['final'][1])
        # Obtenemos los symbols para requests que puedan ser necesarias
        symbols = self.getSymbol(trade['init'][1], trade['final'][1])
        # Se obtiene el tipo de trade
        tradeType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={}'.format(init_coin, final_coin))[0][0]

        money = [trade['init'][0], trade['final'][0]]
        # Se obtiene la valuacion
        if len(symbols) == 1:
            # MXN <=> coin
            valuation = getValuation(symbols[0])
        else:
            # coin1 <=> coin2
            raise NotImplementedError
        
        # Se agrega el timestamp
        date = dt.datetime.now().isoformat()

        # Se escribe en la base
        command = "INSERT INTO trades (type, init, final, coinusd, mxnusd, date) VALUES (?, ?, ?, ?, ?, ?);"
        self.write(command, params=[tradeType, money[0], money[1], valuation[1], valuation[0], date])  
        print('Trade almacenado: {} {} => {} {}'.format(trade['init'][0], trade['init'][1], trade['final'][0], trade['final'][1]))
        # Actualizando el valor de balances    
        self.updateBalance(trade)
        # Actualizando gains
        if 'mxn' in trade['final'][1]:  self.updateGains(trade['init'][0], tradeType)

    # Agregando fondos
    def addFund(self, fund):
        """
        fund = {amount: number, isInput: bool}
        """
        if type(fund) == int:
            # Se coloca solo el nombre
            entry = fund
            isInput = 1
        else:
            entry = fund['amount']
            isInput = 1 if fund['isInput'] == True else -1
        # Agregando fecha
        date = dt.datetime.now().isoformat()
        command = "INSERT INTO spei (amount, input, date) VALUES (?, ?, ?);"
        self.write(command, params=[entry, isInput, date])
        print('Fondos almacenados correctamente')
        self.updateBalance({'init': [entry, 'mxn']})

    # Agregar monedas
    def addCoin(self, coin):
        # Se recogen las monedas existentes
        # Se agrega moneda
        coin_add = "INSERT INTO wCoin (coin) VALUES (?)"
        constrain = """SELECT id FROM wCoin WHERE coin = ?;"""
        if(self.uniqueWrite(coin_add, constrain, paramsCommand=[coin], paramsConstrain=[coin])):
            print('Moneda almacenada')
        coins = self.getCoins()
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
        for state in ['init', 'final']:
            try:
                # Primero corroboramos que exista el renglón
                balance = self.retreiveBalance(self.getCoin(trade[state][1]))
                amount = trade[state][0] if state == 'final' else -1 * trade[state][0]
                coin = self.getCoin(trade[state][1])
                if balance == False and balance != 0:
                    # Caso que no existe el renglón de la crypto
                    print('Inicializando registro de moneda {}'.format(trade[state][1]))
                    command = 'INSERT INTO balances (coin, amount) VALUES (?, ?);'
                    self.write(command, params=[coin, amount])
                else:
                    # Update normal
                    balance += amount
                    self.write('UPDATE balances SET amount = ? WHERE coin=?;', params=[balance, coin])
            except KeyError:
                pass
        print('Balances actualizados')
        self.updateValuation()
    
    # Gains
    def updateGains(self, amount, tradeType):
        """
        """
        # First, retrieve the trades to MXN
        lastTrade = self.read('''SELECT id  FROM trades WHERE type = {} ORDER BY date DESC'''.format(tradeType))[0][0]
        # Then, retrieve the updated balance. 
        coin = self.read('''SELECT initial FROM wTrade WHERE id={}'''.format(tradeType))[0][0]
        Yt = self.read('''SELECT amount  FROM balances WHERE coin={}'''.format(coin))[0][0]
        # Now, calculate valuation
        gain = '{:.6f}'.format(100 * amount / (amount + Yt))
        # Saving data
        command = '''INSERT INTO gains (trade_id, gain, date) VALUES (?);'''
        constrain = '''SELECT id FROM gains WHERE trade_id = ?;'''
        if self.uniqueWrite(command, constrain, [str(lastTrade), gain, dt.datetime.now().isoformat()], [lastTrade]):
            print('Ganancia de {}% almacenada correctamente'.format(gain))

    # Valuation
    def updateValuation(self):
        '''
        Update the current valuation of the money invested. In other words, on average how much you paid for the amount
        of crypto 
        dot(A, X) = y
        '''
        # Retrieve the coins to find the trades
        coins = self.getCoins()
        coins.remove(self.getCoin('mxn'))
        for coin in coins:
            # Retrieve the type of transaction
            wTrade = self.read('SELECT id FROM wTrade where final={};'.format(coin))[0][0]
            # Now retrieving all the investment trades
            inv_trades = DataFrame(self.read('SELECT init, coinusd, mxnusd FROM trades where type={};'.format(wTrade)), columns=['mxn', 'coinusd', 'mxnusd'])
            inv_trades['au'] = inv_trades['mxn'] 
            inv_trades['xu'] = 1 / (inv_trades['coinusd'] * inv_trades['mxnusd'])
            inv_trades['ax'] = inv_trades['mxn'] / inv_trades['mxnusd']
            inv_trades['xx'] = 1 / inv_trades['coinusd']
            # Retrieve the type of transaction
            wTrade = self.read('SELECT id FROM wTrade where initial={};'.format(coin))[0][0]
            # Now retrieving all the investment trades
            gain_trades = DataFrame(self.read('SELECT final, coinusd, mxnusd FROM trades where type={};'.format(wTrade)), columns=['mxn', 'coinusd', 'mxnusd'])
            gain_trades['au'] = - gain_trades['mxn']
            gain_trades['xu'] = 1 / (gain_trades['coinusd'] * gain_trades['mxnusd'])
            gain_trades['ax'] = - gain_trades['mxn'] / gain_trades['mxnusd']
            gain_trades['xx'] = 1 / gain_trades['coinusd']
            trades = concat([inv_trades, gain_trades])
            valuation_usd = 1 / ((trades['ax'] * trades['xx']).sum() / trades['ax'].sum())
            valuation_mxn = 1 / ((trades['au'] * trades['xu']).sum() / trades['au'].sum())
            self.write('UPDATE balances SET valuationusd = ?, valuationmxn= ? WHERE coin=?;', params=[valuation_usd, valuation_mxn, coin])
            

    # Reading functions
    # Coins id
    def getCoins(self):
        try:
            return [value[0] for value in self.read('SELECT id FROM wCoin;')]
        except:
            return False
            

    def getCoin(self, coin):
        try:
            return self.read('SELECT id FROM wCoin WHERE coin=\"{}\"'.format(coin))[0][0]
        except IndexError:
            return False


    def retrieveCoins(self):
        try:
            return [value[0] for value in self.read('SELECT coin FROM wCoin;') if 'mxn' not in value[0]]
        except:
            return False


    def getSymbol(self, c1:str, c2:str):
        '''
        Returns the symbols involved in the transaction, only if mxn is in there, will return None int it's place
        '''
        # First, loading the available symbols
        with open('settings.json', 'r') as f:
            data = load(f)
        # Now checking if the coins
        return [symbol for coin in [c1, c2] for symbol in data['symbols'] if coin.upper() in symbol]


    def retreiveBalance(self, coin):
        try:
            return self.read('SELECT amount FROM balances WHERE coin={}'.format(coin))[0][0]
        except IndexError:
            return False

    # This returns the current valuation or the many valuations and the current one
    def retrieveValuation(self, coin: str, out:str = 'usd'):
        try:
            if type(coin) == str:
                # In case the user sets the string
                coin = self.getCoin(coin)
            return self.read('SELECT valuation{} FROM balances WHERE coin={}'.format(out, coin))[0][0]
        except IndexError:
            return False


    def tradesOf(self, coin:str, base:str='mxn'):
        wType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin(base), self.getCoin(coin)))[0][0]
        entries = DataFrame(self.read('SELECT init, coinusd, mxnusd FROM trades WHERE type={};'.format(wType)), columns=['amount', 'valueusd', 'valuemxn'])
        wType = self.read('SELECT id FROM wTrade WHERE initial={} AND final={};'.format(self.getCoin(coin), self.getCoin(base)))[0][0]
        outries = DataFrame(self.read('SELECT init, coinusd, mxnusd FROM trades WHERE type={};'.format(wType)), columns=['amount', 'valueusd', 'valuemxn'])
        return [entries, outries]

        

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
    def write(self, command, params):
        try:
            if self.test:
                print(command)
            else:
                self.cursor.execute(command, params)
                self.conn.commit()
        except sqlite3.Error as e:
            print(e)

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


# Trade blueprint
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

# This is a Lucas function
def NewTrade(db:DataManager, data:list=None):
    print('Has seleccionado agregar un nuevo trade')
    if not data:
        data = [input('Ingresa el inicial: [cantidad][moneda(3caracteres)]: ') for i in [1, 2]]
    db.addTrade(Trade((float(data[0][:-3]), data[0][-3:]), (float(data[1][:-3]), data[1][-3:])))


if __name__ == '__main__':
    db = DataManager()
    print(db.tradesOf('btc'))
    

