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

import traceback
from github import Github
import time
from time import mktime
import sys
#import datetime
#from backports.zoneinfo import ZoneInfo
from datetime import date, timedelta

###
## Replace AUTH_TOKEN with your personal github token via:
## Github -> Settings -> Developer Settings -> Personal access tokens -> Generate new token
###
AUTH_TOKEN = ""
ORG_NAME = ""
MATCH_NAME = None
DAYS = 0

# UTC is 4 hours ahead of EST, so we need to subtract this from the gh timestamp
# Note: this script may not run as intended if in another timezone
UTC_OFFSET = 4*60*60 

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



if(AUTH_TOKEN == "" or ORG_NAME == ""):
    sys.exit("Error: Auth token or organization name missing")

syslen = len(sys.argv)

# Total repo count
count = 0
# Named repo count
matched_count = 0

print("For a list of all commands, run `python3 late-repos.py -h`")

# Command line argument invoked
if(syslen > 1):
    if("-h" in sys.argv):
        print("Options:")
        print("     -n [s] only prints repos containing substring s, useful for checking only certain projects")
        print("     -t [d] adds a buffer to the latest day a repo can be created in days")
        print("     -h print this help menu again")
        sys.exit()
    else:
        print("Parsing args...")
    if("-n" in sys.argv):
        n_idx = sys.argv.index("-n")
        if(syslen >= n_idx+1):
            MATCH_NAME = sys.argv[n_idx+1].lower()        
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
    sys.exit("HTTP Request Failed")

try:
    ranges = open("dates.txt")
except FileNotFoundError:
    sys.exit("File not found!")

modules = []
mod_dict = {}
finished = None

for line in ranges:

    arr = line.split(",")
    if(len(arr) != 3):
        print("Skipping line with insufficient length...")
    else:

        mod_dict[arr[0]] = []

        # Convert both dates to time_struct objects
        # Then convert to seconds via mktime()
        t1 = mktime(time.strptime(arr[1], "%m/%d/%Y"))
        t2 = mktime(time.strptime(arr[2], "%m/%d/%Y"))

        modules.append([arr[0],t1,t2])


ranges.close()

print("Reading repos....")

repos = None

try:
    repos = gh.get_organization(ORG_NAME).get_repos()
except:
    sys.exit("Error reading repos...")

for repo in repos:

    count += 1

    progress(count, repos.totalCount)

    if(MATCH_NAME != None):
        if(MATCH_NAME not in repo.name.lower()):
            continue
        else:
            matched_count += 1

    # datetime.datetime objects
    # Note: while repo.pushed_at should supply the last time a repo was pushed to
    # It seems to provide a date later than the last commmit in some cases
    # An alternative approach is commented out below that gets the last commit from the repo
    # However, it is incredibly slow and would benefit from use in tandum with the -n flag
    created = repo.created_at.timestamp()
    finished = (repo.pushed_at-timedelta(seconds=UTC_OFFSET)).timestamp()


    ###
    ##
    ## Begin alternate commit-based approach 
    ## Consider moving this inside of our check for repos created in the right timespan
    ## to cut down on API calls made significantly
    ##
    ###
    # try:
    #     master = repo.get_branch("master")
    # except:
    #     print("no master branch")
    #     finished = repo.updated_at

    # if(finished == None):
    #     print("aaa")
    #     sha_com = master.commit
    #     commit = repo.get_commit(sha=sha_com.sha)
    #     timeObj = commit.commit.author.date

    #     finished = timeObj

    #     utc = ZoneInfo('UTC')
    #     local_timezone = ZoneInfo("localtime")

    #     utc_time = finished.replace(tzinfo=utc)
    #     local = utc_time.astimezone(local_timezone)

    #     finished = local.timestamp()
    #     print(str(finished) + " " + repo.name)
    ###
    ##
    ## End alternate commit-based approach 
    ##
    ###

    for mod in modules:

        if((mod[1] <= created) and (created <= mod[2]+DAYS)): # Created in reasonable timespan
            if(finished > mod[2]): # Finished before deadline
                mod_dict[mod[0]].append(repo.name + "\nCreated At: " + str(repo.created_at-timedelta(seconds=UTC_OFFSET)) + "\nUpdated At: " + str(repo.pushed_at-timedelta(seconds=UTC_OFFSET)) + "\n")
    # Uncomment this line if implementing alternate approach
    #finished = None


# Pretty print dictionary, itemized by module
print("\n\nTotal Repos Read: " + str(count))
if(MATCH_NAME is not None):
    print("Matched Repos Read: " + str(matched_count) + "\n")
else:
    print("\n")
for key in mod_dict.keys():
    print("--------------------\n")
    print("---- Module: " + key + " ----\n")
    for item in mod_dict[key]:
        print(item)
print("--------------------")