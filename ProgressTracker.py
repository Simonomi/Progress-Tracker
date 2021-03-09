# Simonomi's Progress Tracker v3.0
# Thank you to https://www.tvmaze.com/api
from tkinter import *
from tkinter import ttk, font, messagebox
from tkinter.filedialog import askopenfilename
from pathlib import Path
from PIL import Image, ImageTk
from threading import Thread
from glob import glob
from os import path, mkdir
from pickle import load, dump


# Initializing some variables
tempPath = "{}\\AppData\\Roaming\\ProgressTracker\\".format(Path.home())
showVersion = 1.2
data = []
sites = []
pictures = {}
offline = False
addingShows = 0
currentShow = None
smallPictures = {}
currentShowNum = 0
showLinkInfo = False


# Default values
dataPath = "{}\\Desktop\\Progress.dat".format(Path.home())
errorUrl = "https://static.tvmaze.com/images/no-img/no-img-portrait-text.png"
showImageProgress = False
showUpdateProgress = False
browserTimeout = 30
showBrowser = False
darkMode = True
slowMode = True

if not path.exists(tempPath + "settings.conf"):
	with open(tempPath + "settings.conf", "w") as file:
		file.write("")
with open(tempPath + "settings.conf") as file:
	preferences = file.read().split("\n")
	for i in range(0, len(preferences), 2):
		if preferences[i] == "fileLocation":
			dataPath = preferences[i + 1].format(Path.home())
		if preferences[i] == "errorUrl":
			errorUrl = preferences[i + 1]
		if preferences[i] == "showImageProgress":
			showImageProgress = preferences[i + 1] == "True"
		if preferences[i] == "showUpdateProgress":
			showUpdateProgress = preferences[i + 1] == "True"
		if preferences[i] == "browserTimeout":
			browserTimeout = int(preferences[i + 1])
		if preferences[i] == "showBrowser":
			showBrowser = preferences[i + 1] == "True"
		if preferences[i] == "darkMode":
			darkMode = preferences[i + 1] == "True"
		if preferences[i] == "slowMode":
			slowMode = preferences[i + 1] == "True"



class Show:
	def __init__(self, info):
		if type(info) == dict:
			self.id = info["id"]
			self.title = info["title"]
			self.episodeData = info["episodeData"]
			self.status = info["status"]
			
			if "imageLink" in list(info.keys()):
				self.imageLink = info["imageLink"]
			else:
				self.imageLink = ""
			if "links" in list(info.keys()):
				self.links = info["links"]
			else:
				self.links = {}
			if "episodeProgress" in list(info.keys()):
				self.episodeProgress = info["episodeProgress"]
			else:
				self.episodeProgress = 1
			if "timeProgress" in list(info.keys()):
				self.timeProgress = info["timeProgress"]
			else:
				self.timeProgress = ""
			if "originalTitle" in list(info.keys()):
				self.originalTitle = info["originalTitle"]
			else:
				self.originalTitle = self.title
			if "discontinued" in list(info.keys()):
				self.discontinued = info["discontinued"]
			else:
				self.discontinued = False
			if "autoMode" in list(info.keys()):
				self.autoMode = info["autoMode"]
			else:
				self.autoMode = True
			if "starred" in list(info.keys()):
				self.starred = info["starred"]
			else:
				self.starred = False
			
			self.version = showVersion
		else:
			self.id = int(info)
			
			from json import loads, decoder
			showDataDict = loads(getSourceCode("https://api.tvmaze.com/shows/{0}?embed=seasons".format(self.id)))
			
			seasons = []
			for i in showDataDict["_embedded"]["seasons"]:
				if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
					if hasPassed(i["endDate"]):
						seasons.append(i["episodeOrder"])
					else:
						seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/{0}/episodes".format(i["id"]))
						seasonEpisodesDict = loads(seasonEpisodes)
						for j in seasonEpisodesDict:
							if not hasPassed(j["airdate"]):
								seasons.append(int(j["number"]) - 1)
								break
			
			if None in seasons:
				episodeList = getSourceCode("https://api.tvmaze.com/shows/{0}/episodes".format(showDataDict["id"]))
				episodeListDict = loads(episodeList)

				episodes = []
				for i in range(0, len(episodeListDict)):
					episodes.append(episodeListDict[i]["season"])

				seasons = []
				for i in range(1, episodes[len(episodes) - 1] + 1):
					seasons.append(episodes.count(i))
			
			self.title = removeForbidden(showDataDict["name"])
			if showDataDict["image"] == None:
				self.imageLink = ""
			else:
				self.imageLink = showDataDict["image"]["medium"]
			self.episodeData = seasons
			self.status = showDataDict["status"]
			self.links = {}
			self.episodeProgress = 1
			self.timeProgress = ""
			self.originalTitle = self.title
			self.discontinued = False
			self.autoMode = True
			self.starred = False
			self.version = showVersion
	
	
	def __str__(self):
		if self.starred:
			return "⋆" + self.title
		return self.title
	
	
	def __repr__(self):
		return "<Show \"{0}\">".format(self.title)
	
	
	def __lt__(self, other):
		selfStatus = self.getStatus()
		otherStatus = other.getStatus()
		
		if selfStatus == otherStatus:
			if self.starred == other.starred:
				return self.title < other.title
			elif self.starred and not other.starred:
				return True
			else:
				return False
		elif selfStatus < otherStatus:
			return True
		else:
			return False
		
	
	def getStatus(self):
		if self.isComplete():
			return "3complete"
		elif self.discontinued:
			return "4discontinued"
		elif self.episodeProgress != 1:
			return "1watching"
		else:
			return "2toWatch"
	
	
	def getSeasonEpisode(self):
		totalProgress = self.episodeProgress
		seasonNumber = 1
		for i in self.episodeData:
			totalProgress -= i
			seasonNumber += 1
			if totalProgress <= 0:
				totalProgress += i
				seasonNumber -= 1
				return [seasonNumber, totalProgress, len(self.episodeData), self.episodeData[seasonNumber - 1]]
				break
		return [seasonNumber, totalProgress, len(self.episodeData), 0]
	
	
	def isComplete(self):
		totalEpisodes = 0
		for i in self.episodeData:
			totalEpisodes += i
		return self.episodeProgress > totalEpisodes
	
	
	def dump(self):
		return {"id": self.id, "title": self.title, "imageLink": self.imageLink, "episodeData": self.episodeData, "status": self.status, "links": self.links, "episodeProgress": self.episodeProgress, "timeProgress": self.timeProgress, "originalTitle": self.originalTitle, "discontinued": self.discontinued, "autoMode": self.autoMode, "version": self.version, "starred": self.starred}



class Site:
	def __init__(self, file):
		with open(file) as site:
			info = site.read().split("\n")
			
			self.name = ".".join(file.split("\\")[-1].split(".")[:-1])
			self.priority = int(info[0].split(": ")[1])
			self.multipleSeasons = info[1].split(": ")[1] == "True"
			self.downloadable = info[2].split(": ")[1] == "True"
			
			self.firstLink = "\n".join(info[3:]).split("firstLink")[1].split("\n")[1:-1]
			if self.downloadable:
				self.downloadEpisode = "\n".join(info[3:]).split("downloadEpisode")[1].split("\n")[1:-1]
	
	
	def __lt__(self, other):
		return self.priority < other.priority
	
	
	def __repr__(self):
		return "<Site {}>".format(self.name)
	
	
	def getLinks(self, string, parent):
		links = modifyString(self.firstLink, string, parent)
		
		if self.multipleSeasons:
			for i in range(2, len(currentShow.episodeData) + 1):
				links += "\n" + modifyString(self.firstLink, "{} {}".format(string, i), parent)
				if links[-1] == "\n":
					return links[:-1]
		
		return links
	
	
	def getDownloadLink(self, link):
		return modifyString(self.downloadEpisode, link)



