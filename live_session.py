from records.DBManager import DataManager
from web.collector import Thunder
from visualizer.visualizer import createFigure, Freeze
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.animation as animation
from json import load

matplotlib.use('tkAgg')

def update(curr):
    f.update()

with open('settings.json', 'r') as f:
    data = load(f)
#            min * 60 s/min * 1000 ms/s
interval = data['freeze']['interval'] * 60000
db = DataManager()
thunder = Thunder(test=True)
fig, ax = createFigure()
f = Freeze(ax, thunder, 'BTC-USD', timespan='5h')
f.plotValuation(CM2CU(db.retrieveValuation('btc')))
a = animation.FuncAnimation(fig, update, interval=interval)
plt.show()
