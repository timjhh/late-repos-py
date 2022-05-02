# late-repos-py
Github org scraper for finding late projects

Install dependencies via:

`pip install PyGithub`

Run via:

python3 late-repos.py [-n [Project_Name] -t [Days #]]

The script takes several optional command line arguments:

  -n [s] only prints repos containing substring s, useful for checking only certain projects

  -t [d] adds a buffer to the latest day a repo can be created in days

  -h print this help menu again
