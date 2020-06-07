from sys import argv, exit
import matplotlib.pyplot as plt
import matplotlib
import threading

from records.DBManager import DataManager, Trade
from web.collector import Thunder, CM2CU
from visualizer.visualizer import Freeze, createFigure

matplotlib.use('tkAgg')

"""
Entry commands to sys.argv
snap --[window]: Muestra una ventana de un tiempo determinado
shell: Initialize a shell 

Options:
--test: Bool => Database en true o en false
"""
# TODO: Configuración de shell con sys.argv
# TODO: Traceback de inversion
# TODO: Antes probar con un script aparte e importarlo como con temp. El tracker en tiempo real parece que tendrá que ser una gui

# Declaring globals
db = DataManager()
thunder = Thunder(test=True)


# De produccion
# db = DataManager()
# coins = db.retrieveCoins()
# thunder = Thunder()


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
    f = Freeze(ax, thunder, 'BTC-USD', timespan=window) if window else Freeze(ax, thunder, 'BTC-USD', timespan='5h')
    f.plotCoin()
    f.plotValuation(CM2CU(db.retrieveValuation('btc')))
    
    # Complete
    # fig, axes = createFigure(rows=3, cols=1)
    # freeze_axes = [Freeze(ax, thunder, coin, timespan=window) if window else Freeze(ax, thunder, coin) for (ax, coin) in set(zip(axes, coins))]
    # [f.plotCoin() for f in freeze_axes]
    
    fig.tight_layout()
    plt.show()


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
    
    db.updateValuation()
    
    # For now, this is the operation
    db.close()