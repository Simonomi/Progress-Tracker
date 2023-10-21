import tkinter as tk
from tkinter import ttk, messagebox
from common import *
from database import *
from PIL import Image, ImageTk
from pathlib import Path
from glob import glob
from threading import Thread
from os import path, remove, mkdir
import urllib
import urllib.request
import urllib.error


errorUrl = "https://static.tvmaze.com/images/no-img/no-img-portrait-text.png"


class MainWindow(tk.Tk):
	def __init__(self, database, **kwargs):
		super().__init__()
		
		self.setOptions(kwargs)
		self.database = database
		
		self.title("Movie Tracker")
		self.resizable(False, False)
		self.columnconfigure(3, weight=1)
		self.rowconfigure(2, weight=1)
		
		self.style()
		
		# menu bar
		# self.overrideredirect(True)
		
		# left pane
		# self.banner = ttk.Frame(self, style="Banner.TFrame", cursor="hand2")
		# banner.bind("<Button-1>", self.goOnline)
		
		# self.bannerText = ttk.Label(self.banner, text="You are offline, click to go online", style="Banner.TLabel")
		# self.bannerText.grid(padx=2)
		
		self.itemList = tk.StringVar()
		self.itemListBox = tk.Listbox(self, listvariable=self.itemList, height=20, width=20, font=("Times New Roman", 10), fg=self.fg, bg=self.bg,  highlightcolor=self.highlightcolor, highlightbackground=self.highlightbackground, selectbackground=self.selectbackground, exportselection=False)
		self.itemListBox.grid(row=1, column=0, rowspan=2, sticky="ew")
		self.itemListBox.bind("<<ListboxSelect>>", self.setView)
		self.itemListBox.bind("<B1-Leave>", lambda x: "break")
		self.itemListBox.bind("<Right>", self.itemListBoxRight)
		self.itemListBox.bind("<space>", self.openLink)
		
		self.scrollbar = ttk.Scrollbar(self, command=self.itemListBox.yview)
		self.itemListBox.configure(yscrollcommand=self.scrollbar.set)
		self.scrollbar.grid(row=1, column=1, rowspan=2, padx=(2, 0), sticky="nsw")
		
		self.itemTitle = ttk.Label(self, style="Title.TLabel")
		self.itemTitle.grid(row=1, column=2, columnspan=3, sticky="nw", padx=3)
		
		self.picture = ttk.Label(self)
		self.picture.grid(row=2, column=2, rowspan=2, sticky="nw")
		
		self.addButton = ttk.Button(self, text="Add", command=self.addItem)
		self.addButton.grid(row=3, column=0, columnspan=2, pady=2, sticky="ew")
		
		self.addEntry = ttk.Entry(self, width=10, font=("Courier New", 15, "bold"))
		self.addEntry.bind("<Return>", self.submitAddEntry)
		self.addEntry.bind("<Escape>", lambda x: self.closeAddEntry())
		
		
		# shows
		self.showDataFrame = ttk.Frame(self)
		
		self.showSeason = ttk.Label(self.showDataFrame)
		self.showSeason.grid(row=0, column=0, columnspan=2, sticky="w")
		
		self.showEpisode = ttk.Label(self.showDataFrame)
		
		self.showTimeLabel = ttk.Label(self.showDataFrame, text="Time:")
		
		self.showTimeEntry = ttk.Entry(self.showDataFrame, width=5, font=("Courier New", 15, "bold"))
		self.showTimeEntry.bind("<KeyRelease>", self.updateTime)
		self.showTimeEntry.bind("<Left>", lambda x: self.itemListBox.focus_set())
		
		self.showOpenLinkButton = ttk.Button(self.showDataFrame, text="Open link", command=self.openLink)
		
		self.showCompleteEpisodeButton = ttk.Button(self.showDataFrame, text="Complete Episode", command=self.complete)
		
		self.showSettingsButton = ttk.Button(self.showDataFrame, text="Settings", command=self.settings)
		self.showSettingsButton.grid(row=6, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.showStarButton = ttk.Button(self.showDataFrame, text="Star", command=self.star)
		self.showStarButton.grid(row=5, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.showDiscontinueButton = ttk.Button(self.showDataFrame, text="Discontinue", command=self.discontinue)
		self.showDiscontinueButton.grid(row=7, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.showDeleteButton = ttk.Button(self.showDataFrame, text="Delete", command=self.deleteItem)
		self.showDeleteButton.grid(row=8, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		
		# movies
		self.movieDataFrame = ttk.Frame(self)
		
		self.movieCompleteButton = ttk.Checkbutton(self.movieDataFrame, text="Complete", command=self.complete)
		
		self.movieTimeLabel = ttk.Label(self.movieDataFrame, text="Time:")
		self.movieTimeLabel.grid(row=1, column=0, sticky="nsw", pady=2)
		
		self.movieTimeEntry = ttk.Entry(self.movieDataFrame, width=5, font=("Courier New", 15, "bold"))
		self.movieTimeEntry.grid(row=1, column=1, sticky="nsw", padx=3, pady=2)
		self.movieTimeEntry.bind("<KeyRelease>", self.updateTime)
		self.movieTimeEntry.bind("<Left>", lambda x: self.itemListBox.focus_set())
		
		self.movieOpenLinkButton = ttk.Button(self.movieDataFrame, text="Open link")
		
		self.movieSettingsButton = ttk.Button(self.movieDataFrame, text="Settings", command=self.settings)
		self.movieSettingsButton.grid(row=4, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.movieStarButton = ttk.Button(self.movieDataFrame, text="Star", command=self.star)
		self.movieStarButton.grid(row=3, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.movieDiscontinueButton = ttk.Button(self.movieDataFrame, text="Discontinue", command=self.discontinue)
		self.movieDiscontinueButton.grid(row=5, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.movieDeleteButton = ttk.Button(self.movieDataFrame, text="Delete", command=self.deleteItem)
		self.movieDeleteButton.grid(row=6, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		
		# collections
		self.collectionDataFrame = ttk.Frame(self)
		
		self.collectionStarButton = ttk.Button(self.collectionDataFrame, text="Star", command=self.star)
		self.collectionStarButton.grid(row=0, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.collectionSettingsButton = ttk.Button(self.collectionDataFrame, text="Settings", command=self.settings)
		self.collectionSettingsButton.grid(row=1, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.collectionDiscontinueButton = ttk.Button(self.collectionDataFrame, text="Discontinue", command=self.discontinue)
		self.collectionDiscontinueButton.grid(row=2, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		self.collectionDeleteButton = ttk.Button(self.collectionDataFrame, text="Delete", command=self.deleteItem)
		self.collectionDeleteButton.grid(row=3, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
		
		
		self.itemListBox.focus_set()
		
		self.bind("<MouseWheel>", self.mouseScroll)
		self.bind("<Escape>", self.settings)
		self.bind("<Return>", self.complete)
		self.bind("<Delete>", self.deleteItem)
		self.bind("<BackSpace>", self.deleteItem)
		self.bind("<Control-e>", self.exportData)
		# self.bind("<Control-i>", importData())
		self.bind("<Control-n>", lambda x: self.addItem())
		# self.bind("<Control-p>", openPreferences())
		# self.bind("<Control-r>", refreshImageCache())
		self.bind("<Up>", self.itemListBoxUp)
		self.bind("<Down>", self.itemListBoxDown)
		self.bind("<Control-w>", lambda x: self.quit())
		
		
		imageDestination = self.tempPath + "loading.jpg"
		if not (path.exists(imageDestination) and path.getsize(imageDestination) != 0):
			urllib.request.urlretrieve(errorUrl, imageDestination)
		self.pictures = {"loading": ImageTk.PhotoImage(Image.open(self.tempPath + "loading.jpg").resize((210, 295)))}
		
		# Thread(target=lambda: self.database.update(self), daemon=True).start()
		
		self.setList()
		self.setView()
		self.mainloop()
	
	
	def setOptions(self, options):
		if "apiKey" in options.keys():
			self.apiKey = options["apiKey"]
		else:
			raise NameError("Missing api key")
		
		if "darkMode" in options.keys():
			self.darkMode = options["darkMode"]
		else:
			self.darkMode = False
		
		if "tempPath" in options.keys():
			self.tempPath = options["tempPath"].format(Path.home())
		else:
			self.tempPath = "{}\\AppData\\Roaming\\ProgressTracker\\".format(Path.home())
		
		if not path.exists(self.tempPath):
			mkdir(self.tempPath)
		
		if "sitesFolder" in options.keys():
			sitesFolder = options["sitesFolder"].format(Path.home())
		else:
			sitesFolder = self.tempPath + "Sites\\"
		
		self.sites = []
		for i in glob("{}*.site".format(sitesFolder)):
			self.sites.append(Site(i))
		self.sites.sort()
	
	
	def style(self):
		style = ttk.Style()
		
		if self.darkMode:
			self.configure(background="black")
			style.theme_use("clam")
			
			style.configure(".", font=("Times New Roman", 16), foreground="white", background="black", lightcolor="grey", fieldbackground="black", selectbackground="grey", arrowcolor="white", arrowsize=15, insertcolor="white")
			
			style.configure("Banner.TFrame", background="#00137F")
			style.configure("Banner.TLabel", font=("Times New Roman", 16), background="#00137F")
			style.configure("Option.TLabel", font=("Times New Roman", 12), anchor="center", justify="center")
			style.configure("Title.TLabel", font=("Times New Roman", 24))
			style.configure("Heading.TLabel", font=("Times New Roman", 20))
			
			style.configure("TButton", font=("Times New Roman", 12))
			style.configure("Vertical.TScrollbar", troughcolor="black", background="black")
			style.configure("Horizontal.TProgressbar", troughcolor="black", background="black")
			style.configure("TCheckbutton", indicatorbackground="black", indicatorforeground="white")

			style.map(".",
				foreground=[
					("active", "white"),
					("disabled", "grey")],
				background=[
					("pressed", "#151515"),
					("active", "#252525"),
					("focus", "#252525")],
				fieldbackground=[
					("pressed", "#151515"),
					("active", "#252525"),
					("focus", "#252525")])
			
			style.map("TButton",
				background=[
					("pressed", "#202020"),
					("active", "#252525"),
					("focus", "#252525")],
				foreground=[
					("disabled", "#757575")])
			style.map("TEntry",
				bordercolor=[("focus", "grey")],
				lightcolor=[("focus", "grey")],
				fieldbackground=[("focus", "#252525")])
			style.map("TCheckbutton",
				indicatorbackground=[("pressed", "black")])
			style.map("TCombobox",
				background=[
					("active", "#252525"),
					("focus", "#252525")],
				fieldbackground=[("focus", "#252525")],
				selectbackground=[
					("focus", "#252525"),
					("readonly", "black")],
				selectforeground=[("readonly", "white")])
			
			
			self.fg = "white"
			self.bg = "black"
			self.selectbackground = "#303030"
			self.highlightcolor = "grey"
			self.highlightbackground = "grey"
			
			self.watchingColor = "#fffd96"
			self.watchingForegroundColor = "#fffd96"
			self.watchingBackgroundColor = "black"
			
			self.towatchColor = "white"
			self.towatchForegroundColor = "white"
			self.towatchBackgroundColor = "black"
			
			self.completeColor = "#c8ffc8"
			self.completeForegroundColor = "#c8ffc8"
			self.completeBackgroundColor = "black"
			
			self.discontinuedColor = "#ff9696"
			self.discontinuedForegroundColor = "#ff9696"
			self.discontinuedBackgroundColor = "black"
			
			self.unknownProgressColor = "#fffd96"
			self.runningProgressColor = "#c8ffc8"
			self.endedProgressColor = "#ff9696"
		else:
			style.configure(".", font=("Times New Roman", 16))
			
			style.configure("Banner.TLabel", font=("Times New Roman", 16), background="#00137F")
			style.configure("Option.TLabel", font=("Times New Roman", 12), anchor="center", justify="center")
			style.configure("TButton", font=("Times New Roman", 12))
			style.configure("Title.TLabel", font=("Times New Roman", 24))
			style.configure("Heading.TLabel", font=("Times New Roman", 20))
			
			
			self.fg = "black"
			self.bg = "#f0f0f0"
			self.selectbackground = "#0078d7"
			self.highlightcolor = "grey"
			self.highlightbackground = "grey"
			
			self.watchingColor = "#fffd96"
			self.watchingForegroundColor = "black"
			self.watchingBackgroundColor = "#fffd96"
			
			self.towatchColor = "white"
			self.towatchForegroundColor = "black"
			self.towatchBackgroundColor = "white"
			
			self.completeColor = "#c8ffc8"
			self.completeForegroundColor = "black"
			self.completeBackgroundColor = "#c8ffc8"
			
			self.discontinuedColor = "#ff9696"
			self.discontinuedForegroundColor = "black"
			self.discontinuedBackgroundColor = "#ff9696"
			
			self.runningProgressColor = "#008000"
			self.endedProgressColor = "#800000"
			self.unknownProgressColor = "#807d00"
	
	
	def setList(self):
		self.database.sort()
		self.itemList.set(self.database)
		
		for i in range(len(self.database)):
			if self.database[i].isComplete():
				self.itemListBox.itemconfigure(i, fg=self.completeForegroundColor, bg=self.completeBackgroundColor, selectforeground=self.completeColor)
			elif self.database[i].discontinued:
				self.itemListBox.itemconfigure(i, fg=self.discontinuedForegroundColor, bg=self.discontinuedBackgroundColor, selectforeground=self.discontinuedColor)
			elif self.database[i].isWatching():
				self.itemListBox.itemconfigure(i, fg=self.watchingForegroundColor, bg=self.watchingBackgroundColor, selectforeground=self.watchingColor)
			else:
				self.itemListBox.itemconfigure(i, fg=self.towatchForegroundColor, bg=self.towatchBackgroundColor, selectforeground=self.towatchColor)
			
			if type(self.database[i]) == Movie:
				from datetime import datetime
				if self.database[i].year > datetime.now().year:
					self.itemListBox.itemconfigure(i, fg="grey", selectforeground="grey")
	
	
	def setView(self, item=0):
		if not len(self.database):
			self.currentItem = None
			self.currentItemNum = 0
			
			self.picture.config(image="")
			self.itemTitle.config(text="")
			
			self.showDataFrame.grid_forget()
			self.collectionDataFrame.grid_forget()
			self.movieDataFrame.grid_forget()
			return
		
		if type(item) == int:
			self.currentItemNum = item
		elif type(item) == tk.Event:
			self.currentItemNum = self.itemListBox.curselection()[0]
		else:
			self.currentItemNum = self.database.index(item)
		
		self.currentItem = self.database[self.currentItemNum]
		
		
		# title color
		self.itemTitle.config(text=str(self.currentItem).strip())
		style = ttk.Style()
		if type(self.currentItem) == Show:
			if self.currentItem.status == "Running":
				style.configure("Title.TLabel", foreground=self.runningProgressColor)
			elif self.currentItem.status == "Ended":
				style.configure("Title.TLabel", foreground=self.endedProgressColor)
			else:
				style.configure("Title.TLabel", foreground=self.unknownProgressColor)
		else:
			from datetime import datetime
			if self.currentItem.year > datetime.now().year:
				style.configure("Title.TLabel", foreground="grey")
			else:
				style.configure("Title.TLabel", foreground=self.endedProgressColor)
		
		
		# picture
		key = "{} {}".format(type(self.currentItem).__name__, self.currentItem.id)
		if key in self.pictures:
			self.picture.config(image=self.pictures[key])
		else:
			self.picture.config(image=self.pictures["loading"])
			Thread(target=self.downloadImage, daemon=True).start()
		
		
		# right pane
		if type(self.currentItem) == Show:
			self.showDataFrame.grid(row=2, column=3,
				rowspan=2, sticky="nw", padx=3)
			self.collectionDataFrame.grid_forget()
			self.movieDataFrame.grid_forget()
			
			if self.currentItem.starred:
				self.showStarButton.config(text="Unstar")
			else:
				self.showStarButton.config(text="Star")
			
			if self.currentItem.discontinued:
				self.showDiscontinueButton.config(text="Recontinue")
			else:
				self.showDiscontinueButton.config(text="Discontinue")
			
			
			if self.currentItem.isComplete():
				self.showSeason.config(text="Complete")
				
				self.showEpisode.grid_forget()
				self.showTimeLabel.grid_forget()
				self.showTimeEntry.grid_forget()
				self.showOpenLinkButton.grid_forget()
				self.showCompleteEpisodeButton.grid_forget()
			elif self.currentItem.discontinued:
				self.showSeason.config(text="Discontinued")
				
				self.showEpisode.grid_forget()
				self.showTimeLabel.grid_forget()
				self.showTimeEntry.grid_forget()
				self.showOpenLinkButton.grid_forget()
				self.showCompleteEpisodeButton.grid_forget()
			else:
				self.showTimeEntry.delete(0, "end")
				self.showTimeEntry.insert(0, self.currentItem.timeProgress)
				
				if len(set(list(self.currentItem.links.keys())) &
						set([x.name for x in self.sites])):
					self.showOpenLinkButton.state(["!disabled"])
				else:
					self.showOpenLinkButton.state(["disabled"])
				
				self.showEpisode.grid(row=1, column=0, columnspan=2, sticky="w")
				self.showTimeLabel.grid(row=2, column=0, sticky="nsw", pady=2)
				self.showTimeEntry.grid(row=2, column=1,
					sticky="nsw", padx=3, pady=2)
				self.showOpenLinkButton.grid(row=3, column=0,
					columnspan=2, padx=3, pady=2, sticky="ew")
				self.showCompleteEpisodeButton.grid(row=4, column=0,
					columnspan=2, padx=3, pady=2, sticky="ew")
				
				if self.currentItem.getMaxSeasons() == 1:
					self.showSeason.config(text="Season 1")
				else:
					self.showSeason.config(text="Season {}/{}".format(
						self.currentItem.getSeason(),
						self.currentItem.getMaxSeasons()))
				
				self.showEpisode.config(text="Episode {}/{}".format(
					self.currentItem.getEpisode(),
					self.currentItem.getMaxEpisodes()))
		elif type(self.currentItem) == Collection:
			self.collectionDataFrame.grid(row=2, column=3,
				rowspan=2, sticky="nw", padx=3)
			self.showDataFrame.grid_forget()
			self.movieDataFrame.grid_forget()
			
			if self.currentItem.starred:
				self.collectionStarButton.config(text="Unstar")
			else:
				self.collectionStarButton.config(text="Star")
			
			if self.currentItem.discontinued:
				self.collectionDiscontinueButton.config(text="Recontinue")
			else:
				self.collectionDiscontinueButton.config(text="Discontinue")
		else:
			self.movieDataFrame.grid(row=2, column=3,
				rowspan=2, sticky="nw", padx=3)
			self.showDataFrame.grid_forget()
			self.collectionDataFrame.grid_forget()
			
			if self.currentItem.isComplete():
				self.movieCompleteButton.state(['selected'])
			else:
				self.movieCompleteButton.state(['!selected'])
			
			if self.currentItem.starred:
				self.movieStarButton.config(text="Unstar")
			else:
				self.movieStarButton.config(text="Star")
			
			if self.currentItem.isComplete():
				self.movieDiscontinueButton.config(text="Discontinue")
				
				self.movieCompleteButton.grid(row=0, column=0,
					columnspan=2, padx=3, pady=2, sticky="ew")
				
				self.movieTimeLabel.grid_forget()
				self.movieTimeEntry.grid_forget()
				self.movieOpenLinkButton.grid_forget()
			elif self.currentItem.discontinued:
				self.movieDiscontinueButton.config(text="Recontinue")
				
				self.movieCompleteButton.grid_forget()
				self.movieTimeLabel.grid_forget()
				self.movieTimeEntry.grid_forget()
				self.movieOpenLinkButton.grid_forget()
			else:
				self.movieDiscontinueButton.config(text="Discontinue")
				
				self.movieTimeEntry.delete(0, "end")
				self.movieTimeEntry.insert(0, self.currentItem.timeProgress)
				
				if len(set(list(self.currentItem.links.keys())) &
						set([x.name for x in self.sites])):
					self.movieOpenLinkButton.state(["!disabled"])
				else:
					self.movieOpenLinkButton.state(["disabled"])
				
				self.movieCompleteButton.grid(row=0, column=0,
					columnspan=2, padx=3, pady=2, sticky="ew")
				self.movieTimeLabel.grid(row=1, column=0, sticky="nsw", pady=2)
				self.movieTimeEntry.grid(row=1, column=1,
					sticky="nsw", padx=3, pady=2)
				self.movieOpenLinkButton.grid(row=2, column=0,
					columnspan=2, padx=3, pady=2, sticky="ew")
		
		
		# left pane
		self.itemListBox.selection_clear(0, "end")
		self.itemListBox.selection_set(self.currentItemNum)
		self.itemListBox.activate(self.currentItemNum)
		self.itemListBox.see(self.currentItemNum)
	
	
	def downloadImage(self, item=None):
		if not path.exists(self.tempPath + "Images\\"):
			mkdir(self.tempPath + "Images\\")
		
		if not item:
			item = self.currentItem
		
		key = "{} {}".format(type(item).__name__, item.id)
		if key in self.pictures:
			return
		
		# set imageDestination
		if not item.imageLink:
			imageDestination = self.tempPath + "error.jpg"
			
			if not (path.exists(imageDestination) and
					path.getsize(imageDestination) != 0):
				urllib.request.urlretrieve(errorUrl, imageDestination)
		else:
			imageDestination = "{}{}.jpg".format(self.tempPath + "Images\\", key)
		
		
		# download imageDestination
		if not (path.exists(imageDestination) and
				path.getsize(imageDestination) != 0):
			try:
				urllib.request.urlretrieve(item.imageLink, imageDestination)
			except urllib.error.URLError:
				# print("offline")
				return
		
		# set pictures key to image
		if path.exists(imageDestination) and path.getsize(imageDestination) != 0:
			try:
				self.pictures[key] = ImageTk.PhotoImage(Image.open(imageDestination).resize((210, 295)))
			except OSError:
				remove(imageDestination)
				return
			
			if item is self.currentItem:
				self.picture.configure(image=self.pictures[key])
	
	
	def itemListBoxUp(self, event):
		if event.widget != self.itemListBox:
			self.itemListBox.focus_set()
			if self.currentItemNum > 0:
				self.setView(self.currentItemNum - 1)
	
	
	def itemListBoxDown(self, event):
		if event.widget != self.itemListBox:
			self.itemListBox.focus_set()
			if self.currentItemNum < len(self.database) - 1:
				self.setView(self.currentItemNum + 1)
	
	
	def itemListBoxRight(self, event):
		if type(self.currentItem) == Show:
			self.showTimeEntry.focus_set()
			self.showTimeEntry.select_range(0, "end")
			self.showTimeEntry.icursor("end")
		elif type(self.currentItem) == Movie:
			self.movieTimeEntry.focus_set()
			self.movieTimeEntry.select_range(0, "end")
			self.movieTimeEntry.icursor("end")
		return "break"
	
	
	def mouseScroll(self, event):
		if event.widget != self.itemListBox:
			if event.delta > 0 and self.currentItemNum > 0:
				self.setView(self.currentItemNum - 1)
			elif event.delta < 0 and self.currentItemNum < len(self.database) - 1:
				self.setView(self.currentItemNum + 1)
	
	
	def addItem(self):
		self.addButton.grid_forget()
		self.addEntry.delete(0, "end")
		self.addEntry.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
		self.addEntry.focus_set()
		
		self.bind("<Button-1>", self.closeAddEntry)
	
	
	def closeAddEntry(self, event=None):
		if not event or event.widget != self.addEntry:
			self.unbind("<Button-1>")
			self.addEntry.grid_forget()
			self.addButton.grid(row=3, column=0,
				columnspan=2, pady=2, sticky="ew")
			
			if not event or event.widget not in [
					self.showTimeEntry, self.movieTimeEntry]:
				self.itemListBox.focus_set()
	
	
	def submitAddEntry(self, event=None):
		self.closeAddEntry()
		if not self.addEntry.get():
			return
		
		for i in self.addEntry.get().split("|"):
			Thread(target=lambda: SearchItems(self, i, self.apiKey, self.tempPath),
				daemon=True).start()
	
	
	def updateTime(self, event):
		self.currentItem.timeProgress = event.widget.get()
		self.setList()
		self.setView(self.currentItem)
	
	
	def complete(self, event=None):
		if event and event.widget in [self.addEntry, self.showTimeEntry]:
			return
		
		if type(self.currentItem) == Show:
			self.currentItem.completeEpisode()
		elif type(self.currentItem) == Movie:
			self.currentItem.toggleComplete()
		
		self.setList()
		self.setView(self.currentItem)
	
	
	def openLink(self, event=None):
		if self.currentItem.isComplete():
			return
		
		link = self.currentItem.getLink(self.sites)
		if link:
			from webbrowser import open
			open(link)
	
	
	def star(self, event=None):
		self.currentItem.toggleStar()
		self.setList()
		self.setView(self.currentItem)
	
	
	def settings(self, event=None):
		if not event or event.widget != self.addEntry:
			SettingsWindow(self)
	
	
	def discontinue(self, event=None):
		self.currentItem.toggleDiscontinue()
		self.setList()
		self.setView(self.currentItem)
	
	
	def deleteItem(self, event=None):
		if event and (event.widget in [self.showTimeEntry,
				self.movieTimeEntry, self.addEntry]):
			return
		
		confirmDelete = messagebox.askokcancel("Confirm deletion",
			"Are you sure you want to delete {0}?".format(
			str(self.currentItem).strip()))
		
		if confirmDelete:
			# if the item is a movie that's the last in it's collection unless it's the only one in the collection, select the previous movie instead
			# there's probably a better way
			if type(self.currentItem) == Movie and self.currentItem.collection and len(self.currentItem.collection.movies) > 1 and sorted(self.currentItem.collection.movies).index(self.currentItem) == len(self.currentItem.collection.movies) - 1:
				nextItemNum = self.currentItemNum - 1
			else:
				nextItemNum = self.currentItemNum
			
			self.database.delete(self.currentItem)
			nextItem = self.database[nextItemNum]
			self.setList()
			self.setView(nextItem)
	
	
	def exportData(self, event):
		# print("export")
		# output = ""
		
		for movie in [x for x in self.database if type(x) == Movie]:
			if movie.collection:
				databaseCollection = [x for x in self.database if type(x) == Collection and x.id == movie.collection.id][0]
				if movie not in databaseCollection.movies:
					databaseCollection.movies.append(movie)
		
		for collection in [x for x in self.database if type(x) == Collection]:
			collection.movies = [x for x in collection.movies if x in self.database]
		
		print(len([x for x in self.database if type(x) == Movie]))
		with open("C:\\Users\\Simonomi\\Desktop\\test 2.txt", "w") as file:
			for movie in [x for x in self.database if type(x) == Movie]:
				file.write("{}\t{}\t{}\t{}\t".format(movie.id, movie.complete, movie.starred, movie.discontinued))
				if movie.isWatching():
					file.write("\t{}".format(movie.timeProgress))
				file.write("\n")
		
		
		# for movie in [x for x in self.database if type(x) == Movie and x.year == 999999]:
			# print(movie.title)
			# self.database.delete(movie)
			# item = ""
			
			# item += str(show.id) + "|"
			# item += str(show.title) + "|"
			# item += str(show.discontinued) + "|"
			# item += str(show.starred) + "|"
			# item += str(show.autoMode) + "|"
			
			# completionData = []
			# for season in range(len(show.episodeData)):
				# for episode in range(show.episodeData[season]):
					# if season + 1 < show.getSeason():
						# completionData.append(True)
					# elif season + 1 == show.getSeason():
						# if episode + 1 < show.getEpisode():
							# completionData.append(True)
						# else:
							# completionData.append(False)
					# else:
						# completionData.append(False)
			
			# item += "-".join([str(x) for x in completionData])
			
			# output += item + "\n"
		
		# with open("C:\\Users\\Simonomi\\Google Drive\\desktop\\output.txt", "wb") as file:
			# file.write(output.encode('utf8'))
			
	def downloadEpisode(self, totalEpisode):
		for site in self.sites:
			if str(site) in self.currentItem.links:
				downloadLink = site.getDownloadLink(
					self.currentItem.getLink(self.sites, totalEpisode))
				
				fileName = "{} s{}e{}".format(self.currentItem.title,
					self.currentItem.getSeason(totalEpisode),
					self.currentItem.getEpisode(totalEpisode))
				
				# print("wget -c -O \"{}.mp4\" \"{}\"".format(fileName, # downloadLink))
				
				import win32com.shell.shell as shell
				command = "start \"Downloading\" cmd /c \"cd \\doomsday&wget -c -O \"{}.mp4\" \"{}\"\"".format(fileName, downloadLink)
				shell.ShellExecuteEx(lpVerb="runas", lpFile="cmd.exe",
					lpParameters="/c {}".format(command))
				break



class SettingsWindow(tk.Toplevel):
	def __init__(self, parent):
		super().__init__()
		
		self.parent = parent
		self.item = self.parent.currentItem
		
		self.title("Settings - {}".format(self.item.title))
		self.resizable(False, False)
		self.config(bg=self.parent.bg)
		self.focus_set()
		
		
		self.heading = ttk.Label(self, text="{} (ID: {})".format(self.item.originaltitle,
			self.item.id),style="Heading.TLabel")
		self.heading.grid(row=0, column=0, columnspan=3, padx=3, sticky="w")
		
		
		self.titleFrame = ttk.Frame(self)
		self.titleFrame.columnconfigure(1, weight=1)
		self.titleFrame.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
		
		self.titleLabel = ttk.Label(self.titleFrame, text="Title:")
		self.titleLabel.grid(row=0, column=0, sticky="w")
		
		self.titleEntry = ttk.Entry(self.titleFrame, font=("Courier New", 15, "bold"))
		self.titleEntry.grid(row=0, column=1, sticky="nsew", padx=3)
		self.titleEntry.bind("<KeyPress>", self.pressKey)
		self.titleEntry.bind("<KeyRelease>", self.pressKey)
		
		self.resetTitleButton = ttk.Button(self.titleFrame, text="Reset", command=self.resetTitle)
		self.resetTitleButton.grid(row=0, column=2, sticky="e")
		
		
		self.imageFrame = ttk.Frame(self)
		self.imageFrame.columnconfigure(1, weight=1)
		self.imageFrame.grid(row=2, column=0, padx=5, pady=2, sticky="ew")
		
		self.imageLabel = ttk.Label(self.imageFrame, text="Image URL:")
		self.imageLabel.grid(row=0, column=0, sticky="w")
		
		self.imageEntry = ttk.Entry(self.imageFrame, font=("Courier New", 15, "bold"))
		self.imageEntry.grid(row=0, column=1, sticky="nsew", padx=3)
		self.imageEntry.bind("<KeyPress>", self.pressKey)
		self.imageEntry.bind("<KeyRelease>", self.pressKey)
		
		self.resetImageButton = ttk.Button(self.imageFrame, text="Reset", command=self.resetImage)
		self.resetImageButton.grid(row=0, column=2, sticky="e")
		
		self.titleEntry.insert(0, self.item.title)
		self.imageEntry.insert(0, self.item.imageLink)
		
		
		if type(self.item) == Show:
			self.episodeDataFrame = ttk.Frame(self)
			self.episodeDataFrame.columnconfigure(1, weight=1)
			self.episodeDataFrame.grid(row=3, column=0, padx=5, pady=2, sticky="ew")
			
			self.episodeDataLabel = ttk.Label(self.episodeDataFrame, text="Episode data:")
			self.episodeDataLabel.grid(row=0, column=0, sticky="w")
			
			self.episodeDataEntry = ttk.Entry(self.episodeDataFrame, font=("Courier New", 15, "bold"))
			self.episodeDataEntry.grid(row=0, column=1, sticky="nsew", padx=3)
			self.episodeDataEntry.bind("<KeyPress>", self.pressKey)
			self.episodeDataEntry.bind("<KeyRelease>", self.pressKey)
			
			self.autoMode = tk.IntVar()
			self.episodeDataAutoButton = ttk.Checkbutton(self.episodeDataFrame, text="Auto mode", command=self.toggleAutoMode, variable=self.autoMode)
			self.episodeDataAutoButton.grid(row=0, column=2, sticky="e")
			
			
			self.episodeProgressFrame = ttk.Frame(self)
			self.episodeProgressFrame.columnconfigure(1, weight=1)
			self.episodeProgressFrame.grid(row=4, column=0, padx=5, pady=2, sticky="ew")
			self.episodeProgressLabel = ttk.Label(self.episodeProgressFrame, text="Total episode progress:")
			self.episodeProgressLabel.grid(row=0, column=0, sticky="w")
			
			self.episodeProgressSpinbox = ttk.Spinbox(self.episodeProgressFrame, from_=1, to=sum(self.item.episodeData), increment=1, font=("Courier New", 15, "bold"))
			self.episodeProgressSpinbox.grid(row=0, column=1, sticky="nsew", padx=3)
			self.episodeProgressSpinbox.bind("<KeyPress>", self.pressKey)
			self.episodeProgressSpinbox.bind("<KeyRelease>", self.pressKey)
			
			self.episodeProgressTotalLabel = ttk.Label(self.episodeProgressFrame, text="/{}".format(sum(self.item.episodeData)))
			self.episodeProgressTotalLabel.grid(row=0, column=2, sticky="w")
			
			self.episodeDataEntry.insert(0, " ".join([str(x) for x in self.item.episodeData]))
			self.episodeProgressSpinbox.insert(0, self.item.episodeProgress)
			
			if self.item.autoMode:
				self.autoMode.set(1)
				self.episodeDataEntry.state(["disabled"])
			else:
				self.autoMode.set(0)
				self.episodeDataEntry.state(["!disabled"])
		
		
		self.resizeWindow()
		self.titleEntry.focus_set()
		self.titleEntry.select_range(0, "end")
		
		self.bind("<Escape>", self.submit)
		self.bind("<Return>", self.submit)
		self.parent.bind("<FocusIn>", self.submit)
	
	
	def pressKey(self, event):
		self.after(1, self.resizeWindow)
		if event.keycode == 37 and event.widget.select_present(): # left
			event.widget.icursor(min(event.widget.index("sel.first"), event.widget.index("sel.last")))
		elif event.keycode == 39 and event.widget.select_present(): # right
			event.widget.icursor(max(event.widget.index("sel.first"), event.widget.index("sel.last")))
	
	
	def resizeWindow(self):
		self.titleEntry.config(width=len(self.titleEntry.get()) + 1)
		self.imageEntry.config(width=len(self.imageEntry.get()) + 1)
		
		if type(self.item) == Show:
			self.episodeDataEntry.config(width=len(self.episodeDataEntry.get()) + 1)
			self.episodeProgressSpinbox.config(width=len(self.episodeProgressSpinbox.get()) + 1)
	
	
	def resetTitle(self):
		self.titleEntry.delete(0, "end")
		self.titleEntry.insert(0, self.item.originalTitle)
		self.titleEntry.select_range(0, "end")
		self.titleEntry.icursor("end")
		self.titleEntry.focus_set()
		self.resizeWindow()
	
	
	def resetImage(self):
		self.imageEntry.delete(0, "end")
		self.imageEntry.insert(0, self.item.originalImageLink)
		self.imageEntry.select_range(0, "end")
		self.imageEntry.icursor("end")
		self.imageEntry.focus_set()
		self.resizeWindow()
	
	
	def toggleAutoMode(self):
		self.item.autoMode = not self.item.autoMode
		if self.item.autoMode:
			self.autoMode.set(1)
			self.item.resetEpisodeData()
			
			self.episodeDataEntry.delete(0, "end")
			self.episodeDataEntry.insert(0, " ".join([str(x) for x in self.item.episodeData]))
			self.episodeDataEntry.state(["disabled"])
		else:
			self.autoMode.set(0)
			self.episodeDataEntry.state(["!disabled"])
	
	
	def close(self, event=None):
		self.parent.unbind("<FocusIn>")
		self.destroy()
		self.parent.focus_set()
	
	
	def submit(self, event=None):
		if self.winfo_exists():
			self.item.title = self.titleEntry.get()
			self.item.imageLink = self.imageEntry.get()
			
			if type(self.item) == Show:
				try:
					self.item.episodeData = [int(x) for x in self.episodeDataEntry.get().split(" ")]
				except:
					pass
				try:
					self.item.episodeProgress = int(self.episodeProgressSpinbox.get())
				except:
					pass
			
			self.close()
			
			self.parent.setList()
			self.parent.setView(self.parent.currentItem)
		else:
			self.parent.unbind("<FocusIn>")



class SearchItems(tk.Toplevel):
	def __init__(self, parent, search, apiKey, tempPath):
		super().__init__()
		
		self.tempPath = tempPath
		self.parent = parent
		
		self.title("Search Results: {}".format(search))
		self.config(width=500, height=0)
		self.resizable(False, False)
		self.config(bg=self.parent.bg)
		self.focus_set()
		
		self.progressBar = ttk.Progressbar(self, length=500, mode="indeterminate", orient=tk.HORIZONTAL)
		self.progressBar.start()
		self.progressBar.grid()
		
		
		from json import loads
		from requests import exceptions
		try:
			# showData = loads(getSourceCode("https://api.tvmaze.com/search/shows?q={}".format(search)))
			showData = []
			movieData = loads(getSourceCode("https://api.themoviedb.org/3/search/movie?api_key={}&query={}".format(apiKey, search)))
		except (urllib.error.URLError, exceptions.SSLError,
			exceptions.ConnectionError):
			self.destroy()
			# print("offline")
			return
		
		if "errors" in movieData:
			movieData["results"] = []
		
		
		sumall = len(showData) + len(movieData["results"])
		if sumall == 1:
			self.destroy()
			
			if len(showData) > 0:
				newShow = Show(showData[0]["show"]["id"])
				self.parent.database.append(newShow)
				self.parent.setList()
				self.parent.setView(newShow)
				
				messagebox.showinfo("Show added",
					"The show \"{}\" was added".format(newShow.title),
					parent=self.parent)
			else:
				newMovie = Movie(movieData["results"][0]["id"])
				
				if newMovie.collection and newMovie.collection.id not in [
						x.id for x in self.parent.database if type(x) == Collection]:
					self.parent.database.append(newMovie.collection)
					for i in newMovie.collection.movies:
						self.parent.database.append(i)
					
					self.parent.setList()
					self.parent.setView(newMovie.collection)
				else:
					self.parent.database.append(newMovie)
					
					self.parent.setList()
					self.parent.setView(newMovie)
				
				messagebox.showinfo("Movie added",
					"The movie \"{}\" was added".format(newMovie.title),
					parent=self.parent)
			return
		if sumall == 0:
			self.destroy()
			
			messagebox.showinfo("No Results Found",
				"No search results were found for the search \"{}\"".format(
				search), parent=self.parent)
			return
		
		
		self.progressBar.grid_forget()
		
		self.frames = {}
		
		imageDestination = self.tempPath + "loading.jpg"
		if not (path.exists(imageDestination) and
				path.getsize(imageDestination) != 0):
			urllib.request.urlretrieve(errorUrl, imageDestination)
		self.pictures = {"loading": ImageTk.PhotoImage(Image.open(
			imageDestination).resize((126, 177)))}
		
		for i in reversed(showData):
			if i["show"]["id"] in [x.id for x in self.parent.database if type(x) == Show]:
				showData.remove(i)
		
		for i in reversed(movieData["results"]):
			if i["id"] in [x.id for x in self.parent.database if type(x) == Movie]:
				movieData["results"].remove(i)
		
		
		if showData:
			ttk.Label(self, text="TV Shows:").grid(row=0, column=0,
				columnspan=10, sticky="w", padx=3)
		column = 0
		for i in showData[:10]:
			key = "Show {}".format(i["show"]["id"])
			
			self.frames[key] = ttk.Frame(self, name=key.lower())
			self.frames[key].grid(row=1, column=column)
			
			ttk.Label(self.frames[key], image=self.pictures["loading"]).grid()
			if i["show"]["image"] == None:
				Thread(target=lambda: self.downloadImage("Show",
					i["show"]["id"], None), daemon=True).start()
			else:
				Thread(target=lambda: self.downloadImage("Show",
					i["show"]["id"], i["show"]["image"]["medium"]),
					daemon=True).start()
			
			ttk.Label(self.frames[key], text=i["show"]["name"],
				wraplength=126, style="Option.TLabel")
			column += 1
		
		# if movieData["results"]:
			# ttk.Label(self, text="Movies:").grid(row=2, column=0,
				# columnspan=10, sticky="w", padx=3)
		column = 0
		for i in movieData["results"][:10]:
			key = "Movie {}".format(i["id"])
			
			self.frames[key] = ttk.Frame(self, name=key.lower())
			self.frames[key].grid(row=3, column=column)
			
			ttk.Label(self.frames[key], image=self.pictures["loading"]).grid()
			Thread(target=lambda: self.downloadImage("Movie", i["id"],
				"https://themoviedb.org/t/p/w300{}".format(i["poster_path"])),
				daemon=True).start()
			
			ttk.Label(self.frames[key], text="{}".format(i["title"]),
				wraplength=126, style="Option.TLabel")
			column += 1
		
		
		for i in self.frames.values():
			i.bind("<Enter>", self.enterFrame)
			i.bind("<Leave>", self.exitFrame)
		
		self.bind("<Button-1>", self.submit)
	
	
	def downloadImage(self, type, id, downloadLink):
		if not path.exists(self.tempPath + "Images\\"):
			mkdir(self.tempPath + "Images\\")
		
		key = "{} {}".format(type, id)
		
		if key in self.pictures:
			return
		
		if downloadLink:
			imageDestination = "{}{}.jpg".format(self.tempPath + "Images\\", key)
		else:
			imageDestination = self.tempPath + "error.jpg"
		
		if not (path.exists(imageDestination) and
				path.getsize(imageDestination) != 0):
			try:
				urllib.request.urlretrieve(downloadLink, imageDestination)
			except urllib.error.URLError:
				imageDestination = self.tempPath + "error.jpg"
		
		if not self.winfo_exists():
			return
		
		if path.exists(imageDestination) and path.getsize(imageDestination) != 0:
			try:
				self.pictures[key] = ImageTk.PhotoImage(
					Image.open(imageDestination).resize((126, 177)))
				
				self.frames[key].winfo_children()[0].config(
					image=self.pictures[key])
			except OSError:
				return
	
	
	def enterFrame(self, event):
		event.widget.winfo_children()[1].grid(row=0,
			column=0, sticky="sew", pady=2)
	
	
	def exitFrame(self, event):
		event.widget.winfo_children()[1].grid_forget()
	
	
	def submit(self, event):
		itemType, id = str(event.widget).split(".")[2].split(" ")
		
		self.destroy()
		
		if itemType == "show":
			newShow = Show(id)
			self.parent.database.append(newShow)
			self.parent.setList()
			self.parent.setView(newShow)
		else:
			newMovie = Movie(id)
			
			if newMovie.collection and newMovie.collection.id not in [
					x.id for x in self.parent.database if type(x) == Collection]:
				self.parent.database.append(newMovie.collection)
				for i in newMovie.collection.movies:
					self.parent.database.append(i)
				self.parent.setList()
				self.parent.setView(newMovie.collection)
			else:
				self.parent.database.append(newMovie)
				
				if newMovie.collection:
					newMovie.collection = [x for x in self.parent.database if type(x) == Collection and x.id == newMovie.collection.id][0]
					newMovie.collection.movies.append(newMovie)
				
				self.parent.setList()
				self.parent.setView(newMovie)