class ShowOptionsWindow:
	def __init__(self, search):
		global addingShows
		
		self.search = search
		
		showData = getSourceCode("https://api.tvmaze.com/search/shows?q={0}&embed=seasons".format(self.search))
		from json import loads, decoder
		
		try:
			showDataDict = loads(showData)
		except decoder.JSONDecodeError:
			print("ERROR: Invalid search: {0}".format(self.search))
			return
		
		shows = []
		for i in [x["show"] for x in showDataDict]:
			shows.append(Show(int(i["id"])))
		
		if len(shows) == 1:
			show = shows[0]
			
			if show.id in [x.id for x in data]:
				overwriteShow = messagebox.askyesnocancel("Overwrite show", "{0} already exists, would you like to overwrite it?".format(show.title))
			else:
				overwriteShow = False
			
			if overwriteShow:
				data[[x.id for x in data].index(show.id)] = show
				sortData()
				setShow(show)
			elif overwriteShow == False:
				data.append(show)
				sortData()
				setShow(show)
		else:
			for i in shows:
				Thread(target=lambda: downloadImage(i, True), daemon=True).start()
			
			notDownloaded = True
			while notDownloaded:
				notDownloaded = False
				for i in shows:
					notDownloaded = notDownloaded or i.id not in list(smallPictures.keys())
			
			self.optionsMenu = Toplevel(root, bg=backgroundColor)
			self.optionsMenu.title("Search for \"{0}\"".format(search))
			self.optionsMenu.resizable(False, False)
			self.optionsMenu.focus_set()
			
			self.optionsMenu.bind("<Control-w>", lambda x: self.optionsMenu.destroy())
			self.optionsMenu.bind("<Escape>", lambda x: self.optionsMenu.destroy())
			
			self.optionsMenu.bind("<Up>", lambda x: self.options[0].choiceFrame.focus_set() if self.optionsMenu.focus_get() == self.optionsMenu else False)
			self.optionsMenu.bind("<Down>", lambda x: self.options[0].choiceFrame.focus_set() if self.optionsMenu.focus_get() == self.optionsMenu else False)
			self.optionsMenu.bind("<Left>", lambda x: self.options[0].choiceFrame.focus_set() if self.optionsMenu.focus_get() == self.optionsMenu else False)
			self.optionsMenu.bind("<Right>", lambda x: self.options[0].choiceFrame.focus_set() if self.optionsMenu.focus_get() == self.optionsMenu else False)
			
			if len(shows) == 0:
				title = Label(self.optionsMenu, text="No results found for for \"{0}\"".format(search), fg=foregroundColor, bg=backgroundColor, font=titleFont)
			else:
				title = Label(self.optionsMenu, text="Pick a show for \"{0}\"".format(search), fg=foregroundColor, bg=backgroundColor, font=titleFont)
			title.grid(columnspan=5)
			
			self.options = []
			x = 1
			y = 0
			for i in shows:
				self.options.append(ShowOption(self, i.title, i.id, x, y))
				y += 1
				if y >= 5:
					y = 0
					x += 1
			
			self.cancelButton = Button(self.optionsMenu, text="Cancel", command=lambda: self.optionsMenu.destroy(), fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
			if len(shows) < 5:
				self.cancelButton.grid(row=1, column=4, sticky="sew", padx=5, pady=(0,5))
			elif len(shows) > 5 and len(shows) < 10:
				self.cancelButton.grid(row=2, column=4, sticky="sew", padx=5, pady=(0,5))
			else:
				self.cancelButton.grid(column=4, sticky="nsew", padx=5, pady=(0,5))
		
		addingShows -= 1
		if addingShows == 0:
			addButton.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=3, padx=3)
			addProgress.grid_forget()
			
			root.bind("<Control-n>", lambda x: addShowButton())
			settingsButton['state'] = NORMAL
	
	
	def focusShow(self, x, y):
		if y < 0:
			y = 4
		elif y >= 5:
			y = 0
		
		if x < 1:
			x = 2
		elif x > 2:
			x = 1
		
		for i in self.options:
			if i.x == x and i.y == y:
				i.choiceFrame.focus_set()



class ShowOption:
	def __init__(self, parentObject, title, id, x, y):
		self.parent = parentObject.optionsMenu
		self.parentObject = parentObject
		self.selected = False
		self.title = title
		self.id = id
		self.x = x
		self.y = y
		
		self.choiceFrame = Frame(self.parent, bg=backgroundColor, width=126, height=177)
		self.choiceFrame.grid(row=self.x, column=self.y, sticky="nw", padx=(0,5), pady=(0,5))
		self.choiceFrame.grid_propagate(False)
		
		self.showPhoto = Label(self.choiceFrame, bg=backgroundColor)
		self.showPhoto["image"] = smallPictures[self.id]
		self.showPhoto.grid(sticky="nw")
		
		self.showName = Label(self.choiceFrame, text=self.title, fg=foregroundColor, bg=backgroundColor, wraplength=126)
		
		self.choiceFrame.bind("<Enter>", lambda x: self.choiceFrame.focus_set())
		self.choiceFrame.bind("<Leave>", lambda x: self.parent.focus_set())
		
		self.choiceFrame.bind("<FocusIn>", lambda x: self.setHovered(True))
		self.choiceFrame.bind("<FocusOut>", lambda x: self.setHovered(False))
		
		self.choiceFrame.bind("<Up>", lambda x: self.parentObject.focusShow(self.x - 1, self.y))
		self.choiceFrame.bind("<Down>", lambda x: self.parentObject.focusShow(self.x + 1, self.y))
		self.choiceFrame.bind("<Left>", lambda x: self.parentObject.focusShow(self.x, self.y - 1))
		self.choiceFrame.bind("<Right>", lambda x: self.parentObject.focusShow(self.x, self.y + 1))
		
		self.choiceFrame.bind("<Return>", lambda x: self.selectShow())
		self.choiceFrame.bind("<space>", lambda x: self.selectShow())
		
		self.showPhoto.bind("<Button-1>", lambda x: self.selectShow())
		self.showName.bind("<Button-1>", lambda x: self.selectShow())
	
	
	def setHovered(self, hovered):
		if hovered:
			self.showName.grid(row=0, sticky="sew", pady=2)
		else:
			self.showName.grid_forget()
	
	
	def selectShow(self):
		self.parent.destroy()

		show = Show(self.id)
		
		if show.id in [x.id for x in data]:
			overwriteShow = messagebox.askyesnocancel("Overwrite show", "{0} already exists, would you like to overwrite it?".format(show.title))
		else:
			overwriteShow = False
		
		if overwriteShow:
			data[[x.id for x in data].index(show.id)] = show
		elif overwriteShow == False:
			data.append(show)
		else:
			return
		
		sortData()
		setShow(show)



