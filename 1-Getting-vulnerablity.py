import myutils
import time
import sys
import json
import subprocess
from datetime import datetime
import requests 
import pickle
from pydriller import RepositoryMining
import os
import requests
from requests_oauthlib import OAuth1Session
from requests_oauthlib import OAuth1 



def getChanges(rest):
  
  ### extracts the changes from the pure .diff file
  ### start by parsing the header of the diff
  
  changes = []
  while ("diff --git" in rest):
    filename = ""
    start = rest.find("diff --git")+1
    secondpart = rest.find("index")+1
    #get the title line which contains the file name
    titleline = rest[start:secondpart]
    if not (".py") in rest[start:secondpart]:
      # No python file changed in this part of the commit
      rest = rest[secondpart+1]
      continue
    if "diff --git" in rest[start:]:
      end = rest[start:].find("diff --git");
      filechange = rest[start:end]
      rest = rest[end:]
    else:
      end = len(rest)
      filechange = rest[start:end]
      rest = ""
    filechangerest = filechange
    
    
    while ("@@" in filechangerest):
      ### extract all singular changes, which are recognizable by the @@ marking the line number
      change = ""
      start = filechangerest.find("@@")+2
      start2 = filechangerest[start:start+50].find("@@")+2
      start = start+start2
      filechangerest=filechangerest[start:]
      
      if ("class" in filechangerest or "def" in filechangerest) and "\n" in filechangerest:
        filechangerest = filechangerest[filechangerest.find("\n"):]
      
      if "@@" in filechangerest:
          end = filechangerest.find("@@")
          change = filechangerest[:end]
          filechangerest = filechangerest[end+2:]
          
      else:
        end = len(filechangerest)
        change = filechangerest[:end]
        filechangerest = ""
        
      if len(change) > 0:
        changes.append([titleline,change])
  
  return changes
  
  
def getFilename(titleline):
  #extracts the file name from the title line of a diff file
  s = titleline.find(" a/")+2
  e = titleline.find(" b/")
  name = titleline[s:e]
  
  if titleline.count(name) == 2:
    return name
  elif ".py" in name and (" a"+name+" " in titleline):
    return name
  else:
    print("couldn't find name")
    print(titleline)
    print(name)
  
  
def makechangeobj(changething):
  #for a single change, consisting of titleline and raw code, create a usable object by extracting all relevant info
  
  change = changething[1]
  titleline = changething[0]
  
  if "<html" in change:
    return None
  
  if "sage:" in change or "sage :" in change:
    return None
  
  thischange = {}

  if myutils.getBadpart(change) is not None:      
    badparts = myutils.getBadpart(change)[0]
    goodparts = myutils.getBadpart(change)[1]
    linesadded = change.count("\n+")
    linesremoved = change.count("\n-")
    thischange["diff"] = change
    thischange["add"] = linesadded
    thischange["remove"] = linesremoved
    thischange["filename"] = getFilename(titleline)
    thischange["badparts"] = badparts
    thischange["goodparts"] = []
    if goodparts is not None:
      thischange["goodparts"] = goodparts
    if thischange["filename"] is not None:
      return thischange

  return None



#===========================================================================
# main 



#load list of all repositories and commits
with open('PyCommitsWithDiffs.json', 'r') as infile:
  data = json.load(infile)

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("finished loading ", nowformat)
                


progress = 0
changedict = {}



#default is sql
mode = "sql" 
if (len(sys.argv) > 1):
    mode = sys.argv[1]
  

