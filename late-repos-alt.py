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

gh = Github(AUTH_TOKEN)

try:
    ranges = open("dates.txt")
except FileNotFoundError:
    sys.exit("File not found!")

modules = []

for line in ranges:

    arr = line.split(",")
    if(len(arr) != 3):
        print("Skipping line with insufficient length...")
    else:

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

try:
    for repo in gh.get_organization(ORG_NAME).get_repos():

        if(MATCH_NAME != None):
            if(MATCH_NAME not in repo.name.lower()):
                continue

        # datetime.datetime objects
        created = repo.created_at.timestamp()
        #finished = repo.pushed_at.timestamp()




        finished = repo.get_commits()


        
        #created = repo.created_at
        #finished = repo.pushed_at

        for mod in modules:

            if((mod[1] <= created)): # Created in reasonable timespan +DAYS +datetime.timedelta(days=DAYS)  ////  and (created < (mod[2]+DAYS))

                if(finished > mod[2] and (created <= mod[2]+DAYS)): # Finished before deadline
                    print("--------------------\n" + mod[0] + ": " + repo.name)
                    print("Repo last updated: " + str(repo.pushed_at) + "\n--------------------\n")
                    print("Deadline " + str(mod[2]))
                    #print("Repo last updated: " + str(date.fromtimestamp(finished)) + "\n--------------------\n")
                    
                    #print(str(date.fromtimestamp(created)) + " " + str(date.fromtimestamp(finished)) + " " + repo.name)
                    #print(str(created) + " " + str(finished) + " " + repo.name)
                    #print(str(modules[0][1]) + " " + str(modules[0][2]) + " " + repo.name + "\n")
            # else:
            #     if(MATCH_NAME in repo.name.lower()):
            #         print("--------------------\n" + mod[0] + ": " + repo.name + " Created after deadline")
            #         print("Repo created: " + str(date.fromtimestamp(created)) + "\n--------------------\n")           

            # if(MATCH_NAME is not None):
            #     if((created > mod[2]) and (MATCH_NAME in repo.name.lower())):
            #         print("--------------------\n" + mod[0] + ": " + repo.name + " may be created after deadline")
            #         print("Repo created: " + str(created) + " " + " Deadline " + str(mod[2]) + "\n--------------------\n")
            #         #print("Repo created: " + str(date.fromtimestamp(created)) + " " + " Deadline " + str(date.fromtimestamp(mod[2])) + "\n--------------------\n")
except:
    print("HTTP Request Failed")
