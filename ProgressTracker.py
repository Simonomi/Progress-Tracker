# Simonomi's Progress Tracker v2.0
# Thank you to https://www.tvmaze.com/api

from tkinter import *
from tkinter import ttk, font, messagebox
from pathlib import Path
import zipfile, os, urllib.request, threading


# Edit this variable to change where Progress.zip is stored
dataPath = str(Path.home()) + "\\Dropbox\\Personal\\"
tempPath = str(Path.home()) + "\\AppData\\Roaming\\ProgressTracker\\"

data = {}
root = Tk()

showImageDownloadProgress = True
darkMode = True



# Basic functions def ________________BASIC FUNCTIONS:
def getSourceCode(url):
	try:
		import requests
		r = requests.get(url)
		page_source = r.text
		return page_source
	except (urllib.error.URLError, requests.exceptions.SSLError):
		print("Error: no internet or invalid URL: " + url)


def hasPassed(date):
	import datetime
	return (datetime.datetime.now() - datetime.datetime(int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2]))).days >= 0



# Unique functions def ______________UNIQUE FUNCTIONS:
def loadDataFromFile(filePath):
	global data
	with zipfile.ZipFile(filePath, "r") as zip:
		for name in zip.namelist():
			fileName = ".".join(name.split(".")[:-1])
			data[fileName] = zip.read(name).decode("utf-8").replace("\r", "").split("\n")
			data[fileName][1] = [int(x) for x in data[fileName][1].split("|")]
			data[fileName][4] = int(data[fileName][4])
			data[fileName][7] = data[fileName][7] == "True"
			data[fileName][9] = int(data[fileName][9])
	sortData()


def downloadImage(imageUrl, imageDestination):
	import urllib.request

	try:
		urllib.request.urlretrieve(imageUrl, imageDestination)
	except:
		print("Error: no internet or invalid URL: " + imageUrl)

	if showImageDownloadProgress:
		global downloadThreadCount
		if downloadProgress.value == downloadProgress.max_value - 1:
			downloadProgress.finish()
		else:
			downloadProgress.update(downloadProgress.value + 1)


def downloadImages():
	if not os.path.exists(tempPath):
		os.mkdir(tempPath)

	if showImageDownloadProgress:
		global downloadProgress
		import progressbar.bar
		downloadProgress = progressbar.bar.ProgressBar(0, len(data.keys()))
		downloadProgress.update(0)

	for i in list(data.keys()):
		imageUrl = data[i][0]
		imageFile = tempPath + i + ".jpg"
		if (not os.path.exists(imageFile)) or os.path.getsize(imageFile) == 0:
			threading.Thread(target=lambda: downloadImage(imageUrl, imageFile), daemon=True).start()
		elif showImageDownloadProgress:
			downloadProgress.update(downloadProgress.value + 1)

	if showImageDownloadProgress:
		if downloadProgress.value == downloadProgress.max_value:
			downloadProgress.finish()


def updateShow(show):
	showName = show[0]
	show = show[1]

	if show[9]:
		if show[2] != "Ended":
			import time
			time.sleep(3)
		
		showData = getSourceCode("http://api.tvmaze.com/shows/{0}?embed=seasons".format(show[8]))
		import json

		try:
			showDataDict = json.loads(showData)
		except json.decoder.JSONDecodeError:
			print("ERROR: Invalid show: " + show)
			return

		if showDataDict["status"] != show[2]:
			show[2] = showDataDict["status"]
		
		try:
			uninportanttemp = showDataDict["_embedded"]["seasons"]
		except:
			print("ERROR AT {0}".format(show))
			return
		
		seasons = []
		for i in showDataDict["_embedded"]["seasons"]:
			if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
				if hasPassed(i["endDate"]):
					seasons.append(i["episodeOrder"])
				else:
					seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/" + str(i["id"]) + "/episodes")
					seasonEpisodesDict = json.loads(seasonEpisodes)
					for j in seasonEpisodesDict:
						if not hasPassed(j["airdate"]) and j["number"] != None:
							seasons.append(int(j["number"]) - 1)
							break


		if None in seasons:
			episodeList = getSourceCode("https://api.tvmaze.com/shows/" + str(show[8]) + "/episodes")
			episodeListDict = json.loads(episodeList)
			
			episodes = []
			for i in range(0, len(episodeListDict)):
				episodes.append(episodeListDict[i]["season"])

			seasons = [] # A list of how many episodes per season
			for i in range(1, episodes[len(episodes) - 1] + 1):
				seasons.append(episodes.count(i))

		if not seasons == show[1]:
			show[1] = seasons

