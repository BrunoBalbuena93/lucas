from sys import argv, exit
import matplotlib.pyplot as plt
import matplotlib
import datetime as dt
from json import load
from time import sleep
import pandas as pd
matplotlib.use('tkAgg')

from records.DBManager import DataManager
from core.collector import Thunder
from core.calcs import Fire
from core.alert import Alert
from gui.visualizer import Freeze, createFigure
from gui.gui import startGUI

# TODO: Concluir la GUI

"""
Entry commands to sys.argv
snap --[window]: Muestra una ventana de un tiempo determinado
trade [cantidad][moneda] [cantidad][moneda]: Agrega un trade a base de instrucciones
funds --[fondos]: Agregar fondos 
value [coin] --current?True: Valuación actual de moneda con saldo en cartera. Current => Comparativa con el valor actual
inv --g: Cantidad invertidad al momento. g => Separa cantidad de SPEI y cantidad de ganancia
alert --custom(opcional): Crea funcion iterante de alerta
shell: Initialize a shell

Options:
--test: Bool => Database en true o en false

Notas
pyuic5 -x [nombre ui] -o [output.py]
"""
# TODO: Traceback de inversion
# TODO: Antes probar con un script aparte e importarlo como con temp. El tracker en tiempo real parece que tendrá que ser una gui
# TODO: Agregar funcion all a prev

# Declaring globals
with open('settings.json', 'r') as f:
    settings = load(f)
db = DataManager()
thunder = Thunder()


def newShell():
    '''
    Genera una shell para trabajar
    '''
    # TODO: Configurar las flechas de navegacion
    print('Interactive shell activated')
    count = [0, 0]
    while True:
        x = input('In[{}]: '.format(count[0]))
        count[0] += 1
        if 'exit' in x: break
        try:
            y = eval(x)
            if y: print('Out[{}]: {}'.format(count[1], y))
            count[1] += 1
        except:
            try:
                exec(x)
            except Exception as e:
                print('Error: ', e)
    print('See you around!')

def snapshot(coin:str, window):
    '''
    Genera una gráfica de velas de la ventana determinada, en caso de que la ventana no esté especificada, es de 5h
    '''
    print('{} ventana configurada'.format(window)) if window else print('Default window configured')
    fig, ax = createFigure()
    fire = Fire(coin, thunder.getWindow(coin))
    f = Freeze(ax, settings['coin-symbol'][coin], fire, timespan=window) if window else Freeze(ax, settings['coin-symbol'][coin], fire, timespan='5h')
    f.plotCoin()
    f.plotValuation(db.retrieveValuation(coin))
    fig.tight_layout()
    plt.show()
   
def createAlert(options):
    '''
    Crea una alerta con logs
    '''
    try:
        Alert(options, db)
    except KeyboardInterrupt:
        db.close()

def preview(values):
    '''
    Hace un forecast de cuanto estarías generando extra
    '''
    db.gainForecast(*values)
    
def quickValue(params:dict):
    '''
    Aveces hay discrepancias entre tradeview/yahoo finance y mi plataforma, así que esto es para ver la 
    valuacion que me está dando mi plataforma
    '''
    usdval = thunder.getUSDValuation()
    if 'mxn' in params['init'][1]:
        # Caso que mxn sea la inicial
        platformValuation = (params['init'][0] / usdval) / params['final'][0]
        value, percent = db.quickValuation(params['final'][1], params['init'][0] / usdval, platformValuation)
        forecastValuation = 'Esta compra te dejaría una valuación de {:.4f} | {:.4f}%'.format(value, percent)
        coin = 'usd/' + params['final'][1]
    elif 'mxn' in params['final'][1]: 
        # Caso que mxn sea la final, calcular ganancia
        platformValuation = (params['final'][0] / usdval) / params['init'][0]
        gain, percent = db.quickGain(params['init'][1], params['init'][0], platformValuation)
        forecastValuation = 'Esta compra genera una ganacia de {:.2f} | {:.4f}%'.format(gain, percent)
        coin = 'usd/' + params['init'][1]
    else:
        # Caso que sea entre monedas
        raise NotImplementedError('Aun no está implementado esto')
    print('La valuación que te estan dando es {:.3f} {}\n{}'.format(platformValuation, coin, forecastValuation))
    

