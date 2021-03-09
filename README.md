# Progress Tracker

## Features
- Keeps track of season, episode, and (optional) time for any number of shows
- Sorts shows in order of:
	1. Watching
	2. To Watch
	3. Completed
	4. Discontinued (remembers progress but hides from other lists)
- Uses [TVmaze](https://www.tvmaze.com/api) to retrieve and update show information
	- Automatically generates show information given (at least partial) title, including:
		- Full title
		- Season/episode data
		- Preview image
	- Automatically updates shows when new seasons/episodes are released
- To add shows in bulk, separate each title by a `|` character
- Togglable light/dark theme (edit variable in code)
- "Starred" shows appear at top of their respective sections
- More not listed

## How to use
- Install [python](https://www.python.org/downloads/) (latest version 3.x)
- Install/update pip (`python -m pip install --upgrade pip`)
- Install requirements (`pip install -r requirements.txt`)
- Run ProgressTracker.py with python!

## Links
- New shows automatically generate a link for optional user-defined "Sites"
- Shows have an option in settings to generate a link for each Site
- When loaded, the application searches for `.site` files in its temporary directory (default _C:\Users\%USERNAME%\AppData\Roaming\ProgressTracker\Sites\\_)
	- If none are found, all link functionality is disabled
- A `.site` file contains the following information on the first three lines:
	1. priority: _[number]_
		- A rating of which order a site should be used in, used from lowest to highest
	2. multiple seasons: _[True/False]_
		- True if the site has a different format link for each season of a show
		- www.example.com/show-name-season-1-episode-1
		- www.example.com/show-name-season-2-episode-1
	3. downloadable: _[True/False]_
		- True if it is possible (and provided) to generate a download link (.mp4) for an episode
- Followed by script-like sets of instructions
	- One section is required to generate a link for a show: _firstLink_
	- One section is optionally used for generating a download link for an episode: _downloadEpisode_
	- Each section is marked at the beginning and end by a line with nothing but the name of that section
	- A section uses a list of instructions and arguments to manipulate an array of values, which by default is empty (`[]`)
	- In a section, the following syntax is used:
		- Command name
			- **getElementAttribute** sets item _index_ to the _attribute_ of the _element_ at _element index_ in the webpage at _url_ (any `{}` in _url_ will be replaced with the show title, or in case of multiple seasons, "show title _[season number]_")
				- index
				- url
				- element
				- attribute
				- element index
			- **replace** replaces _query_ with _replacement_ in item _index_
				- index
				- query
				- replacement
			- **split** splits item _index_ with _regex query_
				- index
				- regex query
			- **insert** inserts _text_ into memory at _index_
				- index
				- text
			- **debase** decodes base64 item at _index_
				- index
			- **add** adds item at _index_ to _number_
				- index
				- number
- Example: _Netflix.site_
	- priority: 0<br>multiple seasons: False<br>downloadable: False<br><br>firstLink<br>getElementAttribute<br>0<br>https://www.google.com/search?q=site%3Awww.netflix.com%2Ftitle%2F+{}<br>#rso > div:first-child> div > div.yuRUbf > a<br>href<br>0<br>replace<br>0<br>title<br>watch<br>firstLink


## To do
https://trello.com/b/dSpY8vhz/progress-tracker
