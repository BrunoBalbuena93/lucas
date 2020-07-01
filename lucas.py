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

# TODO: Implementar metodo para obtener la cantidad invertida al momento en una moneda (DBManager)
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
# TODO: Configuración de shell con sys.argv
# TODO: Traceback de inversion
# TODO: Antes probar con un script aparte e importarlo como con temp. El tracker en tiempo real parece que tendrá que ser una gui

# Declaring globals
with open('settings.json', 'r') as f:
    settings = load(f)
db = DataManager()
thunder = Thunder()
# fire = Fire('btc', thunder.getWindow('btc'))

# De produccion
# db = DataManager()
# coins = db.retrieveCoins()
# thunder = Thunder()
# fires = [Fire(coin, thunder.getWindow((coin))) for coin in coins]


def newShell():
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

def snapshot(window):
    print('{} window configured'.format(window)) if window else print('Default window configured')
    # Testing
    fig, ax = createFigure()
    fire = Fire('btc', thunder.getWindow('btc'))
    f = Freeze(ax, 'BTC-USD', fire, timespan=window) if window else Freeze(ax, 'BTC-USD', fire, timespan='5h')
    f.plotCoin()
    f.plotValuation(db.retrieveValuation('btc'))

    # Complete
    # fig, axes = createFigure(rows=3, cols=1)
    # fires = [Fire(coin, thunder.getWindow((coin))) for coin in coins]
    # freeze_axes = [Freeze(ax, coin, fire, timespan=window) if window else Freeze(ax, coin, fire) for (ax, fire, coin) in set(zip(axes, fires, coins))]
    # [f.plotCoin() for f in freeze_axes]
    # [f.plotValuation(db.retrieveValuation(coin)) for (f, coin) in set(zip(freeze_axes, coins))]

    fig.tight_layout()
    plt.show()
   
def createAlert(options):
    Alert(options, db)

def initGui():
    startGUI(db, thunder)

def help():
    
    print('''Lucas es el asistente para control de gastos en criptomonedas\n
    snap --[window]: Muestra una ventana de un tiempo determinado\n
    trade [cantidad][moneda] [cantidad][moneda]: Agrega un trade a base de instrucciones\n
    funds --[fondos]: Agregar fondos\n
    value [coin] --current?True: Valuación actual de moneda con saldo en cartera. Current => Comparativa con el valor actual\n
    inv --g: Cantidad invertidad al momento. g => Separa cantidad de SPEI y cantidad de ganancia\n
    alert --custom(opcional): Crea funcion iterante de alerta. En caso de custom, utiliza alert_settings.json\n
    shell: Inicia una shell con Data Manager y Thunder inicializados
    ''')

def HandleCommands(commands):
    '''
    In order to keep the main clean, I'm migrating all the handling here
    '''
    # First, attend the options
    options = [entry.replace('-', '') for entry in commands if '-' in entry]
    [commands.remove('--' + entry) for entry in options]
    
    if 'h' in options or 'help' in options:
        help()
        return

    if 'snap' in commands:
        # Check if time declared
        win = options[0] if len(options) > 0 else False
        snapshot(win)
    
    if 'trade' in commands:
        commands.remove('trade')
        print('Has seleccionado agregar un nuevo trade')
        if len(commands) == 0:
            commands = [input('Ingresa el inicial: [cantidad][moneda(3caracteres)]: ') for i in [1, 2]]
        db.addTrade(db.Trade((float(commands[0][:-3]), commands[0][-3:]), (float(commands[1][:-3]), commands[1][-3:])))
    
    if 'funds' in commands:
        if len(options) == 0:
            options = [input('¿De cuanto fue el deposito?  ')]
        db.addFund(float(options[0]))

    if 'alert' in commands:
        createAlert(options)
            
    if 'value' in commands:
        commands.remove('value')
        current = False
        if len(commands) < 1:
            commands = [input('De que moneda? ')]
        if 't' in options:
            current = True
        data = db.reportCoin(commands[0], current)
        print('coin: {}\nValor invertido: {:.3f} @ {:.3f} {}/usd'.format(data['coin'], data['mxnvalue'], data['valuation'], data['coin']))
        if current:
            print('Valor actual: {:.3f} @ {:.3f} {}/usd'.format(data['currentvalue'], data['currentvaluation'], data['coin']))
    
    if 'invested' in commands or 'inv' in commands:
        separate = True if 'g' in options else False
        data = db.reportMXN(separate)
        print('Ingresado por SPEI: {:.2f}\nInversiones: {:.2f}\nGanancias: {:.2f}'.format(data['spei'], data['invested'], data['gains']))

    if 'gui' in commands:
        initGui()

    if 'shell' in commands:
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
