#!/usr/bin/env python3
###
##
## Late Repo Scraper
## Author: Tim Harrold - timjharrold@gmail.com
## Scrapes a github organization for late projects as specified in a .txt file
## File should contain comma separated values including a module name, starting date, and ending date
## Dates should be MM/DD/YY
##
## The -n flag can be optionally provided to match all projects with a certain name
## E.g. `python3 late-repos.py -n 3d-graphics` will only return repos containing the name `3d-graphics`
##
## The -t flag can be optionally provided to buffer the ending time by a number of days, so the script will search for projects created between [start,end+n]
## You might use this over modifying the end date, because a repo created and finished 3 days late would not register as late at all(with an extended due date). Adding this flag
## registers that program as late, because it is created after the original due date.
## E.g. `python late-repos.py -d 3` will search for repos created 3 days after the deadline
##
###

from email.utils import parsedate
import traceback
from github import Github
import configparser
import time
from time import mktime
import sys
#import datetime
#from backports.zoneinfo import ZoneInfo
from datetime import date, timedelta



DATA = {}
COUNT = [0,0]

MATCH_NAME = None
DAYS = 0
# UTC is 4 hours ahead of EST, so we need to subtract this from the gh timestamp
# Note: this script may not run as intended if in another timezone
UTC_OFFSET = 4*60*60 

def init():
    # Parse the config file
    parser = configparser.ConfigParser()
    try:
        parser.read("config.ini")
    except Exception:
        sys.exit("There was an issue reading config.ini. Please make sure it exists and is formatted correctly.")

    global DATA
    DATA = parser

    if(not DATA.has_option("settings", "authToken")):
        sys.exit("Error: Auth token missing")
    if(not DATA.has_option("settings", "orgName")):
        sys.exit("Error: Organization name missing")

    try:
        gh = Github(DATA["settings"]["authToken"])
    except Exception:
        traceback.print_exc()
        sys.exit("HTTP Request Failed")

    print("Github initialized...")
    return gh

def parseArgs():
    # Command line argument invoked
    if(len(sys.argv) > 1):
        # Check for help flag
        if("-h" in sys.argv):
            print("Options:")
            print("     -n [s] only prints repos containing substring s, useful for checking only certain projects")
            print("     -t [d] adds a buffer to the latest day a repo can be created in days")
            print("     -h print this help menu again")
            sys.exit()
        else:
            print("Parsing args...")

        # Check for match name flag
        if("-n" in sys.argv):
            n_idx = sys.argv.index("-n")
            if(len(sys.argv) >= n_idx+1):
                MATCH_NAME = sys.argv[n_idx+1].lower()        
            else:
                sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")

        # Check for buffer days flag
        if("-t" in sys.argv):
            t_idx = sys.argv.index("-t")
            if(len(sys.argv) >= t_idx+1):
                try:
                    DAYS = int(sys.argv[t_idx+1])
                except:
                    sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")    
            else:
                sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")

def parseDates():
    modules = []
    t1 = mktime(time.strptime(DATA["modules"]["startDate"], "%Y-%m-%d"))
    t2 = mktime(time.strptime(DATA["modules"]["endDate"], "%Y-%m-%d"))
    modules.append([DATA["modules"]["module"],t1,t2])

    return modules

def readRepos(gh, modules):
    try:
        repos = gh.get_organization(DATA["settings"]["orgName"]).get_repos()
    except:
        sys.exit("Error reading repos...")

    print("Reading repos....")
    modDict = {}

    for repo in repos:

        COUNT[0] += 1

        progress(COUNT[0], repos.totalCount)

        if(MATCH_NAME != None):
            if(MATCH_NAME not in repo.name.lower()):
                continue
            else:
                COUNT[1] += 1

        # datetime.datetime objects
        # Note: while repo.pushed_at should supply the last time a repo was pushed to
        # It seems to provide a date later than the last commmit in some cases
        # An alternative approach is commented out below that gets the last commit from the repo
        # However, it is incredibly slow and would benefit from use in tandum with the -n flag
        created = repo.created_at.timestamp()
        finished = (repo.pushed_at-timedelta(seconds=UTC_OFFSET)).timestamp()

        for mod in modules:
            if((mod[1] <= created) and (created <= mod[2] + (DAYS * 24 * 60 * 60))): # Created in reasonable timespan
                if(finished > mod[2]): # Finished before deadline
                    modDict[mod[0]].append(repo.name + "\nCreated At: " + str(repo.created_at-timedelta(seconds=UTC_OFFSET)) + "\nUpdated At: " + str(repo.pushed_at-timedelta(seconds=UTC_OFFSET)) + "\n")
    
    return modDict

def printRepos(modDict):
    # Pretty print dictionary, itemized by module
    print("\n\nTotal Repos Read: " + str(COUNT[0]))
    if(MATCH_NAME is not None):
        print("Matched Repos Read: " + str(COUNT[1]) + "\n")
    else:
        print("\n")
    for key in modDict.keys():
        print("--------------------\n")
        print("---- Module: " + key + " ----\n")
        for item in modDict[key]:
            print(item)
    print("--------------------")

    
##
#
# Progress bar taken from
# https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
#
##
def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()  # As suggested by Rom Ruben


def main():
    parseArgs()
    gh = init()
    modules = parseDates()
    modDict = readRepos(gh, modules)
    printRepos(modDict)

if __name__=="__main__":
    main()