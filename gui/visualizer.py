import matplotlib.pyplot as plt
import matplotlib.animation as animation
from json import load
import datetime as dt

"""
Visualizador dinámico de los plots
Técnicamente no se pretende hacer una GUI, por lo que se dejaran en ventanas de monedas
dentro del objeto Freeze
Usa los parámetros de settings 
"""
with open('settings.json', 'r') as f:
    data = load(f)
colors = data['freeze']['colors']

class Freeze():
    def __init__(self, ax: plt.axes, coin: str, fire=None, timespan: str='default', isGui:bool = False):
        '''
        Al definir el objeto se le envía el axis, es más sencillo que definir un 
        grid determinado
        :param axis: Axis the la figure donde se ploteará
        :param fire: De donde se saca la información
        '''
        self.ax: plt.axes = ax
        self.fire = fire
        self.coin = coin
        self.isGui= isGui
        
        self.strWin = timespan if 'default' not in timespan else data['freeze']['window']
        self.color = colors
        # Cuanto tiempo va a mostrar el plot?
        self.configureWindow()
        if not isGui:
            self.prepPlot()


    def configureWindow(self):
        if 'd' in self.strWin:
            # Son dias
            self.window = (dt.datetime.now() - dt.timedelta(days=int(self.strWin[:-1]))).timestamp()
        elif 'h' in self.strWin:
            # Son horas
            self.window = (dt.datetime.now() - dt.timedelta(hours=int(self.strWin[:-1]))).timestamp()
        elif 'm' in self.strWin:
            # Son minutos
            self.window = (dt.datetime.now() - dt.timedelta(minutes=int(self.strWin[:-1]))).timestamp()
        else:
            return
   
            
    def prepPlot(self):
        self.ax.cla()
        # Setting title
        self.ax.set_title('Coin: {}  {} - {}'.format(self.coin[:3].lower(), dt.datetime.fromtimestamp(self.window).strftime('%Y-%m-%d %H:%M')[2:], dt.datetime.now().strftime('%Y-%m-%d %H:%M')[2:]))
        self.ax.set_xlim([self.window, int(dt.datetime.now().timestamp())])
        self.ax.set_facecolor(self.color['background'])
        self.ax.grid()
        

    def plotCoin(self):
        df = self.fire.getData(int(self.window))
        self.prepPlot()
        self.plotData(df)

    def plot2Gui(self, df):
        # Dado que las velas no se ven tanto, opinaria por hacer una curva de tendencia con sombeado, igual es más rapida
        self.ax.set_title('Coin: {}  {} - {}'.format(self.coin, dt.datetime.fromtimestamp(df.index[0]).strftime('%Y-%m-%d %H:%M')[2:], dt.datetime.fromtimestamp(df.index[-1]).strftime('%Y-%m-%d %H:%M')[2:]))
        self.ax.set_facecolor(self.color['background'])
        self.ax2 = self.ax.twinx()
        self.ax2.grid(b=True, which='major', color=self.color['high'], linestyle='-')
        self.ax.plot(df.index, df['volume'], color=self.color['volume'], alpha=0.85)
        self.ax.fill_between(df.index, df['volume'], color=self.color['volume'], alpha=0.3)
        self.ax.set_ylim([0, 12 * max(df['volume']) / 3])
        tendency = df.apply(lambda x: x[['close', 'open']].mean(), axis=1)
        self.ax2.plot(df.index, tendency, color=self.color['tendency'])
        self.ax2.fill_between(df.index, df['close'], df['open'], color=self.color['high'], alpha=0.3)
        low_lim = df[['open', 'close', 'high', 'low']].min().min()
        high_lim = df[['open', 'close', 'high', 'low']].max().max()
        rango = high_lim - low_lim
        self.ax2.set_ylim([low_lim - 0.33 * rango, high_lim + 0.02*rango])
        [spine.set_visible(False) for spine in self.ax2.spines.values()]
        [spine.set_visible(False) for spine in self.ax.spines.values()]
        self.ax.get_xaxis().set_visible(False)
        self.ax2.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)
        # self.ax2.get_yaxis().set_visible(False)
        
    
    def plotData(self, df):
        '''
        :params df: El dataframe debe tener high, open, low, close y volume en sus columnas
        '''
        # Duplicando el axes
        self.ax2 = self.ax.twinx()
        # Configurando limites
        self.ax.plot(df.index, df['volume'], color=self.color['volume'], alpha=0.85)
        self.ax.fill_between(df.index, df['volume'], color=self.color['volume'], alpha=0.3)
        self.ax.set_ylim([0, 12 * max(df['volume']) / 3])
        for k in range(len(df)):
            # Se itera porque pues soy wey y no se me ocurrio algo mejor
            entry = df.iloc[k]
            # Definiendo los colores
            color = self.color['low'] if entry['open'] > entry['close'] else self.color['high']
            # Primero las barras de open y close
            self.ax2.plot([entry.name] * 2, [entry.open, entry.close], color = color, linewidth=3)
            # Luego las lineas de high and low
            self.ax2.plot([entry.name] * 2, [entry.high, entry.low], color = color, linewidth=1)
        # Limites
        self.ax2.plot(df.index, df.apply(lambda x: x[['close', 'open']].mean(), axis=1), color=self.color['tendency'], alpha=0.3)
        low_lim = df[['open', 'close', 'high', 'low']].min().min()
        high_lim = df[['open', 'close', 'high', 'low']].max().max()
        rango = high_lim - low_lim
        self.ax2.set_ylim([low_lim - 0.33 * rango, high_lim + 0.02*rango])
        [spine.set_visible(False) for spine in self.ax2.spines.values()]
        [spine.set_visible(False) for spine in self.ax.spines.values()]
        self.ax2.set_xticks([])
        self.ax.set_xticks([])
            
    
    def plotValuation(self, val):
        X = self.ax.get_xlim()
        self.ax2.hlines(val, xmin=X[0], xmax=X[1], color=colors['tendency'], linestyle='dashed')
        self.ax.set_title(self.ax.get_title() + '|  Val: {:.2f}'.format(val))

    def update(self):
        df = self.fire.getData(int(self.window))
        self.prepPlot()
        self.plotData(df)

    def __str__(self):
        return 'Coin: {}  {} - {}'.format(self.coin, dt.datetime.fromtimestamp(self.window).strftime('%Y-%m-%d %H:%M')[2:], dt.datetime.now().strftime('%Y-%m-%d %H:%M')[2:])
    
    @staticmethod
    def getFigureColor():
        return colors['figure-background']

        
def createFigure(rows: int=1, cols: int=1):
    fig, axes = plt.subplots(rows, cols)
    fig.set_facecolor(colors['figure-background'])
    return fig, axes