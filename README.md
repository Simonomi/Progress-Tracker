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
    - Auto generates some links (Netflix, etc)
  - Automatically updates shows when new seasons/episodes are released
- To add shows in bulk, seperate each title by a `|` character
- Stores all data in a `.zip` file, the location of which can be anywhere on disk
  - Can be stored in a cloud-synced folder (Google Drive, Dropbox, iCould, etc)
  - If necessary, can be manually overwritten by unzipping
- More not listed!

## How to use
- Install [python](https://www.python.org/downloads/) (latest version 3.x)
- Install requirements (`pip install -r requirements.txt`)
- Run ProgressTracker.py with python!

## To do
https://trello.com/b/dSpY8vhz/progress-tracker
