# Simonomi's Progress Tracker v3.0
# Thank you to https://www.tvmaze.com/api
from tkinter import *
from tkinter import ttk, font, messagebox
from pathlib import Path
from PIL import Image, ImageTk
from zipfile import ZipFile
from threading import Thread
import os



# Edit this variable to change where Progress.zip is stored
dataPath = "{0}\\Dropbox\\".format(Path.home())
tempPath = "{0}\\AppData\\Roaming\\ProgressTracker\\".format(Path.home())

data = []
sites = []
pictures = {}
addingShows = 0
currentShow = None
currentShowNum = 0
errorUrl = "https://static.tvmaze.com/images/no-img/no-img-portrait-text.png"

# Optional toggles, should be bult-in later
showDownloadProgress = False
showUpdateProgress = False
browserTimeout = 15
hideBrowser = True
darkMode = True
slowMode = True
offline = False



class Show:
	def __init__(self, *args):
		if len(args) == 1:
			self.id = int(args[0])
			
			import json
			showDataDict = json.loads(getSourceCode("https://api.tvmaze.com/shows/{0}?embed=seasons".format(self.id)))
			
			seasons = []
			for i in showDataDict["_embedded"]["seasons"]:
				if i["premiereDate"] != None and hasPassed(i["premiereDate"]):
					if hasPassed(i["endDate"]):
						seasons.append(i["episodeOrder"])
					else:
						seasonEpisodes = getSourceCode("https://api.tvmaze.com/seasons/{0}/episodes".format(i["id"]))
						seasonEpisodesDict = json.loads(seasonEpisodes)
						for j in seasonEpisodesDict:
							if not hasPassed(j["airdate"]):
								seasons.append(int(j["number"]) - 1)
								break
			
			if None in seasons:
				episodeList = getSourceCode("https://api.tvmaze.com/shows/{0}/episodes".format(showDataDict["id"]))
				episodeListDict = json.loads(episodeList)

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
		else:
			self.title = str(args[0])
			self.imageLink = str(args[1])
			
			if type(args[2]) == str:
				self.episodeData = [int(x) for x in args[2].split("|")]
			else:
				self.episodeData = args[2]
			
			self.status = str(args[3])
			
			self.links = {}
			if args[4]:
				for i in str(args[4]).split("|"):
					self.links[i.split("\\n")[0]] = i.split("\\n")[1:]
			
			self.episodeProgress = int(args[5])
			self.timeProgress = str(args[6])
			self.originalTitle = str(args[7])
			
			if type(args[8]) == str:
				self.discontinued = args[8] == "True"
			else:
				self.discontinued = args[8]
			
			self.id = int(args[9])
			
			if type(args[10]) == str:
				self.autoMode = args[10] == "True"
			else:
				self.autoMode = args[10]
	
	
	def __str__(self):
		return self.title
	
	
	def __repr__(self):
		return "<Show \"{0}\">".format(self.title)
	
	
	def __lt__(self, other):
		return self.title < other.title
	
	
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