for mode in ["remote_code_execution","redirect"]:
  
    
      allowedKeywords = ["function injection","remote code","cross frame","csv","redirect","session hijack","session fixation","command injection","sql","xsrf","request forgery","xss","cross site scripting","cross-site scripting","replay attack","unauthorized","unauthorised","brute force","flooding","remote code execution","format string","formatstring","fixation","cross origin","buffer","cache","eval","path","man in the middle","man-in-the-middle","smurf","tamper","saniti","denial","directory","traversal","clickjack","click jack","spoof"]
    #words that should not appear in the filename, because it's a sign that the file is actually part of a demo, a hacking tool or something like that
    suspiciouswords = ["injection", "vulnerability", "exploit", " ctf","capture the flag","ctf","burp","capture","flag","attack","hack"]

    #words that should not appear in the commit message
    badwords = ["sqlmap", "sql-map", "sql_map","ctf "," ctf"]

    progress = 0
    datanew = {}
    
    
    for r in data:

      progress = progress +1
      
      
      #check the repository name
      suspicious = False
      for b in badwords:
        if b.lower() in r.lower():
          suspicious = True
      if suspicious:
        continue


      #skip some repositories that require login
      if("anhday22" in r or "Chaser-wind" in r or "/masamitsu-murase" in r or "joshc/young-goons" in r or "notakang" in r or "sudheer628" in r or "mihaildragos" in r or "aselimov" in r or "tamhidat-api" in r or "aiden-law" in r or "sreeragvv" in r or "LaurenH1090" in r or "/matthewdenaburg1" in r or "haymanjoyce" in r or "/bloctavius" in r or "jordanott/No-Weight-Sharing" in r or "bvanseg" in r or  "sudoku-solver" in r or "tgbot" in r or "lluviaBOT" in r or "jumatberkah" in r or "luisebg" in r or "emredir" in r or "anhday22" in r or "faprioryan" in r or "pablogsal" in r or "zhuyunfeng111" in r or "bikegeek/METplus" in r or "chasinglogic" in r or "Sudhir0547" in r or "fyp_bot" in r):
        continue
      

      changesfromdiff = False
      all_irrelevant = True
      
      changeCommits = []
      for c in data[r]:
        

        irrelevant = True
        for k in allowedKeywords:
          if k.lower() in data[r][c]["keyword"].lower():
            #check if the keywords match with the ones we are looking for
            irrelevant = False

        if irrelevant:
          continue
        
        if not (".py" in data[r][c]["diff"]):
          #doesn't even contain a python file that was changed
          continue    
        

      #  print("\n\n" + r + "/commit/" + c)
      #  print("Keyword: " + data[r][c]["keyword"])
        
        if not "message" in data[r][c]:
          data[r][c]["message"] = ""
        
        #put the commit in a list to check if we get too many duplicates of the same commit (due to forks etc.)
        if not c in changedict:
          changedict[c] = 0
        if c in changedict:
          changedict[c] = changedict[c] + 1
          if changedict[c] > 5:
            #print(" we already have more than five. Skip.")
            continue
        else:
          changedict[c] = 1
        

        
        badparts = {}    
        
        #get all changes that are written down in the diff file
        changes = getChanges(data[r][c]["diff"])
        
        for change in changes:
          
          #make them into usable objects
          thischange = makechangeobj(change)

          if thischange is not None:
            if not "files" in data[r][c]:
              data[r][c]["files"] = {}
            f = thischange["filename"]
            
            if f is not None:
              
              #check the filename for hints that it is an implementation of an attack, a demonstration etc.
              suspicious = False
              for s in suspiciouswords:
                if s.lower() in f.lower():
                  #words should not appear in the filename
                  suspicious = True
                  
              if not suspicious:   
                if not f in data[r][c]["files"]:
                  data[r][c]["files"][f] = {}
                if not "changes" in data[r][c]["files"][f]:
                  data[r][c]["files"][f]["changes"] = []
                data[r][c]["files"][f]["changes"].append(thischange)
                changesfromdiff = True
                changeCommits.append(c)
            
      if changesfromdiff:
          #if any changes in this diff were useful...we get the sourcecode for those files using pydriller
          print("\n\n" + mode + "    mining "  + r + " " + str(progress) + "/" + str(len(data)))

          commitlist = []
          try:
            for commit in RepositoryMining(r).traverse_commits():
              commitlist.append(commit.hash)              

              #go through all commits in the repository mining and check if they match with one of the commits that are of interest
              if not commit.hash in changeCommits:
                continue
              
              for m in commit.modifications:                  
                  #run through all modifications in the single commit in the repository mining
                  if m.old_path != None and m.source_code_before != None:
                    if not ".py" in m.old_path:
                      continue
                    
                    #ignore files that are too large
                    if len(m.source_code_before) > 30000:
                      continue
                      
                    #print("\n  modification with old path: " + str(m.old_path))
                    for c in data[r]: 
                        if c == commit.hash:   
                          #run through commits we have for that repository until the match is found
                          print("  found commit " + c)
                          if not "files" in data[r][c]:
                            print("  no files :(") #rarely ever happens
                          data[r][c]["msg"] = commit.msg #get the commit message from the repository mining, check it for suspicious words
                          for badword in badwords:
                            if badword.lower() in commit.msg.lower():
                              suspicious = True
                          if suspicious:
                            print("  suspicious commit msg: \"" + commit.msg.replace("\n"," ")[:300] + "...\"")
                            continue
                          
                          #print("  The commit has " + str(len(data[r][c]["files"])) + " files.")
                          for f in data[r][c]["files"]:
                              
                              #find the file that was changed in the modification we are at
                              if m.old_path in f:

                                #grab the sourcecode and save it: before without comments, before with comments, and after with comments
                                if not ("source" in data[r][c]["files"][f] and (len(data[r][c]["files"][f]["source"])> 0)):
                                  sourcecode = "\n" + myutils.removeDoubleSeperatorsString(myutils.stripComments(m.source_code_before))
                                  data[r][c]["files"][f]["source"] = sourcecode

                                if not ("sourceWithComments" in data[r][c]["files"][f] and (len(data[r][c]["files"][f]["sourceWithComments"])> 0)):
                                  data[r][c]["files"][f]["sourceWithComments"] = m.source_code_before
                                
                                if not ("sourceWithComments" in data[r][c]["files"][f] and (len(data[r][c]["files"][f]["sourceWithComments"])> 0)):
                                  data[r][c]["files"][f]["sourcecodeafter"] = ""
                                  if m.source_code is not None:
                                    data[r][c]["files"][f]["sourcecodeafter"] = m.source_code   
                                
                                if not r in datanew:
                                  datanew[r] = {}
                                if not c in datanew[r]:
                                  datanew[r][c] = {}
                                  
                                #save it in the new dataset
                                datanew[r][c] = data[r][c]
                                print("     ->> added to the dataset.")
                                  
          except Exception as e:
              print("Exception occured.")
              print(e)
              time.sleep(2)
              continue



    print("done.")
    print(len(data))  

    #save dataset
    with open('data/PyCommitsWithDiffs' + mode, 'w') as outfile:
      json.dump(datanew, outfile)





