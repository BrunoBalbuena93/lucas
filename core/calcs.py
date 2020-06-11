from pandas import DataFrame, Series

'''
Fire is the instance which has all the data
Here we make all the approaches and ML necessary 
I first thought to merge this one with Thunder, but since the processes are different
it may be good praxis to separate them (even thought they share the same data)
Afterwards, treat Thunder as a service and migrate everything of data to Fire

'''

class Fire():
    def __init__(self, coin:str, df: DataFrame= DataFrame(),test: bool=False):
        super(Fire, self).__init__()
        # Datos con los que se trabajara
        self.setDf(df)

    # Observing the changes in the line
    def findTendency(self):
        # Tendency line
        tendency = self.df.apply(lambda x: x[['close', 'open']].mean(), axis=1)
        # close - open
        change = self.df['close'] - self.df['open']
        


    # Setting up the df
    def setDf(self, df: DataFrame):
        self.df = df
       
    # Retrieving data 
    def getData(self, t: int=0):
        return self.df[self.df.index > t]