def getGains(coin:str, options: str):
    '''
    Aquí obtiene las ganancias producidas por los trades.
    coin =>
        None: De todas las monedas
        [coin]: De una moneda en específico
    Options:
        s => Desglozar todas las operaciones de ganancia
        t => Cantidad total al final
        r => Agregar total por moneda
        d:[año-mes]?current => Mes específico
    '''
    separate = any('s' in op for op in options)
    total = any('t' in op for op in options)
    resume = any('r' in op for op in options)
    specDate = any('d' in op for op in options)
    # Primero se obtiene la data por fecha
    try:
        data = db.getCoinGains(coin) if coin else db.getAllGains()
    except:
        print('Aun no has generado ganancias')
        return
    # Despues checamos si se quiere un mes especifico...
    if specDate:
        # Caso especifico
        specDate = [s.replace('d', '') for s in options if 'd' in s][0]
        if len(specDate) == 0:
            specDate = input('Selecciona un mes en formato \'mm-aa\' o \'mm-aaaa\', si quieres el actual, presiona cualquier tecla: ')
        date = Thunder.ConfigureDate(specDate)
        temp = data.loc[date] if date else data.loc[dt.datetime.strptime('{}-{}'.format(dt.date.today().year, dt.date.today().month), '%Y-%m')]
        if separate:
            print('Las ganancias fueron:\n' + '\n'.join(['{}: {:.2f} | {:.4f}%'.format(row['coin'], row['amount'], row['gain']) for _, row in temp.iterrows()]))
        print('Total ganado fue: {:.2f} | {:.4f}%'.format(temp['amount'].sum(), (temp['amount'] * temp['gain']).sum() / temp['amount'].sum()))
        if resume:
            print('Por moneda:\n' + '\n'.join(['{}: {:.2f} | {:.4f} %'.format(coin, temp[temp['coin'] == coin]['amount'].sum(), (temp[temp['coin'] == coin]['amount'] * temp[temp['coin'] == coin]['gain']).sum() / temp[temp['coin'] == coin]['amount'].sum()) for coin in temp['coin'].unique()]))
        return
    
    for month in data.index.unique():
        D = dt.datetime.strftime(month, '%B, %Y')
        if separate:
            print('Las ganancias durante {} fueron:\n'.format(D) + '\n'.join(['{}: {:.2f} | {:.4f}%'.format(row['coin'], row['amount'], row['gain']) for _, row in data.loc[month].iterrows()]))
        print('Total ganado en {} fue: {:.2f} | {:.4f}%'.format(D, data.loc[month]['amount'].sum(), (data.loc[month]['amount'] * data.loc[month]['gain']).sum() / data.loc[month]['amount'].sum()))
    if total:
        if resume:
            print('Por moneda:' + '\n'.join(['{}: {:.2f} | {:.4f} %'.format(coin, data[data['coin'] == coin]['amount'].sum(), (data[data['coin'] == coin]['amount'] * data[data['coin'] == coin]['gain']).sum() / data[data['coin'] == coin]['amount'].sum()) for coin in data['coin'].unique()]))
    print('La ganancia total es de {:.2f} MXN | {:.4f}%'.format(data['amount'].sum(), (data['amount'] * data['gain']).sum() / data['amount'].sum()))
    

def initGui():
    startGUI(db, thunder)

def help():
    
    print('''Lucas es el asistente para control de gastos en criptomonedas\n
    snapshot/snap coin --[window]: Muestra una ventana de un tiempo determinado\n
    trade [cantidad][moneda] [cantidad][moneda]: Agrega un trade a base de instrucciones\n
    funds --[fondos]: Agregar fondos\n
    value [coin] --current?True: Valuación actual de moneda con saldo en cartera. Current => Comparativa con el valor actual\n
    quickvalue [amount][coin] [amount][coin]: Te da una valuacion sobre la moneda, una de ellas debe ser mxn.\n
    inv --[s]: Cantidad invertidad al momento. g => Separa cantidad de SPEI y cantidad de ganancia\n
    alert --custom(opcional): Crea funcion iterante de alerta. En caso de custom, utiliza alert_settings.json\n
    gains [coin] --s: Ganancias totales, si agregas coin te da de esa moneda en específico, s las separa por coin\n
    prev [coin_vendiendo] --all/[amount][coin]: Te dice la ganancia real que obtendrías dado un trade, es decir, vendiendo X cantidad de Y moneda, cuanto ganarías con que porcentaje.\n
    shell: Inicia una shell con Data Manager y Thunder inicializados
    ''')