class Site:
	def __init__(self, name, priority, searchUrl, searchElement, searchAttribute, seasons, pageElement, pageAttribute, episodes, flipPageOrder, flipSeasonOrder):
		self.name = name
		self.priority = int(priority)
		self.searchUrl = searchUrl
		self.searchElement = searchElement
		self.searchAttribute = searchAttribute
		self.seasons = seasons == "True"
		self.pageElement = pageElement
		self.pageAttribute = pageAttribute
		self.episodes = episodes == "True"
		self.flipPageOrder = flipPageOrder == "True"
		self.flipSeasonOrder = flipSeasonOrder == "True"
	
	
	def __str__(self):
		return "<Site \"{}\">".format(self.name)
	
	
	def __lt__(self, other):
		return self.priority < other.priority
	
	
	def search(self, title, episodeData):
		seasons = getElementAttribute(self.searchUrl.format(title), self.searchElement, self.searchAttribute, self.seasons)
		
		if self.flipSeasonOrder:
			seasons.reverse()
		
		episodes = []
		for i in range(len(seasons[:len(episodeData)])):
			episodes.append(getElementAttribute(seasons[i], self.pageElement, self.pageAttribute, self.episodes))
			
			if self.flipPageOrder:
				episodes[-1].reverse()
			episodes[-1] = episodes[-1][:2]
		
		if episodes == []:
			return []
		
		if self.seasons:
			if self.episodes:
				seasonLinks = []
				
				for i in episodes:
					decoded = []
					decodedGroups = []
					for j in i:
						decoded.append(decodePart64(j))
						decodedGroups.append(getGroups(decoded[-1]))
					
					for i in range(len(decodedGroups[0])):
						if len(decodedGroups) == 1 or not decodedGroups[0][i] == decodedGroups[1][i]:
							start = decodedGroups[0][i][0]
							end = start + len(decodedGroups[0][i][1])
							number = decoded[0][start:end]
							
							seasonLinks.append(getNumberType(number, "e", 1).join([decoded[0][:start], decoded[0][end:]]))
							break
				
				out = []
				consider = []
				for i in seasonLinks:
					groups = getGroups(i)
					
					if groups == []:
						out.append(i)
					else:
						groups = (groups[0][0], getNumberType(groups[0][1], "s"))
						consider.append((i, groups))
				
				if consider:
					common = consider[0][1]
					commons = [consider[0][0]]
					for i in consider[1:]:
						if i[1] == common:
							commons.append(i[0])
						else:
							start = common[0]
							end = start + len(common[1]) - 2
							number = commons[0][start:end]
							out.append(getNumberType(number, "s").join([commons[0][:start], commons[0][end:]]))
							
							common = i[1]
							commons = [i[0]]
					
					start = common[0]
					end = start + len(common[1]) - 2
					number = commons[0][start:end]
					out.append(getNumberType(number, "s").join([commons[0][:start], commons[0][end:]]))
				
				return out
			else:
				out = []
				consider = []
				for i in episodes:
					groups = getGroups(i[0])
					
					if groups == []:
						out.append(i[0])
					else:
						groups = (groups[0][0], getNumberType(groups[0][1], "s"))
						consider.append((i[0], groups))
				
				common = consider[0][1]
				commons = [consider[0][0]]
				for i in consider[1:]:
					if i[1] == common:
						commons.append(i[0])
					else:
						start = common[0]
						end = start + len(common[1]) - 2
						number = commons[0][start:end]
						out.append(getNumberType(number, "s").join([commons[0][:start], commons[0][end:]]))
						
						common = i[1]
						commons = [i[0]]
				
				start = common[0]
				end = start + len(common[1]) - 2
				number = commons[0][start:end]
				out.append(getNumberType(number, "s").join([commons[0][:start], commons[0][end:]]))
				
				return out
		else:
			if self.episodes:
				decoded = []
				decodedGroups = []
				for i in episodes:
					for j in i:
						decoded.append(decodePart64(j))
						decodedGroups.append(getGroups(decoded[-1]))
				
				for i in range(len(decodedGroups[0])):
					if not decodedGroups[0][i] == decodedGroups[1][i]:
						start = decodedGroups[0][i][0]
						end = start + len(decodedGroups[0][i][1])
						number = decoded[0][start:end]
						
						return [getNumberType(number, "te", 1).join([decoded[0][:start], decoded[0][end:]])]
						break
			else:
				return [episodes[0][0]]



