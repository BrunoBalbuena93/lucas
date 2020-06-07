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

        
    # Setting up the df
    def setDf(self, df: DataFrame):
        self.df = df
       