def updateShows():
	for i in data.items():
		threading.Thread(target=lambda: updateShow(i), daemon=True).start()


def sortData():
	global data, lbox

	tempData = {}
	for i in sorted(data):
		tempData[i] = data[i]
	data = tempData

	watching = {}
	toWatch = {}
	finished = {}
	discontinued = {}

	for show in data.keys():
		if data[show][7]:
			discontinued[show] = data[show]
		elif data[show][4] > sum(data[show][1]):
			finished[show] = data[show]
		elif data[show][4] != 1:
			watching[show] = data[show]
		else:
			toWatch[show] = data[show]

	data = {**watching, **toWatch, **finished, **discontinued}
	showList.set(list(data.keys()))

	finishedStart = len(watching) + len(toWatch)
	finishedEnd = len(watching) + len(toWatch) + len(finished)
	for i in range(0, len(data)):
		if i < len(watching):
			lbox.itemconfigure(i, background=listBoxWatchingColor, foreground=listBoxWatchingTextColor)
		elif i >= finishedStart and i < finishedEnd:
			lbox.itemconfigure(i, background=listBoxWatchedColor, foreground=listBoxWatchedTextColor)
		elif i >= finishedEnd:
			lbox.itemconfigure(i, background=listBoxDiscontinuedColor, foreground=listBoxDiscontinuedTextColor)
		else:
			if i % 2 == 0:
				lbox.itemconfigure(i, background=listBoxColor1, foreground=listBoxTextColor1)
			else:
				lbox.itemconfigure(i, background=listBoxColor2, foreground=listBoxTextColor2)
	try:
		setShow(selectedShow)
	except:
		setShow(0)


def getSeasonEpisode(show):
	episodeData = data[show][1]
	totalProgress = int(data[show][4])
	seasonNumber = 1
	for i in [int(x) for x in episodeData]:
		totalProgress -= i
		seasonNumber += 1
		if totalProgress <= 0:
			totalProgress += i
			seasonNumber -= 1
			return [seasonNumber, totalProgress, len(episodeData), int(episodeData[seasonNumber - 1])]
			break
	return [seasonNumber, totalProgress, len(episodeData), 0]