class SettingsWindow:
	def __init__(self):
		self.show = currentShow
		self.window = Toplevel(bg=backgroundColor)
		
		self.window.title("{0} Settings".format(self.show.title))
		self.window.resizable(False, False)
		
		self.window.bind("<Destroy>", self.submit)
		self.window.bind("<Control-w>", self.submit)
		self.window.bind("<Escape>", self.submit)
		root.bind("<FocusIn>", self.submit)
		
		self.titleVar = StringVar()
		self.progressVar = StringVar()
		self.episodeDataVar = StringVar()
		self.autoVar = IntVar()
		
		self.titleVar.set(self.show.title)
		self.progressVar.set(self.show.episodeProgress)
		self.episodeDataVar.set(",".join([str(x) for x in self.show.episodeData]))
		self.autoVar.set(self.show.autoMode)
		self.links = self.show.links
		self.sites = list([x.name for x in sites])
		
		titleFrame = Frame(self.window, bg=backgroundColor)
		titleFrame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		titleFrame.columnconfigure(1, weight=1)
		
		progressFrame = Frame(self.window, bg=backgroundColor)
		progressFrame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		progressFrame.columnconfigure(1, weight=1)
		
		episodeDataFrame = Frame(self.window, bg=backgroundColor)
		episodeDataFrame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		episodeDataFrame.columnconfigure(1, weight=1)
		
		linkFrame = Frame(self.window, bg=backgroundColor)
		if showLinkInfo:
			linkFrame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		linkFrame.columnconfigure(1, weight=1)
		linkFrame.rowconfigure(1, weight=1)
		
		titleLabel = Label(titleFrame, text="Title:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		self.titleEntry = Entry(titleFrame, textvariable=self.titleVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor, width=min(len(self.titleVar.get()) + 1, 100))
		self.titleEntry.bind("<Return>", self.submit)
		idLabel = Label(titleFrame, text="(ID: {})".format(self.show.id), font=labelFont, fg=foregroundColor, bg=backgroundColor)
		progressLabel = Label(progressFrame, text="Episode Progress:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		progressEntry = Entry(progressFrame, textvariable=self.progressVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor, width=min(len(self.progressVar.get()) + 1, 100))
		progressEntry.bind("<Return>", self.submit)
		episodeDataLabel = Label(episodeDataFrame, text="Episode Data:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		self.episodeDataEntry = Entry(episodeDataFrame, textvariable=self.episodeDataVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, disabledforeground=disabledColor, disabledbackground=backgroundColor, insertbackground=foregroundColor, width=min(len(self.episodeDataVar.get()) + 1, 100))
		self.episodeDataEntry.bind("<Return>", self.submit)
		autoCheckbox = Checkbutton(episodeDataFrame, text="Auto", variable=self.autoVar, fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, command=self.toggleAuto)
		if self.show.autoMode:
			self.episodeDataEntry["state"] = DISABLED
		else:
			self.episodeDataEntry["state"] = NORMAL
		
		linksLabel = Label(linkFrame, text="Links:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		
		if darkMode:
			style = ttk.Style()
			style.configure("TCombobox", background="black", bordercolor="black", darkcolor="black", foreground="white", arrowcolor="white", lightcolor="grey")
			style.map("TCombobox", fieldbackground=[("readonly", "black")], selectbackground=[("readonly", "black")], selectforeground=[("readonly", "white")], background=[("readonly", "black")])
		self.linkSitesCombobox = ttk.Combobox(linkFrame, values=self.sites, state="readonly", postcommand=self.saveLinks())
		self.linkSitesCombobox.option_add("*TCombobox*Listbox.background", "black")
		self.linkSitesCombobox.option_add("*TCombobox*Listbox.foreground", "white")
		self.linkSitesCombobox.option_add("*TCombobox*Listbox.selectBackground", "grey")
		self.linkSitesCombobox.option_add("*TCombobox*Listbox.selectForeground", "white")
		self.linkSitesCombobox.bind("<<ComboboxSelected>>", self.changeSite)
		try:
			self.linkSitesCombobox.current(0)
			self.oldSite = self.linkSitesCombobox.get()
		except:
			pass
		
		self.linkText = Text(linkFrame, bg=backgroundColor, fg=foregroundColor, font=dataFont, insertbackground=foregroundColor, width=30, height=5, undo=True, autoseparators=True, maxundo=0)
		try:
			self.linkText.insert(END, "\n".join(self.links[self.sites[0]]))
		except:
			pass
		
		self.resetTitleButton = Button(self.window, text="Reset Title", fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor, command=self.resetTitle)
		resetLinkButton = Button(self.window, text="Reset Link", fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor, command=self.resetLink)
		
		titleLabel.grid(row=0, column=0, sticky="w")
		self.titleEntry.grid(row=0, column=1, sticky="ew")
		self.titleEntry.selection_range(0, END)
		self.titleEntry.icursor(END)
		self.titleEntry.focus_set()
		idLabel.grid(row=0, column=2, sticky="w")
		progressLabel.grid(row=0, column=0, sticky="w")
		progressEntry.grid(row=0, column=1, sticky="ew")
		episodeDataLabel.grid(row=0, column=0, sticky="w")
		self.episodeDataEntry.grid(row=0, column=1, sticky="ew")
		autoCheckbox.grid(row=0, column=2, sticky="w")
		linksLabel.grid(row=0, column=0, sticky="w")
		self.linkSitesCombobox.grid(row=0, column=1, sticky="ew")
		self.linkText.grid(row=1, column=0, columnspan=2, sticky="nsew")
		if showLinkInfo:
			self.resetTitleButton.grid(row=4, column=0, sticky="ew", padx=5, pady=3)
			resetLinkButton.grid(row=4, column=1, sticky="ew", padx=5, pady=3)
		else:
			self.resetTitleButton.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		
		self.titleEntry.bind("<Key>", self.updateSize)
		progressEntry.bind("<Key>", self.updateSize)
		self.episodeDataEntry.bind("<Key>", self.updateSize)
		self.linkText.bind("<Key>", self.textSize)
		self.linkText.bind("<Tab>", self.textTab)
	
	
	def resetTitle(self):
		self.titleVar.set(self.show.originalTitle)
		self.titleEntry.selection_clear()
		self.titleEntry.icursor(END)
		self.titleEntry.focus_set()
	
	
	def resetLink(self):
		self.linkText.delete(0.0, END)
		try:
			self.linkText.insert(END, sites[self.linkSitesCombobox.current()].getLinks(self.show.title, self))
			self.textSize()
		except TclError:
			pass
	
	
	def updateSize(self, event):
		if event.char.lower() in "abcdefghijklmnopqrstuvwxyz" and not event.char.lower() == "":
			event.widget.config(width=min(len(event.widget.get()) + 2, 100))
		elif event.keysym == "Delete" or event.keysym == "BackSpace":
			event.widget.config(width=min(len(event.widget.get()), 100))
		else:
			event.widget.config(width=min(len(event.widget.get()) + 1, 100))
	
	
	def textSize(self, event=None):
		height = self.linkText.tk.call((self.linkText._w, "count", "-update", "-displaylines", "0.0", "end"))
		
		if event and event.keysym == "Return":
			height += 1
		if height < 4:
			height = 4
		
		self.linkText.config(height=height + 1)
	
	
	def textTab(self, event):
		self.resetTitleButton.focus_set()
		return "break"
	
	
	def saveLinks(self):
		try:
			if self.linkText.get(0.0, END) == "\n":
				if self.oldSite in self.links:
					del self.links[self.oldSite]
			else:
				self.links[self.oldSite] = self.linkText.get(0.0, END).split("\n")[:-1]
		except AttributeError:
			pass
	
	
	def changeSite(self, event):
		self.saveLinks()
		self.linkText.delete(0.0, END)
		
		if self.linkSitesCombobox.get() in self.links:
			self.linkText.insert(END, "\n".join(self.links[self.linkSitesCombobox.get()]))
		self.textSize()
		self.oldSite = self.linkSitesCombobox.get()
	
	
	def toggleAuto(self):
		if self.autoVar.get():
			self.episodeDataEntry["state"] = DISABLED
			updateShow(self.show, True)
			self.episodeDataVar.set(",".join([str(x) for x in self.show.episodeData]))
		else:
			self.episodeDataEntry["state"] = NORMAL
	
	
	def submit(self, x):
		self.show.title = removeForbidden(self.titleVar.get())
		self.show.episodeProgress = int(self.progressVar.get())
		self.show.episodeData = [int(x) for x in self.episodeDataVar.get().split(",")]
		self.show.autoMode = self.autoVar.get() == 1
		try:
			self.saveLinks()
		except:
			pass
		
		root.unbind("<FocusIn>")
		self.window.destroy()
		
		sortData()
		setShow()


class PreferencesWindow():
	def __init__(self):
		self.window = Toplevel(bg=backgroundColor)
		
		self.window.title("Preferences")
		self.window.resizable(False, False)
		self.window.focus_set()
		
		self.window.bind("<Destroy>", self.submit)
		self.window.bind("<Control-w>", self.submit)
		self.window.bind("<Escape>", self.submit)
		root.bind("<FocusIn>", self.submit)
		
		self.fileLocationVar = StringVar()
		self.errorUrlVar = StringVar()
		self.browserTimeoutVar = IntVar()
		
		self.fileLocationVar.set(dataPath.replace(str(Path.home()), "{}"))
		self.errorUrlVar.set(errorUrl)
		self.browserTimeoutVar.set(browserTimeout)
		
		self.showUpdateProgressVar = IntVar()
		self.showImageProgressVar = IntVar()
		self.slowModeVar = IntVar()
		self.showBrowserVar = IntVar()
		self.darkModeVar = IntVar()
		
		if darkMode:
			self.darkModeVar.set(1)
		if slowMode:
			self.slowModeVar.set(1)
		if showBrowser:
			self.showBrowserVar.set(1)
		if showImageProgress:
			self.showImageProgressVar.set(1)
		if showUpdateProgress:
			self.showUpdateProgressVar.set(1)
		
		self.textFrame = Frame(self.window, bg=backgroundColor)
		self.fileLocationEntry = Entry(self.textFrame, textvariable=self.fileLocationVar, width=75, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
		self.errorUrlEntry = Entry(self.textFrame, textvariable=self.errorUrlVar, width=75, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
		
		if darkMode:
			style = ttk.Style()
			style.configure("TSpinbox", background="black", bordercolor="black", darkcolor="black", foreground="white", arrowcolor="white", lightcolor="grey", fieldbackground="black", insertcolor="white")
		self.browserTimeoutEntry = ttk.Spinbox(self.textFrame, textvariable=self.browserTimeoutVar, width=5, font=dataFont, values=list(range(1, 60)))
		
		self.fileLocationEntry.grid(row=0, column=0, padx=2, pady=2)
		self.errorUrlEntry.grid(row=1, column=0, padx=2, pady=2)
		self.browserTimeoutEntry.grid(row=2, column=0, padx=2, pady=2, sticky="w")
		self.textFrame.grid(row=0, column=0, padx=2, pady=2, sticky="nw")
		
		self.checkFrame = Frame(self.window, bg=backgroundColor)
		self.darkModeCheckbutton = Checkbutton(self.checkFrame, text="Dark mode", fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, variable=self.darkModeVar)
		self.slowModeCheckbutton = Checkbutton(self.checkFrame, text="Slow mode", fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, variable=self.slowModeVar)
		self.showBrowserCheckbutton = Checkbutton(self.checkFrame, text="Show browser", fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, variable=self.showBrowserVar)
		self.showImageProgressCheckbutton = Checkbutton(self.checkFrame, text="Show image downloading progressbar", fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, variable=self.showImageProgressVar)
		self.showUpdateProgressCheckbutton = Checkbutton(self.checkFrame, text="Show updating shows progressbar", fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, variable=self.showUpdateProgressVar)
		
		self.darkModeCheckbutton.grid(row=0, column=0, padx=2, pady=2, sticky="nw")
		self.slowModeCheckbutton.grid(row=1, column=0, padx=2, pady=2, sticky="nw")
		self.showBrowserCheckbutton.grid(row=2, column=0, padx=2, pady=2, sticky="nw")
		self.showImageProgressCheckbutton.grid(row=3, column=0, padx=2, pady=2, sticky="nw")
		self.showUpdateProgressCheckbutton.grid(row=4, column=0, padx=2, pady=2, sticky="nw")
		self.checkFrame.grid(row=0, column=1, padx=2, pady=2, sticky="nw")
	
	
	def submit(self, event):
		global dataPath, errorUrl, showImageProgress, showUpdateProgress, browserTimeout, showBrowser, darkMode, slowMode, downloadProgress, updateProgress, completedShows
		
		root.unbind("<FocusIn>")
		self.window.unbind("<Destroy>")
		self.window.unbind("<Control-w>")
		self.window.unbind("<Escape>")
		
		with open(tempPath + "settings.conf", "w") as file:
			dataPath = self.fileLocationVar.get().format(Path.home())
			errorUrl = self.errorUrlVar.get()
			
			showImageProgress = self.showImageProgressVar.get() == 1
			try:
				downloadProgress.destroy()
			except:
				pass
			if showImageProgress:
				downloadProgress = ProgressBar(root, len(set([x.id for x in data])), "Images")
				downloadProgress.set(len(pictures))
			
			showUpdateProgress = self.showUpdateProgressVar.get() == 1
			try:
				updateProgress.destroy()
			except:
				pass
			if showUpdateProgress:
				updateProgress = ProgressBar(root, len(data), "Updates")
				updateProgress.set(len(completedShows))
			
			browserTimeout = self.browserTimeoutVar.get()
			showBrowser = self.showBrowserVar.get() == 1
			darkMode = self.darkModeVar.get() == 1
			slowMode = self.slowModeVar.get() == 1
			
			if self.fileLocationVar.get() != "{}\\Desktop\\Progress.dat":
				file.write("fileLocation\n")
				file.write(self.fileLocationVar.get() + "\n")
			if self.errorUrlVar.get() != "https://static.tvmaze.com/images/no-img/no-img-portrait-text.png":
				file.write("errorUrl\n")
				file.write(self.errorUrlVar.get() + "\n")
			if self.showImageProgressVar.get() != 0:
				file.write("showImageProgress\n")
				file.write("True\n")
			if self.showUpdateProgressVar.get() != 0:
				file.write("showUpdateProgress\n")
				file.write("True\n")
			if self.browserTimeoutVar.get() != 30:
				file.write("browserTimeout\n")
				file.write(str(self.browserTimeoutVar.get()) + "\n")
			if self.showBrowserVar.get() != 0:
				file.write("showBrowser\n")
				file.write("True\n")
			if self.darkModeVar.get() != 1:
				file.write("darkMode\n")
				file.write("False\n")
			if self.slowModeVar.get() != 1:
				file.write("slowMode\n")
				file.write("False\n")
		
		self.window.destroy()



class ProgressBar:
	def __init__(self, parent, maximum, label=""):
		self.maximum = maximum
		
		self.frame = Frame(parent, bg=backgroundColor)
		
		if darkMode:
			self.bar = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=296, maximum=self.maximum, mode="determinate", style="My.Horizontal.TProgressbar")
		else:
			self.bar = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=296, maximum=self.maximum, mode="determinate")
		self.bar.grid(row=0, column=0, padx=2, pady=2)
		
		self.button = Button(self.frame, text="Hide", command=self.destroy, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
		self.button.grid(row=0, column=1, padx=2, pady=2)
		
		if label != "":
			self.label = Label(self.frame, text=label, font=labelFont, bg=backgroundColor, fg=foregroundColor)
			self.label.grid(row=0, column=2, padx=2, pady=2)
		
		self.frame.grid(columnspan=4, sticky="ew")
	
	
	def isComplete(self):
		return self.bar["value"] >= self.maximum
	
	
	def destroy(self, x=None):
		self.frame.grid_forget()
		self.bar["value"] = self.maximum
	
	
	def add(self, n=1):
		self.bar["value"] += n
		
		if self.isComplete():
			self.destroy()
	
	
	def set(self, n=1):
		self.bar["value"] = n
		
		if self.isComplete():
			self.destroy()



# Simple functions def _______________SIMPLE FUNCTIONS:
def getSourceCode(url):
	from requests import get, exceptions
	import urllib.request
	try:
		return get(url).text
	except (urllib.error.URLError, exceptions.SSLError, exceptions.ConnectionError):
		goOffline()


def removeForbidden(string):
	return string.replace("|", "").encode("cp1252", "ignore").decode('cp1252')


# Takes in a date as "m-d-y"
def hasPassed(date):
	from datetime import datetime
	return (datetime.now() - datetime(int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2]))).days >= 0


def askMultipleChoice(prompt, options):
	window = Toplevel(root)
	if prompt:
		Label(window, text=prompt).grid()
	var = IntVar()
	for i, option in enumerate(options):
		Radiobutton(window, text=option, variable=var, value=i).grid(sticky="w")
	Button(window, text="Submit", command=window.destroy).grid()
	
	window.bind("<Up>", lambda x: var.set(var.get() - 1))
	window.bind("<Down>", lambda x: var.set(var.get() + 1))
	window.bind("<Return>", lambda x: window.destroy())
	window.bind("<Escape>", lambda x: window.destroy())
	window.bind("<Control-w>", lambda x: window.destroy())
	window.focus_set()
	
	root.wait_window(window)
	return var.get()


def getElementAttribute(url, element, attribute):
	try:
		from lxml import etree
		from requests import get, exceptions
		import urllib.request
		try:
			r = get(url)
			html = r.text
		except exceptions.SSLError:
			html = ""
		
		try:
			root = etree.HTML(html)
			
			output = []
			for i in root.cssselect(element):
				output.append(i.get(attribute))
				if output[-1][0] == "/":
					output[-1] = "/".join(url.split("/")[:3]) + output[-1]
			
			return output
		except (IndexError, AttributeError):
			from selenium import webdriver
			from selenium.webdriver.support import expected_conditions as EC
			from selenium.webdriver.support.ui import WebDriverWait
			from selenium.webdriver.common.by import By
			from selenium.common.exceptions import TimeoutException
			
			options = webdriver.ChromeOptions()
			if not showBrowser:
				options.add_argument("--window-size=0,0")
				options.add_argument("--window-position=3000,3000")
			
			options.add_argument("--disable-blink-features=AutomationControlled")
			options.add_experimental_option("excludeSwitches", ["enable-automation"])
			options.add_experimental_option('excludeSwitches', ['enable-logging'])
			options.add_experimental_option('useAutomationExtension', False)
			
			browser = webdriver.Chrome("C:\Program Files\ChromeDriver\chromedriver.exe", options=options)
			if not showBrowser:
				browser.minimize_window()
			
			browser.get(url)
			
			browser.execute_script("window.open('/');")
			if not showBrowser:
				browser.minimize_window()
			
			try:
				WebDriverWait(browser, browserTimeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "{0}[{1}]".format(element, attribute))))
			except TimeoutException:
				print("hi")
				browser.quit()
				return []
			
			html = browser.page_source.encode("cp1252", "ignore").decode('cp1252')
			
			browser.quit()
			
			root = etree.HTML(html)
			
			output = []
			for i in root.cssselect(element):
				output.append(i.get(attribute))
				if output[-1][0] == "/":
					output[-1] = "/".join(url.split("/")[:3]) + output[-1]
			
			return output
	except (urllib.error.URLError, exceptions.SSLError, exceptions.ConnectionError) as e:
		goOffline()


def modifyString(instructions, string, parent=None):
	string = [string]
	
	for i in range(len(instructions)):
		word = instructions[i]
		
		if word in ["getElementAttribute", "replace", "split", "insert", "debase", "add"]:
			index = int(instructions[i + 1])
			
			if word == "getElementAttribute":
				results = getElementAttribute(instructions[i + 2].format(string[index]), instructions[i + 3], instructions[i + 4])
				if results == []:
					if parent:
						parent.window.unbind("<Destroy>")
						messagebox.showinfo("No Results Found", "No search results were found for the search {}".format(string[0]), parent=parent.window)
						if parent.window.winfo_exists():
							parent.window.bind("<Destroy>", parent.submit)
					return ""
				
				string[index] = results[int(instructions[i + 5])]
			elif word == "replace":
				string[index] = string[index].replace(instructions[i + 2], instructions[i + 3])
			elif word == "split":
				from re import split
				string = string[:index] + split(instructions[i + 2], string[index]) + string[index + 1:]
			elif word == "insert":
				string.insert(index, instructions[i + 2])
			elif word == "debase":
				from base64 import b64decode
				string[index] = b64decode(bytes(string[index] + (len(string[index]) % 4 * "="), "UTF-8")).decode("utf-8")
			elif word == "add":
				string[index] = str(int(string[index]) + int(instructions[i + 2]))

	return "".join(string)



# Unique functions def ______________UNIQUE FUNCTIONS:
def goOffline():
	global offline
	if not offline:
		from time import sleep
		sleep(.001)
		
		banner.grid(row=0, column=0, columnspan=4, sticky="new")
		banner.bind("<Button-1>", goOnline)
		bannerText.bind("<Button-1>", goOnline)
	
	offline = True
	addButton["state"] = DISABLED


def goOnline(event=None):
	global offline
	banner.grid_forget()
	offline = False
	addButton["state"] = NORMAL
	
	setShow()
	Thread(target=downloadImages, daemon=True).start()
	Thread(target=updateShows, daemon=True).start()


def sortData():
	global data
	
	data = sorted(data)
	showList.set(data)
	
	watchingEnd = len([x for x in data if x.getStatus() in ["1watching"]])
	toWatchEnd = len([x for x in data if x.getStatus() in ["1watching", "2toWatch"]])
	finishedEnd = len([x for x in data if x.getStatus() in ["1watching", "2toWatch", "3complete"]])
	
	for i in range(0, len(data)):
		if i < watchingEnd:
			showListBox.itemconfigure(i, background=listBoxWatchingColor, foreground=listBoxWatchingTextColor)
		elif i >= toWatchEnd and i < finishedEnd:
			showListBox.itemconfigure(i, background=listBoxWatchedColor, foreground=listBoxWatchedTextColor)
		elif i >= finishedEnd:
			showListBox.itemconfigure(i, background=listBoxDiscontinuedColor, foreground=listBoxDiscontinuedTextColor)
		else:
			if i % 2 == 0:
				showListBox.itemconfigure(i, background=listBoxColor1, foreground=listBoxTextColor1)
			else:
				showListBox.itemconfigure(i, background=listBoxColor2, foreground=listBoxTextColor2)


def downloadImage(show, small = False):
	import urllib.request
	global smallPictures, pictures
	
	if "error" not in pictures:
		try:
			pictures["error"] = ImageTk.PhotoImage(Image.open(tempPath + "error.jpg").resize((210, 295)))
		except FileNotFoundError:
			urllib.request.urlretrieve(errorUrl, tempPath + "error.jpg")
	
	if show.id == currentShow.id and show.id in pictures:
		return
	
	if not path.exists(tempPath + "Images\\"):
		mkdir(tempPath + "Images\\")
	
	if show.imageLink == "":
		imageDestination = tempPath + "error.jpg"
	elif offline:
		return
	else:
		imageDestination = "{0}{1}.jpg".format(tempPath + "Images\\", show.id)
		
		if not (path.exists(imageDestination) and path.getsize(imageDestination) != 0):
			try:
				urllib.request.urlretrieve(show.imageLink, imageDestination)
			except:
				goOffline()
				return
	
	try:
		if small:
			smallPictures[show.id] = ImageTk.PhotoImage(Image.open(imageDestination).resize((126, 177)))
		else:
			pictures[show.id] = ImageTk.PhotoImage(Image.open(imageDestination).resize((210, 295)))
	except:
		try:
			urllib.request.urlretrieve(show.imageLink, imageDestination)
			
			if small:
				smallPictures[show.id] = ImageTk.PhotoImage(Image.open(imageDestination).resize((126, 177)))
			else:
				pictures[show.id] = ImageTk.PhotoImage(Image.open(imageDestination).resize((210, 295)))
		except:
			goOffline()
			return


def downloadImages():
	for i in data:
		Thread(target=lambda: downloadImage(i), daemon=True).start()
	
	if showImageProgress:
		global downloadProgress
		try:
			downloadProgress.destroy()
		except:
			pass
		downloadProgress = ProgressBar(root, len(set([x.id for x in data])), "Images")
		
		from time import sleep
		while len(pictures) < len(set([x.id for x in data])):
			if len(pictures) != downloadProgress.bar["value"]:
				downloadProgress.set(len(pictures))
			sleep(.1)
		downloadProgress.destroy()


def updateShow(show, bypass=False):
	if bypass or (show.autoMode and show.status != "Ended" and (not offline)):
		showData = getSourceCode("http://api.tvmaze.com/shows/{0}?embed=seasons".format(show.id))
		from json import loads, decoder

		try:
			showDataDict = loads(showData)
		except decoder.JSONDecodeError:
			print("ERROR: Invalid show: {0}".format(repr(show)))
			if showUpdateProgress and not updateProgress.isComplete():
				updateProgress.add()
			return
		except TypeError:
			if showUpdateProgress and not updateProgress.isComplete():
				updateProgress.add()
			return
		
		show.originalTitle = removeForbidden(showDataDict["name"])
		if showDataDict["image"] == None:
			show.imageLink = ""
		else:
			show.imageLink = showDataDict["image"]["medium"]
		show.status = showDataDict["status"]
		
		seasons = []
		for i in showDataDict["_embedded"]["seasons"]:
			if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
				if hasPassed(i["endDate"]):
					seasons.append(i["episodeOrder"])
				else:
					seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/" + str(i["id"]) + "/episodes")
					try:
						seasonEpisodesDict = loads(seasonEpisodes)
						for j in seasonEpisodesDict:
							if not hasPassed(j["airdate"]) and j["number"] != None:
								seasons.append(int(j["number"]) - 1)
								break
					except TypeError:
						if showUpdateProgress and not updateProgress.isComplete():
							updateProgress.add()
						return
		
		if None in seasons:
			episodeList = getSourceCode("https://api.tvmaze.com/shows/{0}/episodes".format(show.id))
			try:
				episodeListDict = loads(episodeList)
			except TypeError:
				if showUpdateProgress and not updateProgress.isComplete():
					updateProgress.add()
				return
			
			episodes = []
			for i in range(0, len(episodeListDict)):
				if episodeListDict[i]["airdate"] != None and hasPassed(episodeListDict[i]["airdate"]):
					episodes.append(episodeListDict[i]["season"])

			seasons = []
			for i in range(1, episodes[len(episodes) - 1] + 1):
				seasons.append(episodes.count(i))
		
		if show.episodeData != seasons:
			show.episodeData = seasons
			sortData()
			setShow()
	
	completedShows.append("done")
	if showUpdateProgress and not updateProgress.isComplete():
		updateProgress.set(len(completedShows))


def updateShows():
	global completedShows
	completedShows = []
	if showUpdateProgress:
		global updateProgress
		try:
			updateProgress.destroy()
		except:
			pass
		updateProgress = ProgressBar(root, len(data), "Updates")
	
	if slowMode:
		for i in data:
			updateShow(i)
	else:
		for i in data:
			Thread(target=lambda: updateShow(i), daemon=True).start()


def setShow(show = None):
	global currentShow, currentShowNum, title, picture, image
	if len(data) == 0:
		season.grid_forget()
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		starButton.grid_forget()
		discontinueButton.grid_forget()
		
		showTitle.set("No Shows ")
		title.config(fg="#ffffff")
		picture.grid_forget()
		deleteButton.grid_forget()
		settingsButton.grid_forget()
		return
	elif len(data) == 1:
		title.grid(column=2, row=1, sticky="nw", columnspan=3)
		picture.grid(column=2, row=2, sticky="nw", rowspan=2)
		deleteButton.grid(column=0, row=6, sticky="new", pady=2)
		settingsButton.grid(column=0, row=5, sticky="new", pady=2)
	
	if type(show) == Event:
		currentShow = data[showListBox.curselection()[0]]
	elif type(show) == str:
		currentShow = data[[x.title for x in data].index(show)]
	elif type(show) == int:
		currentShow = data[max(0, min(show, len(data)-1))]
	elif type(show) == Show:
		currentShow = data[data.index(show)]
	
	currentShowNum = data.index(currentShow)
	
	showListBox.selection_clear(0, END)
	showListBox.selection_set(currentShowNum)
	showListBox.activate(currentShowNum)
	showListBox.see(currentShowNum)
	
	showTitle.set(currentShow.title)
	
	if currentShow.status == "Ended":
		title.config(fg="#800000")
	elif currentShow.status == "Running":
		title.config(fg="#008000")
	else:
		title.config(fg="#807d00")
	
	if currentShow.id not in list(pictures.keys()):
		downloadImage(currentShow)
	
	if currentShow.id not in list(pictures.keys()):
		picture["image"] = pictures["error"]
	else:
		picture["image"] = pictures[currentShow.id]
	
	if currentShow.discontinued:
		seasonProgress.set("Discontinued")
		season.grid(column=0, row=0, columnspan=2, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		starButton.grid_forget()
		discontinueButton.grid(column=0, row=8, sticky="new", pady=2)
		discontinueButton.config(text="Recontinue")
	elif currentShow.isComplete():
		seasonProgress.set("Finished")
		season.grid(column=0, row=0, columnspan=2, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		
		starButton.grid(column=0, row=7, sticky="new", pady=2)
		if currentShow.starred:
			starButton.config(text="Unstar")
		else:
			starButton.config(text="Star")
		
		discontinueButton.grid_forget()
	else:
		seas, epi, seasMax, epiMax = currentShow.getSeasonEpisode()
		episodeProgress.set("Episode {0}/{1}".format(epi, epiMax))
		timeProgress.set(currentShow.timeProgress)
		
		if seasMax == 1:
			seasonProgress.set("Season 1")
		else:
			seasonProgress.set("Season {0}/{1}".format(seas, seasMax))
		season.grid(column=0, row=0, columnspan=2, sticky="nw", pady=2)
		
		episode.grid(column=0, row=1, columnspan=2, sticky="nw", pady=2)
		timeFrame.grid(column=0, row=2, sticky="nw", pady=2)
		
		if showLinkInfo:
			linkButton.grid(column=0, row=3, sticky="new", pady=2)
			if currentShow.links:
				linkButton["state"] = NORMAL
			else:
				linkButton["state"] = DISABLED
		
		completeButton.grid(column=0, row=4, sticky="new", pady=2)
		
		starButton.grid(column=0, row=7, sticky="new", pady=2)
		if currentShow.starred:
			starButton.config(text="Unstar")
		else:
			starButton.config(text="Star")
		
		discontinueButton.grid(column=0, row=8, sticky="new", pady=2)
		discontinueButton.config(text="Discontinue")



# Main window commands def ____MAIN WINDOW COMMANDS:
def addShowButton():
	newShowName.set("")
	addEntry.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=3, padx=3)
	addButton.grid_forget()
	addEntry.focus_set()
	root.bind("<Button-1>", click)


def addEntryHovered(hovering):
	global addEntryHovering
	addEntryHovering = hovering


def click(x):
	if not addEntryHovering:
		closeAddEntry()


def closeAddEntry(x = None):
	addButton.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=3, padx=3)
	addEntry.grid_forget()
	showListBox.focus_set()
	root.unbind("<Button-1>")


def submitAddEntry(x):
	global addingShows
	
	settingsButton['state'] = DISABLED
	addEntry.grid_forget()
	addProgress.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=3)
	addProgress.start()
	showListBox.focus_set()
	root.unbind("<Control-n>")
	root.unbind("<Button-1>")
	
	for i in newShowName.get().split("|"):
		addingShows += 1
		Thread(target=lambda: ShowOptionsWindow(i), daemon=True).start()


