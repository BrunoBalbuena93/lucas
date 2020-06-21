from sys import argv, exit
import matplotlib.pyplot as plt
import matplotlib
import datetime as dt
from json import load
from time import sleep
import pandas as pd
matplotlib.use('tkAgg')

from records.DBManager import DataManager, Trade, NewTrade, getValuation
from core.collector import Thunder
from core.calcs import Fire
from core.alert import Alert
from gui.visualizer import Freeze, createFigure
from gui.gui import startGUI


"""
Entry commands to sys.argv
snap --[window]: Muestra una ventana de un tiempo determinado
trade [cantidad][moneda] [cantidad][moneda]: Agrega un trade a base de instrucciones
alert --custom(opcional): Crea funcion iterante de alerta
shell: Initialize a shell

Options:
--test: Bool => Database en true o en false

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


def goLive():
    import live_session


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


def HandleCommands(commands):
    '''
    In order to keep the main clean, I'm migrating all the handling here
    '''
    # First, attend the options
    options = [entry.replace('-', '') for entry in commands if '-' in entry]
    [commands.remove('--' + entry) for entry in options]
    print(options)
    print(commands)

    if 'live' in commands:
        goLive()
    
    if 'snap' in commands:
        # Check if time declared
        win = options[0] if len(options) > 0 else False
        snapshot(win)
    
    if 'trade' in commands:
        commands.remove('trade')
        NewTrade(db, commands)
    
    if 'funds' in commands:
        if len(options) == 0:
            options = [input('¿De cuanto fue el deposito?  ')]
        db.addFund(float(options[0]))

    if 'alert' in commands:
        createAlert(options)
            
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
        # Commands displayed
        HandleCommands(commands)
    # Probando del 8 - 11 de mayo
    # For now, this is the operation
    db.close()
