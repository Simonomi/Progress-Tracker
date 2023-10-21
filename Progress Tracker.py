from gui import *
from database import *
from os.path import dirname, realpath

apiKey = "e0ea968db936eab1eaf1a6e436816d04"
dataPath = "{}\\Progress.dat".format(dirname(realpath(__file__)))
sitesFolder = "sites\\"


if __name__ == "__main__":
	database = ProgressDatabase()
	database.load(dataPath)
	MainWindow(database, darkMode=True, apiKey=apiKey, sitesFolder=sitesFolder)
	database.save(dataPath)
