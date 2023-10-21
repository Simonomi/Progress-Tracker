from os import path
from common import *

apiKey = "e0ea968db936eab1eaf1a6e436816d04"



class Site:
	def __init__(self, file):
		with open(file) as site:
			info = site.read().split("\n")
			
			self.name = ".".join(file.split("\\")[-1].split(".")[:-1])
			self.priority = int(info[0].split(": ")[1])
			self.multipleSeasons = info[1].split(": ")[1] == "True"
			self.downloadable = info[2].split(": ")[1] == "True"
			self.shows = info[3].split(": ")[1] == "True"
			self.movies = info[4].split(": ")[1] == "True"
			
			if self.shows:
				self.firstShowLink = "\n".join(info[5:]).split("firstShowLink")[1].split("\n")[1:-1]
			if self.movies:
				self.firstMovieLink = "\n".join(info[5:]).split("firstMovieLink")[1].split("\n")[1:-1]
			if self.downloadable:
				self.downloadEpisode = "\n".join(
					info[5:]).split("downloadEpisode")[1].split("\n")[1:-1]
	
	
	def __lt__(self, other):
		return self.priority < other.priority
	
	
	def __str__(self):
		return self.name
	
	
	def __repr__(self):
		return "<Site \"{}\">".format(self.name)
	
	
	def generateLinks(self, title, item):
		if type(item) == Show:
			link = runCommands(self.firstShowLink, title)
		else:
			link = runCommands(self.firstMovieLink, title)
		
		if type(item) == Show and self.multipleSeasons:
			for i in range(2, len(item.episodeData) + 1):
				links += "\n" + runCommands(self.firstShowLink,	
					"{} {}".format(title,i))
				if links[-1] == "\n":
					return links[:-1]
		
		return link
	
	
	def getDownloadLink(self, link):
		if self.downloadable:
			return runCommands(self.downloadEpisode, link)



class ProgressDatabase(list):
	def __init__(self, version=1.62):
		super().__init__()
		self.version = version
	
	
	def __add__(self, other):
		super().__add__(other)
		return sorted(self)
	
	
	def __iadd__(self, other):
		if other.version < self.version:
			for item in other:
				try:
					item.originaltitle
				except AttributeError:
					item.originaltitle = item.title
				
				try:
					item.originalImageLink
				except AttributeError:
					item.originalImageLink = item.imageLink
				
				if type(item) == Collection:
					try:
						item.autoMode
					except AttributeError:
						item.autoMode = True
		elif other.version > self.version:
			raise TypeError("Please update app to add database")
		else:
			super().__iadd__(other)
		
		return sorted(self)
	
	
	def append(self, other):
		super().append(other)
		self.sort()
	
	
	def load(self, file):
		from pickle import load
		
		if path.exists(file):
			with open(file, "rb") as file:
				self += load(file)
			self.sort()
		else:
			pass
# 			raise FileNotFoundError(file)
	
	
	def save(self, path):
		from pickle import dump
		
		with open(path, "wb") as file:
			dump(self, file)
	
	
	def delete(self, item):
		if type(item) == Collection:
			for i in item.movies:
				if i in self:
					self.remove(i)
		
		if type(item) == Movie and item.collection:
			if len(item.collection.movies) == 1:
				self.delete(item.collection)
				return
			else:
				item.collection.movies.remove(item)
		
		self.remove(item)
	
	
	def update(self, window):
		for i in self:
			changes = i.update()
			
			if i == window.currentItem:
				window.setView(i)
			
			if changes:
				if type(i) == Collection and type(changes) == list:
					for j in changes:
						self.append(j)
				
				window.setList()



class Item:
	def __init__(self, id):
		self.id = id
		self.starred = False
		self.discontinued = False
	
	
	def __str__(self):
		if self.starred:
			return "⋆{}".format(self.title)
		else:
			return self.title
	
	
	def __repr__(self):
		return "<{} {}: {}>".format(type(self).__name__, self.id, self.title)
	
	
	def __lt__(self, other):
		return self.getStatus() < other.getStatus()
	
	
	def getStatus(self):
		if self.isComplete():
			priority = 5
		elif self.discontinued:
			priority = 7
		elif self.isWatching():
			priority = 1
		else:
			priority = 3
		
		if self.starred:
			priority -= 1
		
		if type(self) == Show:
			category = 2
		else:
			category = 0
		
		return "{}{}{}".format(priority, self.title, category)
	
	
	def toggleStar(self):
		self.starred = not self.starred
	
	
	def toggleDiscontinue(self):
		self.discontinued = not self.discontinued