class ShowOptionsWindow:
	def __init__(self, search):
		global addingShows, pictures
		
		self.search = search
		
		showData = getSourceCode("https://api.tvmaze.com/search/shows?q={0}&embed=seasons".format(self.search))
		import json
		
		try:
			showDataDict = json.loads(showData)
		except json.decoder.JSONDecodeError:
			print("ERROR: Invalid search: {0}".format(self.search))
			return
		
		shows = []
		for i in [x["show"] for x in showDataDict]:
			try:
				shows.append([i["name"], int(i["id"]), i["image"]["medium"]])
			except TypeError:
				shows.append([i["name"], int(i["id"]), ""])
		
		if len(shows) == 1:
			show = Show(shows[0][1])
			
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
			skipIds = []
			for i in shows:
				imageFile = "{0}{1}.jpg".format(tempPath + "Images\\", i[1])
				Thread(target=lambda: downloadImage(i[2], imageFile), daemon=True).start()
				if i.pop(2) == "":
					skipIds.append(i[1])
			
			notDownloaded = True
			while notDownloaded:
				notDownloaded = False
				for i in [x for x in shows if x[1] not in skipIds]:
					imageDestination = "{0}{1}.jpg".format(tempPath + "Images\\", i[1])
					notDownloaded = notDownloaded or (not os.path.exists(imageDestination)) or os.path.getsize(imageDestination) == 0
			
			for i in shows:
				imageFile = "{0}{1}.jpg".format(tempPath + "Images\\", i[1])
				try:
					pictures[i[1]] = ImageTk.PhotoImage(Image.open(imageFile).resize((126, 177)))
				except:
					pictures[i[1]] = ImageTk.PhotoImage(Image.open("{0}error.jpg".format(tempPath + "Images\\")).resize((126, 177)))
			
			self.optionsMenu = Toplevel(root, bg=backgroundColor)
			self.optionsMenu.title("Search for \"{0}\"".format(search))
			self.optionsMenu.resizable(False, False)
			self.optionsMenu.focus_set()
			
			self.optionsMenu.bind("<Control-w>", lambda x: root.destroy())
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
				self.options.append(ShowOption(self, *i, x, y))
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
			addButton.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3, padx=3)
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
		self.showPhoto["image"] = pictures[self.id]
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
		self.window.bind("<Control-w>", lambda x: root.destroy())
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
		self.links = currentShow.links
		self.sites = [x.name for x in sites]
		
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
		linkFrame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=3)
		linkFrame.columnconfigure(1, weight=1)
		linkFrame.rowconfigure(1, weight=1)
		
		titleLabel = Label(titleFrame, text="Title:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		self.titleEntry = Entry(titleFrame, textvariable=self.titleVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor, width=len(self.titleVar.get()) + 1)
		idLabel = Label(titleFrame, text="(ID: {})".format(self.show.id), font=labelFont, fg=foregroundColor, bg=backgroundColor)
		progressLabel = Label(progressFrame, text="Episode Progress:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		progressEntry = Entry(progressFrame, textvariable=self.progressVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor, width=len(self.progressVar.get()) + 1)
		episodeDataLabel = Label(episodeDataFrame, text="Episode Data:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		self.episodeDataEntry = Entry(episodeDataFrame, textvariable=self.episodeDataVar, font=dataFont, fg=foregroundColor, bg=backgroundColor, disabledforeground=disabledColor, disabledbackground=backgroundColor, insertbackground=foregroundColor, width=len(self.episodeDataVar.get()) + 1)
		autoCheckbox = Checkbutton(episodeDataFrame, text="Auto", variable=self.autoVar, fg=foregroundColor, bg=backgroundColor, activeforeground=foregroundColor, activebackground=backgroundColor, selectcolor=backgroundColor, command=self.toggleAuto)
		if currentShow.autoMode:
			self.episodeDataEntry["state"] = DISABLED
		else:
			self.episodeDataEntry["state"] = NORMAL
		
		linksLabel = Label(linkFrame, text="Links:", font=labelFont, fg=foregroundColor, bg=backgroundColor)
		
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
		
		self.linkText = Text(linkFrame, bg=backgroundColor, fg=foregroundColor, font=dataFont, insertbackground=foregroundColor, width=30, height=5)
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
		self.resetTitleButton.grid(row=4, column=0, sticky="ew", padx=5, pady=3)
		resetLinkButton.grid(row=4, column=1, sticky="ew", padx=5, pady=3)
		
		self.titleEntry.bind("<Key>", self.updateSize)
		progressEntry.bind("<Key>", self.updateSize)
		self.episodeDataEntry.bind("<Key>", self.updateSize)
		self.linkText.bind("<Key>", self.textSize)
		self.linkText.bind("<Tab>", self.textTab)
	
	
	def resetTitle(self):
		self.titleVar.set(currentShow.originalTitle)
		self.titleEntry.selection_clear()
		self.titleEntry.icursor(END)
		self.titleEntry.focus_set()
	
	
	def resetLink(self):
		self.linkText.delete(0.0, END)
		self.linkText.insert(END, "\n".join(sites[self.linkSitesCombobox.current()].search(currentShow.title, currentShow.episodeData)))
		self.textSize()
	
	
	def updateSize(self, event):
		if event.char.lower() in "abcdefghijklmnopqrstuvwxyz" and not event.char.lower() == "":
			event.widget.config(width=len(event.widget.get()) + 2)
		elif event.keysym == "Delete" or event.keysym == "BackSpace":
			event.widget.config(width=len(event.widget.get()))
		else:
			event.widget.config(width=len(event.widget.get()) + 1)
	
	
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
			updateShow(currentShow)
			self.episodeDataVar.set(",".join([str(x) for x in self.show.episodeData]))
		else:
			self.episodeDataEntry["state"] = NORMAL
	
	
	def submit(self, x):
		currentShow.title = removeForbidden(self.titleVar.get())
		currentShow.episodeProgress = int(self.progressVar.get())
		currentShow.episodeData = [int(x) for x in self.episodeDataVar.get().split(",")]
		currentShow.autoMode = self.autoVar.get() == 1
		try:
			self.saveLinks()
		except:
			pass
		
		root.unbind("<FocusIn>")
		self.window.destroy()
		
		sortData()
		setShow()



# Simple functions def _______________SIMPLE FUNCTIONS:
def getSourceCode(url):
	try:
		import urllib.request, requests
		return requests.get(url).text
	except (urllib.error.URLError, requests.exceptions.SSLError, requests.exceptions.ConnectionError):
		# print("Error: no internet or invalid URL: {0}".format(url))
		goOffline()


def removeForbidden(string):
	return string.replace("|", "").encode("cp1252", "ignore").decode('cp1252')


# Takes in a date as "m-d-y"
def hasPassed(date):
	import datetime
	return (datetime.datetime.now() - datetime.datetime(int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2]))).days >= 0


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


def getElementAttribute(url, element, attribute, returnList=False):
	try:
		from lxml import etree
		import urllib.request, requests
		try:
			r = requests.get(url)
			html = r.text
		except requests.exceptions.SSLError:
			html = ""
		
		try:
			root = etree.HTML(html)
			
			if returnList:
				output = []
				for i in root.cssselect(element):
					output.append(i.get(attribute))
					if output[-1][0] == "/":
						output[-1] = "/".join(url.split("/")[:3]) + output[-1]
				
				return output
			else:
				output = root.cssselect(element)[0].get(attribute)
				
				if output[0] == "/":
					return ["/".join(url.split("/")[:3]) + output]
				return [output]
		except (IndexError, AttributeError):
			from selenium import webdriver
			from selenium.webdriver.support import expected_conditions as EC
			from selenium.webdriver.support.ui import WebDriverWait
			from selenium.webdriver.common.by import By
			from selenium.common.exceptions import TimeoutException
			
			options = webdriver.ChromeOptions()
			if hideBrowser:
				options.add_argument("--window-size=0,0")
				options.add_argument("--window-position=3000,3000")
			
			options.add_argument("--disable-blink-features=AutomationControlled")
			options.add_experimental_option("excludeSwitches", ["enable-automation"])
			options.add_experimental_option('useAutomationExtension', False)
			
			browser = webdriver.Chrome("C:\Program Files\ChromeDriver\chromedriver.exe", options=options)
			if hideBrowser:
				browser.minimize_window()
			
			browser.get(url)
			
			browser.execute_script("window.open('/');")
			if hideBrowser:
				browser.minimize_window()
			
			try:
				WebDriverWait(browser, browserTimeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "{0}[{1}]".format(element, attribute))))
			except TimeoutException:
				browser.quit()
				return []

			html = browser.page_source.encode("cp1252", "ignore").decode('cp1252')
			
			browser.quit()
			
			root = etree.HTML(html)
			
			if returnList:
				output = []
				for i in root.cssselect(element):
					output.append(i.get(attribute))
					if output[-1][0] == "/":
						output[-1] = "/".join(url.split("/")[:3]) + output[-1]
				
				return output
			else:
				output = root.cssselect(element)[0].get(attribute)
				
				if output[0] == "/":
					return ["/".join(url.split("/")[:3]) + output]
				return [output]
	except (urllib.error.URLError, requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
		# print("Error: no internet or invalid URL: {0}:\n\t{1}".format(url, e))
		goOffline()


def decodePart64(link):
	import base64
	
	alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	linkParts = []
	newLinkParts = []
	
	temp = ""
	for i in link:
		if i in alphabet:
			temp += i
		else:
			linkParts.append(temp)
			temp = ""
	linkParts.append(temp)
	
	for i in linkParts:
		try:
			code = i + (len(i) % 4 * "=")
			decoded = base64.b64decode(bytes(code, "UTF-8")).decode("utf-8")
			
			if decoded == decoded.encode("cp1252", "ignore").decode('cp1252'):
				newLinkParts.append(decoded)
			else:
				raise ValueError
		except:
			newLinkParts.append(i)
			pass

	for i in range(len(linkParts)):
		if newLinkParts[i] != linkParts[i]:
			link = link.replace(linkParts[i], "[b64]{}[/b64]".format(newLinkParts[i]))
	return link


def getGroups(link):
	digits = "0123456789"
	lastDigit = False
	currentGroup = ""
	digitGroups = []
	lastIndex = 0
	skip = False
	
	link = "/".join([len("*".join(link.split("/")[:3])) * "*", *link.split("/")[3:]])
	
	for i in link:
		if i == "[":
			skip = True
		elif i == "]":
			skip = False
		elif not skip:
			if i in digits:
				if lastDigit:
					currentGroup += i
				else:
					currentGroup = i
				lastDigit = True
			elif lastDigit:
				if currentGroup[-1] in "snrt":
					if currentGroup[-1] == "s" and i == "t":
						currentGroup += i
					elif currentGroup[-1] in "nr" and i == "d":
						currentGroup += i
					elif currentGroup[-1] in "t" and i == "h":
						currentGroup += i
					else:
						currentGroup = currentGroup[:-1]
					digitGroups.append((link.index(currentGroup, lastIndex), currentGroup))
					lastIndex = digitGroups[-1][0] + 1
					lastDigit = False
				else:
					if i == "s":
						currentGroup += i
					elif i == "n":
						currentGroup += i
					elif i == "r":
						currentGroup += i
					elif i == "t":
						currentGroup += i
					else:
						digitGroups.append((link.index(currentGroup, lastIndex), currentGroup))
						lastIndex = digitGroups[-1][0] + 1
						lastDigit = False
	if lastDigit:
		if currentGroup[-1] in "snrt":
			currentGroup = currentGroup[:-1]
		digitGroups.append((link.index(currentGroup, lastIndex), currentGroup))
		lastIndex = digitGroups[-1][0] + 1
	
	return digitGroups


def getNumberType(number, type, episode=None):
	if number[0] == "0":
		if episode:
			add = int(number) - episode
			if add > 0:
				return "[{0}{1}+{2}]".format((len(number) - 1) * "0", type, add)
			elif add == 0:
				return "[{0}{1}]".format((len(number) - 1) * "0", type)
			else:
				return "[{0}{1}{2}]".format((len(number) - 1) * "0", type, add)
			return "[{0}{1}]".format((len(number) - 1) * "0", type)
	elif number[-1] in "tdh":
		return "[{}nd]".format(type)
	else:
		if episode:
			add = int(number) - episode
			if add > 0:
				return "[{0}+{1}]".format(type, add)
			elif add == 0:
				return "[{}]".format(type)
			else:
				return "[{0}{1}]".format(type, add)
		else:
			return "[{}]".format(type)



# Unique functions def ______________UNIQUE FUNCTIONS:
def loadDataFromFile(filePath):
	global data
	if os.path.exists(filePath):
		with ZipFile(filePath, "r") as zip:
			for name in zip.namelist():
				showData = zip.read(name).decode("utf-8").replace("\r", "").split("\n")
				data.append(Show(".".join(name.split(".")[:-1]), *showData))
	
	sortData()
	setShow(currentShowNum)


def loadSites():
	global sites
	if not os.path.exists(tempPath + "Sites\\"):
		os.mkdir(tempPath + "Sites\\")
		return
	
	import glob
	for i in glob.glob(tempPath + "Sites\\*.site"):
		with open(i) as file:
			sites.append(Site(".".join(i.split("\\")[-1].split(".")[:-1]), *file.read().split("\n")))
	
	sites = sorted(sites)


def saveDataToFile(filePath):
	with ZipFile(filePath, "w") as zip:
		for i in data:
			output = ""
			output += i.imageLink + "\n"
			output += "|".join([str(x) for x in i.episodeData]) + "\n"
			output += i.status + "\n"
			
			links = []
			for j in i.links.items():
				links.append("\\n".join([j[0], *j[1]]))
			output += "|".join(links) + "\n"
			
			output += str(i.episodeProgress) + "\n"
			output += i.timeProgress + "\n"
			output += i.originalTitle + "\n"
			output += str(i.discontinued) + "\n"
			output += str(i.id) + "\n"
			output += str(i.autoMode) + "\n"
			
			zip.writestr(i.title + ".data", output)


def goOffline():
	global offline
	if not offline:
		print("Offline mode enabled")
	offline = True
	addButton["state"] = DISABLED


def sortData():
	global data
	
	data = sorted(data)
	complete = []
	discontinued = []
	watching = []
	toWatch = []
	
	for i in data:
		if i.isComplete():
			complete.append(i)
		elif i.discontinued:
			discontinued.append(i)
		elif i.episodeProgress != 1:
			watching.append(i)
		else:
			toWatch.append(i)
	
	data = [*watching, *toWatch, *complete, *discontinued]
	showList.set(data)
	
	finishedStart = len(watching) + len(toWatch)
	finishedEnd = len(watching) + len(toWatch) + len(complete)
	
	for i in range(0, len(data)):
		if i < len(watching):
			showListBox.itemconfigure(i, background=listBoxWatchingColor, foreground=listBoxWatchingTextColor)
		elif i >= finishedStart and i < finishedEnd:
			showListBox.itemconfigure(i, background=listBoxWatchedColor, foreground=listBoxWatchedTextColor)
		elif i >= finishedEnd:
			showListBox.itemconfigure(i, background=listBoxDiscontinuedColor, foreground=listBoxDiscontinuedTextColor)
		else:
			if i % 2 == 0:
				showListBox.itemconfigure(i, background=listBoxColor1, foreground=listBoxTextColor1)
			else:
				showListBox.itemconfigure(i, background=listBoxColor2, foreground=listBoxTextColor2)


def downloadImage(imageUrl, imageDestination):
	import urllib.request
	if not os.path.exists(tempPath + "Images\\"):
		os.mkdir(tempPath + "Images\\")
	
	if (not offline) and (((not os.path.exists(imageDestination)) or os.path.getsize(imageDestination) == 0) and imageUrl):
		try:
			urllib.request.urlretrieve(imageUrl, imageDestination)
		except:
			print(sys.exc_info())
			# print("Error: no internet or invalid URL: {0}".format(imageUrl))
			goOffline()
	
	if showDownloadProgress and not downloadProgress.value == downloadProgress.max_value:
		if downloadProgress.value == downloadProgress.max_value - 1:
			downloadProgress.finish()
		else:
			downloadProgress.update(downloadProgress.value + 1)


def downloadImages():
	if not os.path.exists(tempPath + "Images\\"):
		os.mkdir(tempPath + "Images\\")
	
	if showDownloadProgress:
		global downloadProgress
		import progressbar.bar
		downloadProgress = progressbar.bar.ProgressBar(0, len(data) + 1)
		downloadProgress.update(0)
	
	downloadImage(errorUrl, "{0}error.jpg".format(tempPath + "Images\\"))
	for i in data:
		imageUrl = i.imageLink
		imageFile = "{0}{1}.jpg".format(tempPath + "Images\\", i.id)
		Thread(target=lambda: downloadImage(imageUrl, imageFile), daemon=True).start()


def updateShow(show):
	if show.autoMode and show.status != "Ended" and (not offline):
		showData = getSourceCode("http://api.tvmaze.com/shows/{0}?embed=seasons".format(show.id))
		import json

		try:
			showDataDict = json.loads(showData)
		except json.decoder.JSONDecodeError:
			print("ERROR: Invalid show: {0}".format(repr(show)))
			return
		except TypeError:
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
					seasonEpisodesDict = json.loads(seasonEpisodes)
					for j in seasonEpisodesDict:
						if not hasPassed(j["airdate"]) and j["number"] != None:
							seasons.append(int(j["number"]) - 1)
							break
		
		if None in seasons:
			episodeList = getSourceCode("https://api.tvmaze.com/shows/{0}/episodes".format(show.id))
			try:
				episodeListDict = json.loads(episodeList)
			except TypeError:
				return
			
			episodes = []
			for i in range(0, len(episodeListDict)):
				episodes.append(episodeListDict[i]["season"])

			seasons = []
			for i in range(1, episodes[len(episodes) - 1] + 1):
				seasons.append(episodes.count(i))

		show.episodeData = seasons
	
	if showUpdateProgress and not updateProgress.value == updateProgress.max_value:
		if updateProgress.value == updateProgress.max_value - 1:
			updateProgress.finish()
		else:
			updateProgress.update(updateProgress.value + 1)


def updateShows():
	if showUpdateProgress:
		global updateProgress
		import progressbar.bar
		updateProgress = progressbar.bar.ProgressBar(0, len(data))
		updateProgress.update(0)
	
	if slowMode:
		for i in data:
			updateShow(i)
	else:
		for i in data:
			Thread(target=lambda: updateShow(i), daemon=True).start()


def setShow(show = None):
	global currentShow, currentShowNum, title, picture, image
	if type(show) == Event:
		currentShow = data[showListBox.curselection()[0]]
	elif type(show) == str:
		currentShow = data[[x.title for x in data].index(show)]
	elif type(show) == int:
		currentShow = data[show]
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
	
	if currentShow.id == "":
		imagePath = "{0}error.jpg".format(tempPath + "Images\\")
		image = ImageTk.PhotoImage(Image.open(imagePath).resize((210, 295)))
	else:
		imagePath = "{0}{1}.jpg".format(tempPath + "Images\\", currentShow.id)
		try:
			image = ImageTk.PhotoImage(Image.open(imagePath).resize((210, 295)))
		except:
			if not os.path.exists(tempPath + "Images\\"):
				os.mkdir(tempPath + "Images\\")
			try:
				# urllib.request.urlretrieve(currentShow.imageLink, imagePath)
				print("DOWNLOAD THE IMAGE DUMBF")
			except urllib.error.URLError:
				goOffline()
			image = ImageTk.PhotoImage(Image.open(imagePath).resize((210, 295)))
	picture["image"] = image
	
	if currentShow.discontinued:
		seasonProgress.set("Discontinued")
		season.grid(column=0, row=0, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		discontinueButton.grid(column=0, row=7, sticky="new", pady=2)
		discontinueButton.config(text="Recontinue")
	elif currentShow.isComplete():
		seasonProgress.set("Finished")
		season.grid(column=0, row=0, sticky="nw", pady=2)
		episode.grid_forget()
		timeFrame.grid_forget()
		linkButton.grid_forget()
		completeButton.grid_forget()
		discontinueButton.grid_forget()
	else:
		seas, epi, seasMax, epiMax = currentShow.getSeasonEpisode()
		episodeProgress.set("Episode {0}/{1}".format(epi, epiMax))
		timeProgress.set(currentShow.timeProgress)
		
		if seasMax == 1:
			season.grid_forget()
		else:
			seasonProgress.set("Season {0}/{1}".format(seas, seasMax))
			season.grid(column=0, row=0, sticky="nw", pady=2)
		
		episode.grid(column=0, row=1, sticky="nw", pady=2)
		timeFrame.grid(column=0, row=2, sticky="nw", pady=2)
		
		linkButton.grid(column=0, row=3, sticky="new", pady=2)
		if currentShow.links:
			linkButton["state"] = NORMAL
		else:
			linkButton["state"] = DISABLED
		
		completeButton.grid(column=0, row=4, sticky="new", pady=2)
		
		discontinueButton.grid(column=0, row=7, sticky="new", pady=2)
		discontinueButton.config(text="Discontinue")



# Main window commands def ____MAIN WINDOW COMMANDS:
def addShowButton():
	newShowName.set("")
	addEntry.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3, padx=3)
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
	addButton.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3, padx=3)
	addEntry.grid_forget()
	showListBox.focus_set()
	root.unbind("<Button-1>")