def changeTime(time):
	if type(time) == Event:
		currentShow.timeProgress = timeProgress.get()
	else:
		currentShow.timeProgress = time


def openLink():
	season, episode, seasMax, epiMax = currentShow.getSeasonEpisode()
	totalEpisode = currentShow.episodeProgress
	
	if not currentShow.links:
		return
	
	for i in [x.name for x in sites]:
		if i in currentShow.links:
			siteName = i
			links = currentShow.links[i]
			break
	
	if len(links) > 1:
		if season >= len(links):
			link = links[-1]
		else:
			link = links[season - 1]
	else:
		link = links[0]
	
	while "[e" in link:
		code = link.split("[e")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[e]", str(episode))
		else:
			signifier = "[e{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					episode = episode + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("+")]) + 1 - len(str(episode))) + str(episode))
				elif "-" in code:
					episode = episode - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("-")]) + 1 - len(str(episode))) + str(episode))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(episode))) + str(episode))
			elif code[0] == "+":
				link = link.replace(signifier, str(episode + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(episode + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(episode)
				if episode > 10 and episode < 20:
					mod += "th"
				else:
					if episode % 10 == 1:
						mod += "st"
					elif episode % 10 == 2:
						mod += "nd"
					elif episode % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[end]", mod)
	while "[te" in link:
		code = link.split("[te")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[te]", str(totalEpisode))
		else:
			signifier = "[te{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					totalEpisode = totalEpisode + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("+")]) + 1 - len(str(totalEpisode))) + str(totalEpisode))
				elif "-" in code:
					totalEpisode = totalEpisode - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("-")]) + 1 - len(str(totalEpisode))) + str(totalEpisode))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(totalEpisode))) + str(totalEpisode))
			elif code[0] == "+":
				link = link.replace(signifier, str(totalEpisode + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(totalEpisode + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(totalEpisode)
				if totalEpisode > 10 and totalEpisode < 20:
					mod += "th"
				else:
					if totalEpisode % 10 == 1:
						mod += "st"
					elif totalEpisode % 10 == 2:
						mod += "nd"
					elif totalEpisode % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[tend]", mod)
	while "[s" in link:
		code = link.split("[s")[1].split("]")[0]
		if len(code) == 0:
			link = link.replace("[s]", str(season))
		else:
			signifier = "[s{}]".format(code)
			if code[0] == "0":
				if "+" in code:
					season = season + int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("+")]) + 1 - len(str(season))) + str(season))
				elif "-" in code:
					season = season - int(code[code.index("+"):])
					link = link.replace(signifier, "0" * (len(code[:code.index("-")]) + 1 - len(str(season))) + str(season))
				else:
					link = link.replace(signifier, "0" * (len(code) + 1 - len(str(season))) + str(season))
			elif code[0] == "+":
				link = link.replace(signifier, str(season + int(code[1:])))
			elif code[0] == "-":
				link = link.replace(signifier, str(season + int(code[1:])))
			elif code[:2] == "nd":
				mod = str(season)
				if season > 10 and season < 20:
					mod += "th"
				else:
					if season % 10 == 1:
						mod += "st"
					elif season % 10 == 2:
						mod += "nd"
					elif season % 10 == 3:
						mod += "rd"
					else:
						mod += "th"
				link = link.replace("[snd]", mod)
	while "[b64]" in link:
		from base64 import b64encode
		code = link.split("[b64]")[1].split("[/b64]")[0]
		link = link.replace("[b64]{}[/b64]".format(code), b64encode(bytes(code, "UTF-8")).decode("utf-8").strip("="))
	
	# site = [x for x in sites if x.name == siteName][0]
	# if site.downloadable:
		# print(site.getDownloadLink(link))
	
	from webbrowser import open
	open(link)