class Show(Item):
	def __init__(self, id):
		super().__init__(id)
		
		from json import loads
		showData = loads(getSourceCode("https://api.tvmaze.com/shows/{}?embed=seasons".format(self.id)))
		
		self.title = showData["name"]
		self.originaltitle = self.title
		if showData["image"]:
			self.imageLink = showData["image"]["medium"]
		else:
			self.imageLink = ""
		self.originalImageLink = self.imageLink
		self.links = {}
		self.timeProgress = ""
		self.episodeData = []
		
		for season in showData["_embedded"]["seasons"]:
			if season["premiereDate"] and dateHasPassed(season["premiereDate"]):
				if dateHasPassed(season["endDate"]):
					self.episodeData.append(season["episodeOrder"])
				else:
					seasonEpisodes = loads(getSourceCode(
						"https://api.tvmaze.com/seasons/{}/episodes".format(season["id"])))
					
					for episode in seasonEpisodes:
						if not dateHasPassed(episode["airdate"]):
							self.episodeData.append(episode["number"] - 1)
							break
		
		if None in self.episodeData:
			seasonEpisodeList = loads(getSourceCode("https://api.tvmaze.com/shows/{}/episodes".format(self.id)))
			
			seasonNumbers = [x["season"] for x in seasonEpisodeList]
			self.episodeData = []
			for i in range(seasonNumbers[-1]):
				self.episodeData.append(seasonNumbers.count(i + 1))
		
		self.episodeProgress = 1
		self.autoMode = True
		self.status = showData["status"]
	
	
	def isWatching(self):
		return self.episodeProgress != 1 or self.timeProgress
	
	
	def isComplete(self):
		return self.episodeProgress > sum(self.episodeData)
	
	
	def getLink(self, sites, episodeProgress=None):
		if not episodeProgress:
			episodeProgress = self.episodeProgress
		season = self.getSeason(episodeProgress)
		
		links = None
		for i in [x.name for x in sites]:
			if i in self.links:
				links = self.links[i]
				break
		
		if not links:
			return
		
		if len(links) > 1:
			if season >= len(links):
				link = links[-1]
			else:
				link = links[season - 1]
		else:
			link = links[0]
		
		return parseLink(link, season,
			self.getEpisode(episodeProgress), episodeProgress)
	
	
	def getEpisode(self, totalProgress=None):
		if not totalProgress:
			totalProgress = self.episodeProgress
		
		for i in self.episodeData:
			totalProgress -= i
			if totalProgress <= 0:
				totalProgress += i
				break
		
		return totalProgress
	
	
	def getMaxEpisodes(self, totalProgress=None):
		return self.episodeData[min(len(self.episodeData) - 1,
			self.getSeason(totalProgress) - 1)]
	
	
	def getSeason(self, totalProgress=None):
		if not totalProgress:
			totalProgress = self.episodeProgress
		
		seasonNumber = 1
		for i in self.episodeData:
			totalProgress -= i
			if totalProgress <= 0:
				break
			seasonNumber += 1
		
		return seasonNumber
	
	
	def getMaxSeasons(self, totalProgress=None):
		return len(self.episodeData)
	
	
	def completeEpisode(self):
		if not self.isComplete():
			self.episodeProgress += 1
			self.timeProgress = ""
	
	
	def resetEpisodeData(self, showData=None):
		from json import loads
		
		if not showData:
			showData = loads(getSourceCode("https://api.tvmaze.com/shows/{}?embed=seasons".format(self.id)))
		
		originalEpisodeData = self.episodeData
		self.episodeData = []
		
		for season in showData["_embedded"]["seasons"]:
			if season["premiereDate"] and dateHasPassed(season["premiereDate"]):
				if dateHasPassed(season["endDate"]):
					self.episodeData.append(season["episodeOrder"])
				else:
					seasonEpisodes = loads(getSourceCode(
						"https://api.tvmaze.com/seasons/{}/episodes".format(season["id"])))
					
					for episode in seasonEpisodes:
						if not dateHasPassed(episode["airdate"]):
							self.episodeData.append(episode["number"] - 1)
							break
		
		if None in self.episodeData:
			seasonEpisodeList = loads(getSourceCode("https://api.tvmaze.com/shows/{}/episodes".format(self.id)))
			
			seasonNumbers = [x["season"] for x in seasonEpisodeList]
			self.episodeData = []
			for i in range(seasonNumbers[-1]):
				self.episodeData.append(seasonNumbers.count(i + 1))
		
		return originalEpisodeData != self.episodeData
	
	
	def update(self):
		from json import loads
		showData = loads(getSourceCode("https://api.tvmaze.com/shows/{}?embed=seasons".format(self.id)))
		
		originalTitle = self.title
		
		if showData["name"] != self.originaltitle:
			if self.title == self.originaltitle:
				self.title = showData["name"]
			self.originaltitle = showData["name"]
		
		if showData["image"] and showData["image"]["medium"] != self.originalImageLink:
			if self.imageLink == self.originalImageLink:
				self.imageLink = showData["image"]["medium"]
			self.originalImageLink = showData["image"]["medium"]
		
		if self.autoMode:
			self.resetEpisodeData(showData)
		
		if self.status != showData["status"]:
			self.status = showData["status"]
		
		return originalTitle != self.title