def searchforkeyword(key, commits, access):
  #collect links from the github API response
  maximum = 9999  
  new = 0


  #craft request for Github
  params = (
      ('q', key),('per_page',100)
  )
  myheaders = {'Accept': 'application/vnd.github.cloak-preview', 'Authorization': 'token ' + access}
  nextlink = "https://api.github.com/search/commits"

  for i in range(0,maximum):
      print(str(len(commits)) + " commits so far.")
      print
      limit = 0
      while(limit == 0):
          #request search results
          response = requests.get(nextlink, headers=myheaders,params=params)
          h = response.headers
          if 'X-RateLimit-Remaining' in h:
            limit = int(h['X-RateLimit-Remaining'])
            if limit == 0:
                # Limit of requests per time was reached, sleep to wait until we can request again
                print("Rate limit. Sleep.")
                time.sleep(35)
            #else:
            #  print(h)
      if 'Link' not in h:
        break;
      
      #go through all elements in Github's reply
      content = response.json()
      for k in range(0, len(content["items"])):
          #get relevant info
          repo = content["items"][k]["repository"]["html_url"]
          if repo not in commits:
              #new repository, new commit
              c = {}
              c["url"] = content["items"][k]["url"]
              c["html_url"] = content["items"][k]["html_url"]
              c["message"] = content["items"][k]["commit"]["message"]
              c["sha"] = content["items"][k]["sha"]
              c["keyword"] = key
              commits[repo] = {}
              commits[repo][content["items"][k]["sha"]] = c;
          else:
              if not content["items"][k]["sha"] in commits[repo]:
                #new commit for this already known repository
                new = new + 1
                c = {}
                c["url"] = content["items"][k]["url"]
                c["html_url"] = content["items"][k]["html_url"]
                c["sha"] = content["items"][k]["sha"]
                c["keyword"] = key
                commits[repo][content["items"][k]["sha"]] = c;
                
                
      #get the links to the next results
      link = h['Link']
      reflinks = analyzelinks(link)
      if "last" in reflinks:
          lastnumber = reflinks["last"].split("&page=")[1]
          maximum = int(lastnumber)-1
      if not "next" in reflinks:
          #done with all that could be collected
          break
      else:
          nextlink = reflinks["next"]
          
  #save the commits that were found
  with open('all_commits.json', 'w') as outfile:
      json.dump(commits, outfile)