def completeEpisode():
	currentShow.episodeProgress += 1
	currentShow.timeProgress = ""
	
	if currentShow.episodeProgress == 2 or currentShow.isComplete():
		sortData()
	setShow()


def deleteShow():
	confirmDelete = messagebox.askokcancel("Confirm deletion", "Are you sure you want to delete {0}?".format(currentShow.title))
	if confirmDelete:
		del data[currentShowNum]
		sortData()
		setShow(currentShowNum)


def starShow():
	currentShow.starred = not currentShow.starred
	sortData()
	setShow()


def discontinueShow():
	currentShow.discontinued = not currentShow.discontinued
	sortData()
	setShow()



# Menu bar def _______________________ MENU BAR:
def refreshImageCache():
	from shutil import rmtree
	global pictures
	
	try:
		rmtree(tempPath + "Images")
	except PermissionError:
		pass
		
	pictures = {}
	setShow(0)
	if showImageProgress:
		print()
	Thread(target=downloadImages, daemon=True).start()


def openPreferences():
	PreferencesWindow()


def importData():
	global data
	filename = askopenfilename(title = "Select file",filetypes = [("DAT files","*.dat")])
	if filename != "":
		importData = load(open(filename, "rb"))
		
		if importData[0].version < showVersion:
			for i in importData:
				data.append(Show(i.dump()))
		elif importData[0].version > showVersion:
			messagebox.showinfo("Import Data", "Please update app to import this database")
			return
		else:
			data += importData
		
		sortData()
		messagebox.showinfo("Imported Data", "Successfully imported {0} shows:\n  {1}".format(len(importData), "\n  ".join([x.title for x in importData])))