class Collection(Item):
	def __init__(self, id):
		super().__init__(id)
		
		from json import loads
		collectionData = loads(getSourceCode("https://api.themoviedb.org/3/collection/{}?api_key={}".format(self.id, apiKey)))
		
		self.title = collectionData["name"].replace(" Collection", "")
		self.originaltitle = self.title
		self.imageLink = "https://themoviedb.org/t/p/w300{}".format(collectionData["poster_path"])
		self.originalImageLink = self.imageLink
		self.autoMode = True
		
		self.movies = []
		for i in collectionData["parts"]:
			self.movies.append(Movie(i["id"], self))
	
	
	def isWatching(self):
		return max([x.isWatching() for x in self.movies])
	
	
	def isComplete(self):
		return min([x.isComplete() for x in self.movies])
	
	
	def toggleStar(self):
		super().toggleStar()
		if len(self.movies) == 1:
			self.movies[0].starred = self.starred
	
	
	def toggleDiscontinue(self):
		super().toggleDiscontinue()
		if len(self.movies) == 1:
			self.movies[0].discontinued = self.discontinued
	
	
	def update(self):
		from json import loads
		collectionData = loads(getSourceCode("https://api.themoviedb.org/3/collection/{}?api_key={}".format(self.id, apiKey)))
		
		originalTitle = self.title
		
		if self.title == self.originaltitle:
			self.title = collectionData["name"].replace(" Collection", "")
		self.originaltitle = collectionData["name"].replace(" Collection", "")
		
		if self.imageLink == self.originalImageLink:
			self.imageLink = "https://themoviedb.org/t/p/w300{}".format(collectionData["poster_path"])
		self.originalImageLink = "https://themoviedb.org/t/p/w300{}".format(collectionData["poster_path"])
		
		newMovies = []
		if self.autoMode:
			if False in [x["id"] in [y.id for y in self.movies] for x in collectionData["parts"]]:
				for i in collectionData["parts"]:
					if i["id"] not in [x.id for x in self.movies]:
						newMovie = Movie(i["id"], self)
						self.movies.append(newMovie)
						newMovies.append(newMovie)
		
		if newMovies:
			return newMovies
		return originalTitle != self.title



class Movie(Item):
	def __init__(self, id, collection=None):
		super().__init__(id)
		
		from json import loads
		movieData = loads(getSourceCode("https://api.themoviedb.org/3/movie/{}?api_key={}".format(self.id, apiKey)))
		
		self.title = movieData["title"]
		self.originaltitle = self.title
		self.imageLink = "https://themoviedb.org/t/p/w300{}".format(movieData["poster_path"])
		self.originalImageLink = self.imageLink
		self.links = {}
		self.timeProgress = ""
		self.complete = False
		
		if movieData["release_date"]:
			self.year = int(movieData["release_date"][:4])
		else:
			self.year = 999999
		
		if collection:
			self.collection = collection
		elif movieData["belongs_to_collection"]:
			self.collection = Collection(movieData["belongs_to_collection"]["id"])
		else:
			self.collection = None
	
	
	def __str__(self):
		if self.year == 999999:
			year = "?"
		else:
			year = self.year
		
		prefix = ""
		if self.collection:
			prefix +=  "   "
		if self.starred:
			prefix += "⋆"
		
		return "{}{} ({})".format(prefix, self.title, year)
	
	
	def getStatus(self):
		if self.isComplete():
			priority = 5
		elif self.discontinued:
			priority = 7
		elif self.isWatching():
			priority = 1
		else:
			priority = 3
		
		if self.starred:
			priority -= 1
		
		if self.collection:
			collectionStatusNoCategory = self.collection.getStatus()[:-1]
			return "{}1{}{}{}".format(collectionStatusNoCategory, priority, self.year, self.title)
		else:
			return "{}{}{}".format(priority, self.title, self.year)
	
	
	# REMOVE THIS
	def getLink(self, sites, ignore=None):
		for i in [x.name for x in sites]:
			if i in self.links:
				return parseLink(self.links[i])
		return
	
	
	def isWatching(self):
		from datetime import datetime
		return datetime.now().year > self.year and (self.complete or bool(self.timeProgress))
	
	
	def isComplete(self):
		from datetime import datetime
		return self.complete or self.year > datetime.now().year
	
	
	def toggleComplete(self):
		self.complete = not self.complete
	
	
	def toggleStar(self):
		super().toggleStar()
		if self.collection and len(self.collection.movies) == 1:
			self.collection.starred = self.starred
	
	
	def toggleDiscontinue(self):
		super().toggleDiscontinue()
		if self.collection and len(self.collection.movies) == 1:
			self.collection.discontinued = self.discontinued
	
	
	def update(self):
		from json import loads
		movieData = loads(getSourceCode("https://api.themoviedb.org/3/movie/{}?api_key={}".format(self.id, apiKey)))
		
		originalTitle = self.title
		originalYear = self.year
		
		if self.title == self.originaltitle:
			self.title = movieData["title"]
		self.originaltitle = movieData["title"]
		
		if self.imageLink == self.originalImageLink:
			self.imageLink = "https://themoviedb.org/t/p/w300{}".format(movieData["poster_path"])
		self.originalImageLink = "https://themoviedb.org/t/p/w300{}".format(movieData["poster_path"])
		
		if movieData["release_date"]:
			self.year = int(movieData["release_date"][:4])
		else:
			self.year = 999999
		
		return originalTitle != self.title or originalYear != self.year