def analyzelinks(link):
    #get references to the next page of results
    
    link = link + ","
    reflinks = {}
    while "," in link:
        pos = link.find(",")
        text = link[:pos]
        rest = link[pos+1:]
        try:
          if "\"next\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["next"]=text
          if "\"prev\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["prev"]=text
          if "\"first\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["first"]=text
          if "\"last\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["last"]=text
        except IndexError as e:
            print(e)
            print("\n")
            print(text)
            print("\n\n")
            sys.exit()
        link = rest
    return(reflinks)





#------------------------------------



if not os.path.isfile('access'):
  print("please place a Github access token in this directory.")
  sys.exit()
  
with open('access', 'r') as accestoken:
  access = accestoken.readline().replace("\n","")

commits = {}

#load previously scraped commits
with open('all_commits.json', 'r') as infile:
    commits = json.load(infile)
    

keywords = ["buffer overflow","denial of service", "dos", "XXE","vuln","CVE","XSS","NVD","malicious","cross site","exploit","directory traversal","rce","remote code execution","XSRF","cross site request forgery","click jack","clickjack","session fixation","cross origin","infinite loop","brute force","buffer overflow","cache overflow","command injection","cross frame scripting","csv injection","eval injection","execution after redirect","format string","path disclosure","function injection","replay attack","session hijacking","smurf","sql injection","flooding","tampering","sanitize","sanitise", "unauthorized", "unauthorised"]

prefixes =["prevent", "fix", "attack", "protect", "issue", "correct", "update", "improve", "change", "check", "malicious", "insecure", "vulnerable", "vulnerability"]

#for all combinations of keywords and prefixes, scrape github for commits
for k in keywords:
  for pre in prefixes:
      searchforkeyword(k + " " + pre, commits, access);



repositories = {}
data = {}


#get mined commits
repositories = {}
with open('all_commits.json', 'r') as infile:
    repositories = json.load(infile)
    
#load progress
if os.path.isfile('DataFilter.json'):
  with open('DataFilter.json', 'r') as infile:
      data = json.load(infile)


if not "showcase" in data:
  data["showcase"] = {}
if not "noshowcase" in data:
  data["noshowcase"] = {}
    
    

toomuchsecurity = ['offensive', 'pentest', 'vulnerab', 'security', 'hack', 'exploit', 'ctf ', ' ctf', 'capture the flag','attack'] #keywords that are not allowed to appear in the repository name
alittletoomuch = ['offensive security', 'pentest', 'exploits', 'vulnerability research', 'hacking', 'security framework', 'vulnerability database', 'simulated attack', 'security research'] #keywords that are not allowed to appear in the readme description



#get access token
if not os.path.isfile('access'):
  print("please place a Github access token in this directory.")
  sys.exit()
with open('access', 'r') as accestoken:
  access = accestoken.readline().replace("\n","")
myheaders = {'Authorization': 'token ' + access}


for repo in repositories:
    #get name of the repository
    name = repo.split('https://github.com/')[1]
    
    #if we don't know yet if it is a showcase...
    if (name in data['showcase']):
        continue
    if (name in data['noshowcase']):
        continue
    
    #check all the 'toomuch' keywords to see if they already appear in the name of the repository
    for toomuch in toomuchsecurity:
      if toomuch in name:
        #put it in the showcase categpry
        data['showcase'][name] = {}
        print(name + ": showcase")
        continue

    #get the readme of the repository
    response = requests.get('https://github.com/'+name+'/blob/master/README.md', headers = myheaders)        
    h = response.headers
            
    if ("markdown-body") in response.text:
      #find the description of the project
      pos = response.text.find("markdown-body")
      pos2 = response.text.find("/article")
      description = response.text[pos:pos2]
      
      #check all keywords from the 'alittletoomuch' category
      for toomuch in alittletoomuch: 
        if toomuch in description:
          #put it in the showcase category
          data['showcase'][name] = {}
          print(name + ": showcase")
          continue
      

    #otherwise, put it in the "noshowcase" category
    print(name + ": not a showcase")
    data['noshowcase'][name] = {}
      
    with open('DataFilter.json', 'w') as outfile:
          json.dump(data, outfile)



