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

## Sites
- New shows automatically generate a link for optional user-defined "Sites"
- Shows have an option in settings to generate a link for a Site
- When loaded, the application searches for `.site` files in its temporary directory (default _C:\Users\%USERNAME%\AppData\Roaming\ProgressTracker\Sites\\_)
	- If none are found, all Site functionality is disabled
- A `.site` file contains the following information separated by newlines:
	1. Priority (#)
	2. Search link (http://...{})
		- Must have `{}` or `{0}` that is replaced with a show's title
	3. Search Element (*css selector*)
		- Selector must indicate search result items
	4. Search Attribute (*html attribute*)
		- Typically `href`, indicates link to season page
	5. Multiple Seasons (True/False)
		- Indicates whether there are multiple season links, usually one per season
		- Used to determine how many search results to accept (one vs two)
	6. Page Element (*css selector*)
		- Selector must indicate episode items
	7. Page Attribute (*html attribute*)
		- Typically `href`, link to individual episode page
	8. Multiple Episodes (True/False)
		- Indicates whether separate episodes have different links
	9. Flip Page Order (True/False)
		- Used if episode pages are presented in reverse order
	10. Flip Season Order (True/False)
		- Used if search results are presented in reverse season order

## To do
https://trello.com/b/dSpY8vhz/progress-tracker