def exportData():
	for i in data:
		if i.isComplete():
			print(i.title)


root = Tk()
menuBar = Menu(root)

fileMenu = Menu(menuBar, tearoff=0)
fileMenu.add_command(label="Refresh Image Cache", command=refreshImageCache, accelerator="Ctrl+R")

fileMenu.add_separator()
fileMenu.add_command(label="Import", command=importData, accelerator="Ctrl+I")
fileMenu.add_command(label="Export", command=exportData, accelerator="Ctrl+E")
fileMenu.add_separator()

fileMenu.add_command(label="Preferences", command=openPreferences, accelerator="Ctrl+P")
fileMenu.add_command(label="Quit", command=root.quit, accelerator="Ctrl+W")
menuBar.add_cascade(label="File", menu=fileMenu)

root.config(menu=menuBar)



# Main window GUI def _____________ MAIN WINDOW GUI:
if darkMode:
	backgroundColor = "#000000"
	foregroundColor = "#ffffff"
	
	disabledColor = "#808080"
	
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
	
	disabledColor = "#808080"
	
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

bannerColor = "#00137F"

root.config(bg=backgroundColor)


showTitle = StringVar()
seasonProgress = StringVar()
episodeProgress = StringVar()
timeProgress = StringVar()
showList = StringVar()
newShowName = StringVar()