def submitAddEntry(x):
	global addingShows
	
	settingsButton['state'] = DISABLED
	addEntry.grid_forget()
	addProgress.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3)
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
	
	for i in sites:
		if i.name in currentShow.links:
			links = currentShow.links[i.name]
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
		import base64
		code = link.split("[b64]")[1].split("[/b64]")[0]
		link = link.replace("[b64]{}[/b64]".format(code), base64.b64encode(bytes(code, "UTF-8")).decode("utf-8").strip("="))
	
	import webbrowser
	if "soap2day" in link:
		webbrowser.open(geElementAttribute(link, "#player > div.jw-media.jw-reset > video", "src")[0])
	else:
		webbrowser.open(link)


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


def discontinueShow():
	currentShow.discontinued = not currentShow.discontinued
	sortData()
	setShow()



# Menu bar def _______________________ MENU BAR:
def refreshImageCache():
	import shutil
	shutil.rmtree(tempPath + "Images")
	print()
	Thread(target=downloadImages, daemon=True).start()


def openPreferences():
	print("Preferences")


def importData():
	print("Import data")


def exportData():
	print("Export data")
	# for i in data:
		# if i.isComplete():
			# print(i)


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

titleFont = font.Font(family='Times New Roman', size=24)
labelFont = font.Font(family='Times New Roman', size=16)
dataFont = font.Font(family='Courier New', size=15, weight="bold")


