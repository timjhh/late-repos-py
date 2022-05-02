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

from multiprocessing.sharedctypes import Value
import traceback
from github import Github
import time
from time import mktime
import sys
import datetime
from datetime import date

###
## Replace AUTH_TOKEN with your personal github token via:
## Github -> Settings -> Developer Settings -> Personal access tokens -> Generate new token
###
AUTH_TOKEN = ""
ORG_NAME = ""
MATCH_NAME = None
DAYS = 0

syslen = len(sys.argv)

# Command line argument invoked
if(syslen > 1):
    if("-n" in sys.argv):
        n_idx = sys.argv.index("-n")
        if(syslen >= n_idx+1):
            MATCH_NAME = sys.argv[n_idx+1]          
        else:
            sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")
    if("-t" in sys.argv):
        t_idx = sys.argv.index("-t")
        if(syslen >= t_idx+1):
            try:
                DAYS = int(sys.argv[t_idx+1])
            except:
                sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")    
        else:
            sys.exit("Usage: python3 late-repos.py [-n [Project_Name] -t [Days #]]")

# Convert days to seconds
# Will still be 0 if arg not provided
DAYS = DAYS * 24 * 60 * 60

try:
    gh = Github(AUTH_TOKEN)
except Exception:
    traceback.print_exc()
    print("HTTP Request Failed")

try:
    ranges = open("dates.txt")
except FileNotFoundError:
    sys.exit("File not found!")

modules = []
mod_dict = {}

for line in ranges:

    arr = line.split(",")
    if(len(arr) != 3):
        print("Skipping line with insufficient length...")
    else:

        mod_dict[arr[0]] = []

        # Convert both dates to time_struct objects
        t1 = time.strptime(arr[1], "%m/%d/%Y")
        t2 = time.strptime(arr[2], "%m/%d/%Y")

        dt1 = mktime(t1) # Original timestamp in seconds
        dt2 = mktime(t2)
        
        #dt1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_wday)
        #dt2 = datetime.datetime(t2.tm_year, t2.tm_mon, t2.tm_wday)

        #dt1 = datetime.combine(date.fromtimestamp(mktime(t1)),datetime.min.time())
        #dt2 = datetime.combine(date.fromtimestamp(mktime(t2)),datetime.min.time())

        modules.append([arr[0],dt1,dt2])


ranges.close()
count = 0

print("Reading repos....")
print("--------------------")

for repo in gh.get_organization(ORG_NAME).get_repos():

    #print(count)
    count += 1

    if(MATCH_NAME != None):
        if(MATCH_NAME not in repo.name.lower()):
            continue

    # datetime.datetime objects
    # Note: while repo.pushed_at should supply the last time a repo was pushed to
    # It seems to provide a date later than the last commmit in some cases
    # An alternative approach is commented out below that gets the last commit from the repo
    # However, it is incredibly slow and would benefit from use in tandum with the -n flag
    created = repo.created_at.timestamp()
    finished = repo.pushed_at.timestamp()


    ###
    ##
    ## Begin alternate commit-based approach 
    ##
    ###
    #last = None
    #finished = repo.get_commits()

    # Optional code for last commit based approach
    # if(finished == None):
    #     continue

    # try:
    #     if(finished.totalCount > 0):
    #         last = finished[finished.totalCount-1]
    #         print("good " + finished.totalCount-1)
    #     else:
    #         continue
    # except:
    #     continue

    # if(last == None):
    #     continue

    # finished = last.commit.author.date.timestamp()
    ###
    ##
    ## End alternate commit-based approach 
    ##
    ###

    for mod in modules:

        if((mod[1] <= created)): # Created in reasonable timespan +DAYS +datetime.timedelta(days=DAYS)  ////  and (created < (mod[2]+DAYS))

            if(finished > mod[2] and (created <= mod[2]+DAYS)): # Finished before deadline
                mod_dict[mod[0]].append(repo.name + "\nCreated At: " + str(repo.created_at) + "\nUpdated At: " + str(repo.pushed_at) + "\n")
                #print("Module: " + mod[0] + ": " + repo.name)
                #print("Repo created: " + str(repo.created_at))
                #print("Repo last updated: " + str(repo.pushed_at))

print("--------------------\nTotal Repos Read: " + str(count) + "\n")
for key in mod_dict.keys():
    print("--------------------")
    print("---- Module: " + key + " ----")
    for item in mod_dict[key]:
        print(item)
print("--------------------")