def setShow(show=""):
	global data, selectedShow, selectedShowNum, pic, image, status

	if type(show) == Event or show == "":
		show = list(data.keys())[lbox.curselection()[0]]
	elif type(show) == int:
		show = list(data.keys())[show]

	selectedShow = show
	selectedShowNum = list(data.keys()).index(show)
	lbox.selection_clear(0, END)
	lbox.selection_set(selectedShowNum)
	lbox.see(selectedShowNum)

	showTitle.set(selectedShow)

	from PIL import Image, ImageTk
	try:
		image = ImageTk.PhotoImage(Image.open(tempPath + show + ".jpg").resize((210, 295)))
	except:
		if not os.path.exists(tempPath):
			os.mkdir(tempPath)
		try:
			urllib.request.urlretrieve(data[show][0], tempPath + show + ".jpg")
		except urllib.error.URLError:
			print("Error: no internet or invalid URL: " + data[i][0])
		image = ImageTk.PhotoImage(Image.open(tempPath + show + ".jpg").resize((210, 295)))
	pic["image"] = image

	if data[show][2] == "Ended":
		title.config(fg="#800000")
	elif data[show][2] == "Running":
		title.config(fg="#008000")
	else:
		title.config(fg="#807d00")

	if data[show][7]:
		# Discontinued
		seasonProgress.set("Discontinued")
		season.grid(column=0, row=0, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		settingsButton.grid_forget()
		discontinueButton.grid_forget()
		recontinueButton.grid(column=0, row=7, sticky="new", pady=2)
	elif data[show][4] > sum(data[show][1]):
		# Finished
		seasonProgress.set("Finished")
		season.grid(column=0, row=0, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		settingsButton.grid(column=0, row=5, sticky="new", pady=2)
		discontinueButton.grid_forget()
		recontinueButton.grid_forget()
	else:
		# Watching or to watch
		seas, epi, seasMax, epiMax = getSeasonEpisode(show)
		episodeProgress.set("Episode " + str(epi) + "/" + str(epiMax))
		timeProgress.set(data[show][5])

		if seasMax == 1:
			season.grid_forget()
		else:
			seasonProgress.set("Season " + str(seas) + "/" + str(seasMax))
			season.grid(column=0, row=0, sticky="nw", pady=2)
		episode.grid(column=0, row=1, sticky="nw", pady=2)
		timeFrame.grid(column=0, row=2, sticky="nw", pady=2)
		linkButton.grid(column=0, row=3, sticky="new", pady=2)
		if data[show][3] == "" or (("netflix" in data[show][3]) and (not "|" in data[show][3])):
			linkButton['state'] = DISABLED
		else:
			linkButton['state'] = NORMAL
		completeButton.grid(column=0, row=4, sticky="new", pady=2)
		settingsButton.grid(column=0, row=5, sticky="new", pady=2)
		discontinueButton.grid(column=0, row=7, sticky="new", pady=2)
		recontinueButton.grid_forget()


def getLinks(show, season=""):
	netflixLink = ""

	try:
		netflixSearch = getSourceCode("https://www.google.com/search?q=site%3Anetflix.com+" + show)
		netflixLink = "https://www.netflix.com/title/" + netflixSearch.split("https://www.netflix.com/title/")[1].split("&")[0]
		linkData = getSourceCode(netflixLink)
		if linkData.split("<title>")[1].split(" |")[0].lower() != show.lower():
			netflixLink = ""
	except IndexError:
		netflixLink = ""

	out = [i for i in [netflixLink] if i != ""]
	if inSettings and selectedShow == show:
		links = "|".join(out)
		linkSettings.set(links)
		resetLinkProgress.grid_forget()
		resetLinkButton.grid(column=0, row=0, sticky="nsew")
	if show in resetLinkThreadShows:
		data[show][3] = "|".join(out)
		resetLinkThreadShows.remove(show)
	return "|".join(out)


def newShow(show):
	showData = getSourceCode("https://api.tvmaze.com/singlesearch/shows?q=" + show + "&embed=seasons")
	import json

	try:
		showDataDict = json.loads(showData)
	except json.decoder.JSONDecodeError:
		print("ERROR: Invalid show: " + show)
		return

	seasons = []
	for i in showDataDict["_embedded"]["seasons"]:
		if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
			if hasPassed(i["endDate"]):
				seasons.append(i["episodeOrder"])
			else:
				seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/" + str(i["id"]) + "/episodes")
				seasonEpisodesDict = json.loads(seasonEpisodes)
				for j in seasonEpisodesDict:
					if not hasPassed(j["airdate"]):
						seasons.append(int(j["number"]) - 1)
						break


	if None in seasons:
		episodeList = getSourceCode("https://api.tvmaze.com/shows/" + str(showDataDict["id"]) + "/episodes")
		episodeListDict = json.loads(episodeList)

		episodes = []
		for i in range(0, len(episodeListDict)):
			episodes.append(episodeListDict[i]["season"])

		seasons = [] # A list of how many episodes per season
		for i in range(1, episodes[len(episodes) - 1] + 1):
			seasons.append(episodes.count(i))


	showName = showDataDict["name"].replace("/", "").replace("\\", "").replace(":", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "").encode("cp1252", "ignore").decode('cp1252')

	out = [str(showDataDict["image"]["medium"])] # Image link (0)
	out.append(seasons) # Episode data (1)
	out.append(str(showDataDict["status"])) # Status (2)
	out.append(getLinks(showName)) # Show links (3)
	out.append(1) # Total progress (4)
	out.append("") # Time progress (5)
	out.append(showName) # Original name (6)
	out.append(False) # Discontinued (7)
	out.append(str(showDataDict["id"])) # Tvmaze id (8)
	out.append(1) # Auto mode (9)

	originalNames = []
	for i in list(data.values()):
		originalNames.append(i[6])

	if showName in originalNames:
		overwriteShow = messagebox.askyesnocancel("Overwrite show", "{0} already exists, would you like to overwrite it?".format(showName))
		if overwriteShow:
			showIndexes = []
			showIndexes.append(list(data.keys())[originalNames.index(showName)])
			while True:
				try:
					showIndexes.append(list(data.keys())[originalNames.index(showName, list(data.keys()).index(showIndexes[-1]) + 1)])
				except ValueError:
					break
			for i in showIndexes:
				data.pop(i)
			data[showName] = out
			sortData()
			setShow(showName)
		elif overwriteShow == False:
			while showName in list(data.keys()):
				showName += "_"
			data[showName] = out
			sortData()
			setShow(showName)
	else:
		data[showName] = out
		sortData()
		setShow(showName)

	newProgress.grid_forget()
	newButton.grid(column=0, row=2, columnspan=2, sticky="sew", pady=3, padx=3)
	settingsButton['state'] = NORMAL


def writeToFile(filePath):
	with zipfile.ZipFile(filePath, "w") as zip:
		for i in data.items():
			i[1][1] = "|".join([str(x) for x in i[1][1]])
			i[1][4] = str(i[1][4])
			i[1][7] = str(i[1][7])
			i[1][9] = str(i[1][9])
			zip.writestr(i[0] + ".data", "\n".join(i[1]))



# Main window commands def ____MAIN WINDOW COMMANDS:
def disableHorizontalScroll(x):
	timeData.focus_set()
	root.after(1, lambda: lbox.xview(0))


def changeTime(event):
	data[selectedShow][5] = timeProgress.get()


def openLink(link=""):
	if link == "":
		link = data[selectedShow][3]
	if "|" in link:
		openLink([i for i in link.split("|") if not "netflix" in i][0])
	else:
		import webbrowser
		webbrowser.open(link)


def completeEpisode():
	oldseas = getSeasonEpisode(selectedShow)[0]

	data[selectedShow][4] = int(data[selectedShow][4]) + 1
	setShow()

	if data[selectedShow][4] == 2 or getSeasonEpisode(selectedShow) == None:
		sortData()


def deleteShow():
	confirmDelete = messagebox.askokcancel("Confirm deletion", "Are you sure you want to delete " + selectedShow + "?")
	if confirmDelete:
	   del data[selectedShow]
	   oldNum = selectedShowNum
	   sortData()
	   setShow(oldNum)


def discontinueShow():
	data[selectedShow][7] = True
	sortData()
	setShow()


def recontinueShow():
	data[selectedShow][7] = False
	sortData()
	setShow()


def openSettings():
	global auto, episodeListEntry, settingsWindow, episodeListSettings, totalProgressSettings, linkSettings, oldseas, showTitleSettings, inSettings, resetLinkButton, resetLinkProgress
	oldseas = getSeasonEpisode(selectedShow)[0]

	try:
		settingsWindow.destroy()
	except:
		pass

	inSettings = True
	settingsWindow = Toplevel(bg=backgroundColor)
	settingsWindow.title(selectedShow + " Settings")
	settingsWindow.resizable(False, False)
	settingsWindow.focus_set()

	settingsWindow.bind("<Control-w>", lambda x: root.destroy())
	settingsWindow.bind("<Return>", submitSettings)
	settingsWindow.bind("<Escape>", submitSettings)
	root.bind("<FocusIn>", submitSettings)

	totalProgressSettings = StringVar()
	episodeListSettings = StringVar()
	showTitleSettings = StringVar()
	linkSettings = StringVar()
	auto = IntVar()

	totalProgressSettings.set(data[selectedShow][4])
	episodeListSettings.set("|".join([str(x) for x in data[selectedShow][1]]))
	showTitleSettings.set(selectedShow)
	linkSettings.set(data[selectedShow][3])
	auto.set(data[selectedShow][9])


	titleLabel = Label(settingsWindow, text="Title:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
	titleLabel.grid(column=0, row=0, sticky="w", padx=5, pady=1)

	titleEntry = Entry(settingsWindow, textvariable=showTitleSettings, width=23, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
	titleEntry.grid(column=1, row=0, sticky="ew", pady=1, padx=5)

	linkLabel = Label(settingsWindow, text="Link:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
	linkLabel.grid(column=0, row=1, sticky="w", padx=5, pady=1)

	linkEntry = Entry(settingsWindow, textvariable=linkSettings, width=23, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
	linkEntry.grid(column=1, row=1, sticky="ew", pady=1, padx=5)

	episodeLabel = Label(settingsWindow, text="Episode:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
	episodeLabel.grid(column=0, row=2, sticky="w", padx=5, pady=1)

	episodeEntry = Entry(settingsWindow, textvariable=totalProgressSettings, width=23, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
	episodeEntry.grid(column=1, row=2, sticky="ew", pady=1, padx=5)

	episodeListFrame = Frame(settingsWindow, bg=backgroundColor)
	episodeListFrame.grid(column=0, row=3, sticky="nsew", columnspan=2, pady=1)

	episodeListLabel = Label(episodeListFrame, text="Episode list:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
	episodeListLabel.grid(column=0, row=0, sticky="w", padx=5)

	episodeListEntry = Entry(episodeListFrame, textvariable=episodeListSettings, width=17, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor, disabledbackground=backgroundColor)
	episodeListEntry.grid(column=1, row=0, sticky="ew")

	autoCheckbox = Checkbutton(episodeListFrame, text="Auto", variable=auto, command=autoMode, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor, selectcolor=backgroundColor)
	autoCheckbox.grid(column=2, row=0, sticky="ew")

	buttonsFrame = Frame(settingsWindow, bg=backgroundColor)
	buttonsFrame.grid(column=0, row=4, sticky="nsew", columnspan=2, padx=5, pady=1)

	resetLinkButton = Button(buttonsFrame, text="Reset link", command=resetLink, width=27, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
	resetLinkButton.grid(column=0, row=0, sticky="nsew")

	resetLinkProgress = ttk.Progressbar(buttonsFrame, orient=HORIZONTAL, length=172, mode="indeterminate")
	try:
		if resetLinkThread.is_alive() and selectedShow in resetLinkThreadShows:
			resetLinkProgress.grid(column=0, row=0, sticky="nsew")
			resetLinkProgress.start()
			resetLinkButton.grid_forget()
	except:
		pass

	resetTitleButton = Button(buttonsFrame, text="Reset title", command=resetTitle, width=27, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
	resetTitleButton.grid(column=1, row=0, sticky="nsew")

	autoMode()



# Settings commands def ___________SETTINGS COMMANDS:
def autoMode():
	global auto, episodeListEntry
	if auto.get() == 1:
		episodeListEntry.config(state='disabled')
		if data[selectedShow][9] != 1:
			import json
			data[selectedShow][9] = 1

			showData = getSourceCode("https://api.tvmaze.com/shows/" + data[selectedShow][8] + "/seasons")
			try:
				showDataDict = json.loads(showData)
			except json.decoder.JSONDecodeError:
				print("ERROR: Invalid show: ")

			seasons = []
			for i in showDataDict:
				if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
					if hasPassed(i["endDate"]):
						seasons.append(i["episodeOrder"])
					else:
						seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/" + str(i["id"]) + "/episodes")
						seasonEpisodesDict = json.loads(seasonEpisodes)
						for j in seasonEpisodesDict:
							if not hasPassed(j["airdate"]):
								seasons.append(int(j["number"]) - 1)
								break

			if None in seasons:
				episodeList = getSourceCode("https://api.tvmaze.com/shows/" + str(data[selectedShow][8]) + "/episodes")
				episodeListDict = json.loads(episodeList)

				episodes = []
				for i in range(0, len(episodeListDict)):
					episodes.append(episodeListDict[i]["season"])

				seasons = [] # A list of how many episodes per season
				for i in range(1, episodes[len(episodes) - 1] + 1):
					seasons.append(episodes.count(i))

			episodeListSettings.set("|".join([str(x) for x in seasons]))
	else:
		episodeListEntry.config(state='normal')
		data[selectedShow][9] = 0


def resetLink():
	global resetLinkThread, resetLinkThreadShows
	resetLinkThread = threading.Thread(target=lambda: getLinks(data[selectedShow][6]), daemon=True)
	resetLinkThread.start()
	resetLinkThreadShows.append(selectedShow)

	resetLinkButton.grid_forget()
	resetLinkProgress.grid(column=0, row=0, sticky="nsew")
	resetLinkProgress.start()


def resetTitle():
	showTitleSettings.set(data[selectedShow][6])


def submitSettings(x):
	global settingsWindow, oldseas, selectedShow, inSettings
	
	root.unbind("<FocusIn>")
	inSettings = False
	settingsWindow.destroy()

	if showTitleSettings.get() != selectedShow:
		newTitle = showTitleSettings.get()
		while newTitle.lower() in [x.lower() for x in list(data.keys())]:
			newTitle += "_"
		data[newTitle] = data.pop(selectedShow)
		try:
			if selectedShow in resetLinkThreadShows:
				resetLinkThreadShows.remove(selectedShow)
		except:
			pass
		try:
			os.rename(tempPath + selectedShow + ".jpg", tempPath + newTitle + ".jpg")
		except FileExistsError:
			os.remove(tempPath + newTitle + ".jpg")
			os.rename(tempPath + selectedShow + ".jpg", tempPath + newTitle + ".jpg")
		sortData()
		selectedShow = newTitle

	if linkSettings.get() != data[selectedShow][3]:
		data[selectedShow][3] = linkSettings.get()

	if totalProgressSettings.get() != data[selectedShow][4]:
		try:
			data[selectedShow][4] = int(totalProgressSettings.get())
		except:
			data[selectedShow][4] = 1

	if episodeListSettings.get() != data[selectedShow][1]:
		try:
			data[selectedShow][1] = [int(i) for i in episodeListSettings.get().split("|")]
		except ValueError:
			pass

	setShow(selectedShow)



# New show commands def ________NEW SHOW COMMANDS:
def addShow():
	newShowName.set("")
	newEntry.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=6, padx=3)
	newButton.grid_forget()
	newEntry.focus_set()
	root.bind("<Button-1>", click)


def newEntrySelect(x):
	global newEntrySelected
	newEntrySelected = x


def click(x):
	if not newEntrySelected:
		closeNewEntry()


def closeNewEntry(x=""):
	global newShowName
	newButton.grid(column=0, row=2, columnspan=2, sticky="sew", pady=3, padx=3)
	newEntry.grid_forget()
	root.focus_set()
	root.unbind("<Button-1>")


def submitNewEntry(x):
	settingsButton['state'] = DISABLED
	for i in newShowName.get().split("|"):
		threading.Thread(target=lambda: newShow(i), daemon=True).start()
	newEntry.grid_forget()
	newProgress.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3)
	newProgress.start()
	root.focus_set()
	root.unbind("<Button-1>")



# Menu bar def ________________________MENU BAR:
def refreshImageCache():
	import shutil
	shutil.rmtree(tempPath[0:-1])
	print()
	threading.Thread(target=downloadImages, daemon=True).start()

def preferences():
	print("Preferences")



menuBar = Menu(root)

fileMenu = Menu(menuBar, tearoff=0)
fileMenu.add_command(label="Refresh Image Cache", command=refreshImageCache, accelerator="Ctrl+R")

fileMenu.add_separator()
# fileMenu.add_command(label="Import", command=importData, accelerator="Ctrl+I")
fileMenu.add_command(label="Import")
# fileMenu.add_command(label="Export", command=exportData, accelerator="Ctrl+E")
fileMenu.add_command(label="Export")
fileMenu.add_separator()

fileMenu.add_command(label="Preferences", command=preferences, accelerator="Ctrl+P")
fileMenu.add_command(label="Quit", command=root.quit, accelerator="Ctrl+W")
menuBar.add_cascade(label="File", menu=fileMenu)

root.config(menu=menuBar)



# Main window GUI def ______________MAIN WINDOW GUI:
if darkMode:
	backgroundColor = "#000000"
	foregroundColor = "#ffffff"
	
	buttonPressedColor = "#000000"
	buttonPressedTextColor = "#ffffff"
	
	listBoxWatchingColor = "#000000"
	listBoxWatchedColor = "#000000"
	listBoxDiscontinuedColor = "#000000"
	
	listBoxWatchingTextColor = "#fffd96"
	listBoxWatchedTextColor = "#c8ffc8"
	listBoxDiscontinuedTextColor = "#ff9696"
	
	listBoxColor1 = "#000000"
	listBoxColor2 = "#000000"
	listBoxTextColor1 = "#ffffff"
	listBoxTextColor2 = "#ccccff"
else:
	backgroundColor = "#f0f0f0"
	foregroundColor = "#000000"
	
	buttonPressedColor = "#f0f0f0"
	buttonPressedTextColor = "#000000"
	
	listBoxWatchingColor = "#fffd96"
	listBoxWatchedColor = "#c8ffc8"
	listBoxDiscontinuedColor = "#ff9696"
	
	listBoxWatchingTextColor = "#000000"
	listBoxWatchedTextColor = "#000000"
	listBoxDiscontinuedTextColor = "#000000"
	
	listBoxColor1 = "#ffffff"
	listBoxColor2 = "#f0f0ff"
	listBoxTextColor1 = "#000000"
	listBoxTextColor2 = "#000000"

root.config(bg=backgroundColor)

showTitle = StringVar()
seasonProgress = StringVar()
episodeProgress = StringVar()
timeProgress = StringVar()
showList = StringVar()
newShowName = StringVar()
resetLinkThreadShows = []
titleFont = font.Font(family='Times New Roman', size=24)
labelFont = font.Font(family='Times New Roman', size=16)
dataFont = font.Font(family='Times New Roman', size=15)


lbox = Listbox(root, listvariable=showList, height=19, exportselection=False, bg=backgroundColor, highlightcolor=backgroundColor, highlightbackground=backgroundColor)
lbox.bind("<<ListboxSelect>>", setShow)
lbox.grid(column=0, row=0, sticky="nsew", rowspan=2)
lbox.focus_set()

title = Label(root, textvariable=showTitle, font=titleFont, bg=backgroundColor)
title.grid(column=2, row=0, sticky="nw", columnspan=3)

pic = Label(root, bg=backgroundColor)
pic.grid(column=2, row=1, sticky="nw", rowspan=2)

dataFrame = Frame(root, bg=backgroundColor, padx=5)
dataFrame.grid(column=3, row=1, sticky="nw")

season = Label(dataFrame, textvariable=seasonProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor)
episode = Label(dataFrame, textvariable=episodeProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor)

timeFrame = Frame(dataFrame, bg=backgroundColor)

timeLabel = Label(timeFrame, text="Time:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
timeLabel.grid(column=0, row=0, sticky="nsw")

timeData = Entry(timeFrame, textvariable=timeProgress, width=5, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
timeData.grid(column=1, row=0, sticky="nsw")
timeData.bind("<KeyRelease>",  changeTime)

linkButton = Button(dataFrame, text="Open link", command=openLink, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
completeButton = Button(dataFrame, text="Complete episode", command=completeEpisode, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

settingsButton = Button(dataFrame, text="Settings", command=openSettings, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
inSettings = False

deleteButton = Button(dataFrame, text="Delete show", command=deleteShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
deleteButton.grid(column=0, row=6, sticky="new", pady=2)

discontinueButton = Button(dataFrame, text="Discontinue", command=discontinueShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
recontinueButton = Button(dataFrame, text="Recontinue", command=recontinueShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

newButton = Button(root, text="Add show", command=addShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
newButton.grid(column=0, row=2, columnspan=2, sticky="sew", pady=3, padx=3)

newEntry = Entry(root, textvariable=newShowName, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
newEntry.grid_forget()
newEntrySelected = False
newEntry.bind("<Enter>", lambda x: newEntrySelect(True))
newEntry.bind("<Leave>", lambda x: newEntrySelect(False))
newEntry.bind("<Return>", submitNewEntry)
newEntry.bind("<Escape>", closeNewEntry)

style = ttk.Style()
style.theme_use("clam")
style.configure("My.Horizontal.TProgressbar", foreground="black", background="black", troughcolor="black")

if darkMode:
	newProgress = ttk.Progressbar(root, orient=HORIZONTAL, length=50, mode="indeterminate", style="My.Horizontal.TProgressbar")
else:
	newProgress = ttk.Progressbar(root, orient=HORIZONTAL, length=50, mode="indeterminate")


root.bind("<Control-w>", lambda x: root.quit())
root.bind("<Up>", lambda x: lbox.focus_set())
root.bind("<Down>", lambda x: lbox.focus_set())
root.title("Progress Tracker")
root.resizable(False, False)
root.grid_columnconfigure(3, weight=1)

lbox.bind("<B1-Leave>", lambda event: "break")
timeData.bind("<Left>", lambda x: lbox.focus_set() if timeData.index(INSERT) == 0 else False)
lbox.bind("<Right>", disableHorizontalScroll)


# Starts application
loadDataFromFile(dataPath + "Progress.zip")
threading.Thread(target=downloadImages, daemon=True).start()
threading.Thread(target=updateShows, daemon=True).start()
root.mainloop()
writeToFile(dataPath + "Progress.zip")


# Data storage format:
# Image link (0)
# Episode data (1)
# Status (2)
# Show links (3)
# Total progress (4)
# Time progress (5)
# Original name (6)
# Discontinued (7)
# Tvmaze id (8)
# Auto mode (9)
