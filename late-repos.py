from github import Github
import time
from time import mktime
import sys
from datetime import date

###
## Replace AUTH_TOKEN with your personal github token via:
## Github -> Settings -> Developer Settings -> Personal access tokens -> Generate new token
###
AUTH_TOKEN = ""
ORG_NAME = ""

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

        dt1 = mktime(t1)
        dt2 = mktime(t2)
        modules.append([arr[0],dt1,dt2])


ranges.close()

for repo in gh.get_organization(ORG_NAME).get_repos():

    # datetime.datetime objects
    created = repo.created_at.timestamp()
    finished = repo.pushed_at.timestamp()


    for mod in modules:

        if((mod[1] <= created) and (created <= mod[2])): # Created in reasonable timespan

            if(finished >= mod[2]):
                print(repo.name + " is late")
                print(str(date.fromtimestamp(created)) + " " + str(date.fromtimestamp(finished)) + " " + repo.name)
                print(str(created) + " " + str(finished) + " " + repo.name)
                print(str(modules[0][1]) + " " + str(modules[0][2]) + " " + repo.name + "\n")