titleFont = font.Font(family='Times New Roman', size=24)
labelFont = font.Font(family='Times New Roman', size=16)
dataFont = font.Font(family='Courier New', size=15, weight="bold")


# Offline banner
banner = Frame(root, bg=bannerColor, cursor="hand2")

bannerText = Label(banner, text="You are offline, click to go online", bg=bannerColor, fg=foregroundColor, font=labelFont)
bannerText.grid(padx=2)


# Listbox
showListBox = Listbox(root, listvariable=showList, height=19, exportselection=False, bg=backgroundColor, highlightcolor=backgroundColor, highlightbackground=backgroundColor)
showListBox.bind("<<ListboxSelect>>", setShow)
showListBox.grid(column=0, row=1, sticky="nsew", rowspan=2)
showListBox.focus_set()

# Title
title = Label(root, textvariable=showTitle, font=titleFont, bg=backgroundColor)
title.grid(column=2, row=1, sticky="nw", columnspan=3)

# Picture
picture = Label(root, bg=backgroundColor)
picture.grid(column=2, row=2, sticky="nw", rowspan=2)

# All show information/buttons
dataFrame = Frame(root, bg=backgroundColor, padx=5)
dataFrame.grid(column=3, row=2, sticky="nw")
dataFrame.grid_columnconfigure(1, weight=1)

