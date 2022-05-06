#!/usr/bin/env python3

##
# @file late-repos.py
#
# @brief Scrapes a github organization for late projects
#
# @section config Configuration
# config.ini should be formatted as follows:
# @code config.ini 
# [settings]
# authToken = [your github auth token]
# orgName = [your github organization name]
# [modules]
# module = [module name]
# startDate = [start date of module YYYY-MM-DD]
# endDate = [end date of module YYYY-MM-DD]
# @endcode
#
#
# @section authors Author(s)
# Tim Harrold - timjharrold@gmail.com
# Connor Milligan - connoramilligan@gmail.com
#

from email.utils import parsedate
import traceback
from github import Github
import configparser
import time
from time import mktime
import sys
from datetime import date, timedelta


## Stores all the values of the config file as a dictionary
DATA = {}
## A list of repos that have been read and the number of repos that match the match name
COUNT = [0,0]
## Command Line Args denoting optional matched name and days offset
ARGS = [None,0]

## UTC is 4 hours ahead of EST, so we need to subtract this from the gh timestamp
# Note: this script may not run as intended if in another timezone
UTC_OFFSET = 4*60*60 

## Initializes the program
# Ensures that the config file is formatted correctly and can be read and
# the global variable DATA is populated with the config file 
# @return Github object
def init():
    # Parse the config file
    parser = configparser.ConfigParser()

    # ensure that the config file exists
    try:
        parser.read("config.ini")
    except Exception:
        sys.exit("There was an issue reading config.ini. Please make sure it exists and is formatted correctly.")

    # set the global variable DATA to the config file
    global DATA
    DATA = parser

    # ensure that the auth token is set
    if(not DATA.has_option("settings", "authToken")):
        sys.exit("Error: Auth token missing")
    # ensure that the org name is set
    if(not DATA.has_option("settings", "orgName")):
        sys.exit("Error: Organization name missing")

    # attempt to create a github object
    try:
        gh = Github(DATA["settings"]["authToken"])
    except Exception:
        traceback.print_exc()
        sys.exit("HTTP Request Failed")

    print("Github initialized...")
    return gh


## Parses the command line arguments
# sets the global variable MATCH_NAME to the name of the repo to match if the -n flag is set
# sets the global variable DAYS to the number of days to add to the latest day a repo can be created
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
                ARGS[0] = sys.argv[n_idx+1].lower()        
            else:
                sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")

        # Check for buffer days flag
        if("-t" in sys.argv):
            t_idx = sys.argv.index("-t")
            if(len(sys.argv) >= t_idx+1):
                try:
                    ARGS[1] = int(sys.argv[t_idx+1])
                except:
                    sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")    
            else:
                sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")

## Parses the dates from the config file
#
# formats the dates and modules into a list of tuples which can be parsed by readRepos
#
# @return list of tuples containing the module name, start date, and end date
# @toDo: add error checking for the dates
# @toDo: allow multiple modules to be parsed
def parseDates():
    modules = []

    # format the start and end dates
    t1 = mktime(time.strptime(DATA["modules"]["startDate"], "%Y-%m-%d"))
    t2 = mktime(time.strptime(DATA["modules"]["endDate"], "%Y-%m-%d"))
    modules.append([DATA["modules"]["module"],t1,t2])

    return modules

## Reads the repos from the github organization
#
# will only read repos that are created after the start date and before the end date
# adds the repo to the dictionary if it is not already there
#
# @param gh Github object
# @param modules list of tuples containing the module name, start date, and end date
# @return dictionary of modules and repos
def readRepos(gh, modules):
    # attempts to fetch repos from the organization
    try:
        repos = gh.get_organization(DATA["settings"]["orgName"]).get_repos()
    except:
        sys.exit("Error reading repos...")

    print("Reading repos....")
    # initialize the dictionary
    modDict = {DATA["modules"]["module"]: []}

    # iterate through the repos
    for repo in repos:

        # count the number of repos read
        COUNT[0] += 1

        # display a progress bar
        progress(COUNT[0], repos.totalCount)

        # if a match name is set, check if the repo name contains the match name
        if(ARGS[0] != None):
            if(ARGS[0] not in repo.name.lower()):
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

        # loop through the modules
        for mod in modules:
            if((mod[1] <= created) and (created <= mod[2] + (int(ARGS[1]) * 24 * 60 * 60))): # Created in reasonable timespan
                if(finished > mod[2]): # Finished before deadline
                    # add the repo to the dictionary
                    modDict[mod[0]].append(repo.name + "\nCreated At: " + str(repo.created_at-timedelta(seconds=UTC_OFFSET)) + "\nUpdated At: " + str(repo.pushed_at-timedelta(seconds=UTC_OFFSET)) + "\n")
    
    return modDict

## Prints the repos
#
# Prints the repos in the dictionary in a readable format
#
# @param modDict dictionary of modules and repos
def printRepos(modDict):
    # Pretty print dictionary, itemized by module
    print("\n\nTotal Repos Read: " + str(COUNT[0]))
    if(ARGS[0] is not None):
        print("Matched Repos Read: " + str(COUNT[1]) + "\n")
    else:
        print("\n")
    for key in modDict.keys():
        print("--------------------\n")
        print("---- Module: " + key + " ----\n")
        for item in modDict[key]:
            print(item)
    print("--------------------")

    
## Progress bar
#
# Progress bar taken from
# https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
#
# @param count number of items read
# @param total total number of items
##
def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()  # As suggested by Rom Ruben

## Main
# 
# Parses the arguments, reads the repos, and prints the repos
def main():
    parseArgs()
    gh = init()
    modules = parseDates()
    modDict = readRepos(gh, modules)
    printRepos(modDict)

# Run the main function
if __name__=="__main__":
    main()