# Listbox
showListBox = Listbox(root, listvariable=showList, height=19, exportselection=False, bg=backgroundColor, highlightcolor=backgroundColor, highlightbackground=backgroundColor)
showListBox.bind("<<ListboxSelect>>", setShow)
showListBox.grid(column=0, row=0, sticky="nsew", rowspan=2)
showListBox.focus_set()

# Title
title = Label(root, textvariable=showTitle, font=titleFont, bg=backgroundColor)
title.grid(column=2, row=0, sticky="nw", columnspan=3)

# Picture
picture = Label(root, bg=backgroundColor)
picture.grid(column=2, row=1, sticky="nw", rowspan=2)

# All show information/buttons
dataFrame = Frame(root, bg=backgroundColor, padx=5)
dataFrame.grid(column=3, row=1, sticky="nw")

# Progress information
season = Label(dataFrame, textvariable=seasonProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor)
episode = Label(dataFrame, textvariable=episodeProgress, font=labelFont, fg=foregroundColor, bg=backgroundColor)

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
deleteButton.grid(column=0, row=6, sticky="new", pady=2)

# Discontinue/recontinue button
discontinueButton = Button(dataFrame, text="Discontinue", command=discontinueShow, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)

# Add show button
addButton = Button(root, text="Add show", command=addShowButton, fg=foregroundColor, bg=backgroundColor, activebackground=buttonPressedColor, activeforeground=buttonPressedTextColor)
addButton.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=3, padx=3)