def HandleCommands(commands):
    '''
    In order to keep the main clean, I'm migrating all the handling here
    '''
    # First, retrieve the raw command
    command = commands.pop(0)
    # First, attend the options
    options = [entry.replace('--', '') for entry in commands if '--' in entry]
    [commands.remove('--' + entry) for entry in options]
    
    if 'h' == command or 'help' in command or 'h' in options or 'help' in options:
        help()
        return

    if 'snap' in command:
        # Getting coin
        coin = commands[0] if len(commands) > 0 else input('Selecciona de que moneda deseas el snapshot: ')
        # Check if time declared
        win = options[0] if len(options) > 0 else False
        snapshot(coin, win)
    
    if 'trade' in command or 't' == command:
        print('Has seleccionado agregar un nuevo trade')
        if len(commands) == 0:
            commands = [input('Ingresa el inicial: [cantidad][moneda(3caracteres)]: ') for i in [1, 2]]
        db.addTrade(db.Trade((float(commands[0][:-3]), commands[0][-3:]), (float(commands[1][:-3]), commands[1][-3:])))
    
    if 'funds' in command or 'f' == command:
        fund = float(commands[0]) if len(commands) > 0 else float(input('¿De cuanto fue el deposito?  '))
        db.addFund(fund)

    if 'alert' in command:
        createAlert(options)
            
    if 'quick' in command or 'qv' == command:
        try:
            data = db.Trade((commands[0][:-3], commands[0][-3:]), (commands[1][:-3], commands[1][-3:]))
        except IndexError:
            temp_1 = input('Dame la cantidad y moneda de origen: ')
            temp_2 = input('Dame la cantidad y moneda de destino: ')
            data = db.Trade((temp_1[:-3], temp_1[-3:]), (temp_2[:-3], temp_2[-3:]))
        quickValue(data)
        
    if 'value' in command or 'v' == command:
        current = True if 't' in options else False
        if len(commands) < 1 or 'all' in commands:
            coins = db.retrieveCoins()
            data_ = list(map(db.reportCoin, coins, [current] * len(coins)))
        else:
            data_ = [db.reportCoin(commands[0], current)]
        for data in data_:
            print('coin: {}\nValor invertido: {:.3f} @ {:.3f} {}/usd'.format(data['coin'], data['mxnvalue'], data['valuation'], data['coin']))
            if current:
                # TODO: Calcular diferencias
                print('Valor actual: {:.3f} @ {:.3f} {}/usd\nDiferencia: {:.2f} mxn  | {:.4f}%'.format(data['currentvalue'], data['currentvaluation'], data['coin'], data['mxnvalue'] * data['currentvaluation'] / data['valuation'], data['currentvaluation'] / data['valuation']))
    
    if 'invested' in command or 'inv' in command:
        # FIXME: Arreglar esto
        separate = True if 'g' in options else False
        data = db.reportMXN(separate)
        print('Ingresado por SPEI: {:.2f}\nInversiones: {:.2f}\nGanancias: {:.2f}'.format(data['spei'], data['invested'], data['gains']))

    if 'prev' in command:
        commands.remove('prev')
        if 'all' in options:
            _, balanceIn, mxnIn, valUSDIn, valMXNIn = db.retrieveBalance(commands[0], many=True)
            data = [balanceIn, commands[0], commands[0]]
        
        elif len(options) > 0:
            data = [float(options[0][:-3]), options[0][-3:], commands[0]]

        else:
            temp = input('Escribe la cantidad a estimar junto con la moneda: ')
            coin = input('Escribe la moneda de origen: ')
            data = [float(temp[:-3]), temp[-3:], coin]        
        preview(data)
    
    if 'gains' in command:
        coin = commands[0] if len(commands) > 0 else None
        getGains(coin, options)

    if 'gui' in command:
        initGui()

    if 'shell' in command:
        newShell()
        db.close()
        exit()


if __name__ == "__main__":
    print('Welcome to Lucas, your new friendly crypto manager!')

    # Parsing the options and commands
    commands = argv[1:]
    if len(commands) > 0:
        HandleCommands(commands)
    db.close()