# Progress information
season = Label(dataFrame, textvariable=seasonProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor)
episode = Label(dataFrame, textvariable=episodeProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor, anchor="w")

# All time stuff
timeFrame = Frame(dataFrame, bg=backgroundColor)

timeLabel = Label(timeFrame, text="Time:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
timeLabel.grid(column=0, row=0, sticky="nsw")

timeData = Entry(timeFrame, textvariable=timeProgress, width=5, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
timeData.grid(column=1, row=0, sticky="nsw")
timeData.bind("<KeyRelease>",  changeTime)

# Open link button
linkButton = Button(dataFrame, text="Open link", command=openLink, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

# Complete episode button
completeButton = Button(dataFrame, text="Complete episode", command=completeEpisode, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

# Settings button
settingsButton = Button(dataFrame, text="Settings", command=lambda: SettingsWindow(), fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
settingsButton.grid(column=0, row=5, sticky="new", pady=2)

# Delete show button
deleteButton = Button(dataFrame, text="Delete show", command=deleteShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
deleteButton.grid(column=0, row=9, sticky="new", pady=2)

# Star/unstar button
starButton = Button(dataFrame, text="Star", command=starShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

# Discontinue/recontinue button
discontinueButton = Button(dataFrame, text="Discontinue", command=discontinueShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

# Add show button
addButton = Button(root, text="Add show", command=addShowButton, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
addButton.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=3, padx=3)

# Add show entry
addEntry = Entry(root, textvariable=newShowName, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
addEntrySelected = False
addEntry.bind("<Return>", submitAddEntry)
addEntry.bind("<Escape>", closeAddEntry)
addEntry.bind("<Enter>", lambda x: addEntryHovered(True))
addEntry.bind("<Leave>", lambda x: addEntryHovered(False))


# Sets progressbar style
if darkMode:
	style = ttk.Style()
	style.theme_use("clam")
	style.configure("TProgressbar", foreground="black", background="black", troughcolor="black")

addProgress = ttk.Progressbar(root, orient=HORIZONTAL, length=50, mode="indeterminate")


def showListBoxRight(x):
	timeData.focus_set()
	timeData.selection_from(0)
	timeData.selection_to(END)
	timeData.icursor(len(timeProgress.get()))
	root.after(1, showListBox.xview(0))
	return "break"

def showListBoxUp(x):
	showListBox.focus_set()
	setShow(currentShowNum - 1)

def showListBoxDown(x):
	showListBox.focus_set()
	setShow(currentShowNum + 1)

def timeDataLeft(x):
	if timeData.index(INSERT) == 0:
		showListBox.focus_set()

def hoverList(hover):
	global listHovered
	listHovered = hover

def mouseScroll(event):
	if not listHovered:
		if event.delta > 0:
			if currentShowNum > 0:
				setShow(currentShowNum - 1)
		else:
			if currentShowNum < len(data) - 1:
				setShow(currentShowNum + 1)


# Arrow keybinds
showListBox.bind("<Right>", showListBoxRight)
timeData.bind("<Left>", timeDataLeft)
timeData.bind("<Up>", showListBoxUp)
timeData.bind("<Down>", showListBoxDown)

# showListBox keybinds
showListBox.bind("<B1-Leave>", lambda x: "break")
showListBox.bind("<Delete>", lambda x: deleteShow())
showListBox.bind("<BackSpace>", lambda x: deleteShow())
showListBox.bind("<space>", lambda x: openLink())
showListBox.bind("<Return>", lambda x: completeEpisode())
listHovered = False
showListBox.bind("<Enter>", lambda x: hoverList(True))
showListBox.bind("<Leave>", lambda x: hoverList(False))

# Root keybinds
root.bind("<MouseWheel>", mouseScroll)
root.bind("<Escape>", lambda x: SettingsWindow())
root.bind("<Control-e>", lambda x: exportData())
root.bind("<Control-i>", lambda x: importData())
root.bind("<Control-n>", lambda x: addShowButton())
root.bind("<Control-p>", lambda x: openPreferences())
root.bind("<Control-r>", lambda x: refreshImageCache())
root.bind("<Control-w>", lambda x: root.quit())
root.title("Progress Tracker")
root.resizable(False, False)
root.grid_columnconfigure(3, weight=1)

# Starts application
if offline:
	goOffline()
	banner.grid(row=0, column=0, columnspan=3, sticky="new")
	banner.bind("<Button-1>", goOnline)

try:
	data = load(open(dataPath, "rb"))
	
	if data[0].version < showVersion:
		newData = []
		for i in data:
			newData.append(Show(i.dump()))
		data = newData
	elif data[0].version > showVersion:
		messagebox.showinfo("Error", "Please update app to use this database")
		exit()
	
	sortData()
except FileNotFoundError:
	data = []


for i in glob(tempPath + "Sites\*.site"):
	sites.append(Site(i))
sites = sorted(sites)
showLinkInfo = len(sites) > 0

setShow(currentShowNum)
Thread(target=downloadImages, daemon=True).start()
Thread(target=updateShows, daemon=True).start()
root.mainloop()
dump(data, open(dataPath, "wb"))