# Add show entry
addEntry = Entry(root, textvariable=newShowName, fg=foregroundColor, bg=backgroundColor, insertbackground=foregroundColor)
addEntrySelected = False
addEntry.bind("<Return>", submitAddEntry)
addEntry.bind("<Escape>", closeAddEntry)
addEntry.bind("<Enter>", lambda x: addEntryHovered(True))
addEntry.bind("<Leave>", lambda x: addEntryHovered(False))


# Dark mode style
style = ttk.Style()
style.theme_use("clam")
style.configure("My.Horizontal.TProgressbar", foreground="black", background="black", troughcolor="black")

# Sets progressbar style
if darkMode:
	addProgress = ttk.Progressbar(root, orient=HORIZONTAL, length=50, mode="indeterminate", style="My.Horizontal.TProgressbar")
else:
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


# Arrow keybinds
showListBox.bind("<Right>", showListBoxRight)
timeData.bind("<Left>", timeDataLeft)
timeData.bind("<Up>", showListBoxUp)
timeData.bind("<Down>", showListBoxDown)

# showListBox keybinds
showListBox.bind("<B1-Leave>", lambda x: "break")
showListBox.bind("<Delete>", lambda x: deleteShow())
showListBox.bind("<BackSpace>", lambda x: deleteShow())

# Root keybinds
root.bind("<space>", lambda x: openLink())
root.bind("<Return>", lambda x: completeEpisode())
root.bind("<Escape>", lambda x: SettingsWindow())
root.bind("<Control-e>", lambda x: exportData())
root.bind("<Control-i>", lambda x: importData())
root.bind("<Control-n>", lambda x: addShowButton())
root.bind("<Control-p>", lambda x: openPreferences())
root.bind("<Control-r>", lambda x: refreshImageCache())
root.bind("<Control-w>", lambda x: root.quit())
root.title("Progress Tracker")
root.resizable(False, False)
root.grid_columnconfigure(4, weight=1)

# Starts application
if offline:
	goOffline()
loadDataFromFile("{0}Progress.zip".format(dataPath))
loadSites()
Thread(target=downloadImages, daemon=True).start()
Thread(target=updateShows, daemon=True).start()
root.mainloop()
saveDataToFile("{0}Progress.zip".format(dataPath))
