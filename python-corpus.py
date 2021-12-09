from pydriller import RepositoryMining
import sys
import StringIO
import subprocess
import time
import sys




repos = ["https://github.com/numpy/numpy", "https://github.com/django/django", "https://github.com/scikit-learn/scikit-learn", "https://github.com/tensorflow/tensorflow", "https://github.com/keras-team/keras","https://github.com/ansible/ansible", "https://github.com/TheAlgorithms/Python", "https://github.com/pallets/flask", "https://github.com/ytdl-org/youtube-dl", "https://github.com/pandas-dev/pandas", "https://github.com/scrapy/scrapy", "https://github.com/kennethreitz/requests", "https://github.com/home-assistant/home-assistant", "https://github.com/ageitgey/face_recognition","https://github.com/emesik/mamona","https://github.com/progrium/notify-io","https://github.com/phoenix2/phoenix","https://github.com/odoo/odoo","https://github.com/ageitgey/face_recognition","https://github.com/psf/requests","https://github.com/deepfakes/faceswap","https://github.com/XX-net/XX-Net","https://github.com/tornadoweb/tornado","https://github.com/saltstack/salt","https://github.com/matplotlib/matplotlib","https://github.com/celery/celery","https://github.com/binux/pyspider","https://github.com/miguelgrinberg/flasky","https://github.com/sqlmapproject/sqlmap","https://github.com/zulip/zulip","https://github.com/scipy/scipy","https://github.com/bokeh/bokeh","https://github.com/docker/compose","https://github.com/getsentry/sentry","https://github.com/timgrossmann/InstaPy","https://github.com/divio/django-cms","https://github.com/boto/boto"]

pythontraining = ""

for r in repos:
  print(r)
  files = []
  for commit in RepositoryMining(r).traverse_commits():
      for m in commit.modifications:
        filename = m.new_path
        
        if filename is not None:
          if ".py" in filename:
            if not filename in files:
              code = m.source_code
              if code is not None:
                pythontraining = pythontraining + "\n\n" + code
                files.append(filename)
        
          
  with open('w2v/pythontraining.txt', 'w') as outfile:
    outfile.write(pythontraining)


#remoe some broken code in the corpus

f=open("w2v/pythontraining.txt", "r")
contents =f.read()
contents = contents.replace('\t', '    ')

if 'PositiveSmallIntegerField(\n                choices' in contents:
    pos = contents.find('PositiveSmallIntegerField(\n                choices')
    contents = contents[:pos-198] + contents[pos+178:]

if "            raise ImportError,self.__dict__.get('_ppimport_exc_info')[1]" in contents:
  pos = contents.find("            raise ImportError,self.__dict__.get('_ppimport_exc_info')[1]")
  length = len("            raise ImportError,self.__dict__.get('_ppimport_exc_info')[1]")
  contents = contents[:pos] + contents[pos+length+1:]

if "[k]*step+start)" in contents:
  pos = contents.find("[k]*step+start)")
  contents = contents[:pos+17] + contents[pos+21:]
badstring = ["silly_field", "('id', models.AutoField(primary_key=True))"]

while "check_framework.Model2." in contents:
  pos = contents.find("check_framework.Model2.")
  area = contents[pos-300:pos+300]
  start = area.find("class")
  end = area.find("def")  
  contents = contents[:pos-300+start] + contents[pos-300+end:]

fromhere = 0
while "DEFAULT_KMS_KEY_NAME" in contents[fromhere:] and "ENCRYPTION_CONFIG" in contents[fromhere:fromhere+2000]:
  pos = fromhere + contents[fromhere:].find("DEFAULT_KMS_KEY_NAME")
  area = contents[pos-1000:pos+1000]
  start = area[:1000].find("class")
  if (start == -1):
    start = area[:1000].find("from")
  if (start == -1):
    start = area[:1000].find("import")
  if (start == -1):
    start = area[:1000].find("def")
    
  end = area[1000:].find("def")
  if (end == -1):
    end = area[1000:].find("from")
  if (end == -1):
    end = area[1000:].find("import")
  
  print("Found it at  " + str(pos))
#    print(len(contents))
  if (start > 0 and end > 0):
    contents = contents[:pos-1000+start] + contents[pos-1000+end:]
    fromhere = pos-1000+start+end+1
    print("countinue at " + str(fromhere))
    print(start)
    print(end)
  else:
    fromhere = pos + 1000
  
 
fromhere = 0
while "somepassword" in contents[fromhere:]:
  pos = fromhere + contents[fromhere:].find("somepassword")
  area = contents[pos-1000:pos+1000]
  start = area.find("def")
  end = area[1000:].find("def")
  if (end == -1):
    end = area[1000:].find("from")
  if (end == -1):
    end = area[1000:].find("import")
  if start > 0 and end > 0:
    contents = contents[:pos-1000+start] + contents[pos+end:]
    fromhere = pos-1000+start

  else:
    fromhere = pos + 1
  
  
if "somepassword" in contents and "someuser" in contents and "somehost" in contents:
  pos = contents.find("somepassword")

for x in badstring:
  while(x in contents):    
    pos = contents.find(x)    
    area = contents[pos-500:pos+1000]            
    if("db.create_table" in area):
      contents = contents.replace("('id', models.AutoField(primary_key=True))","('id', models.AutoField(primary_key=False))",1)
      continue    
    start = area.find("class")    
    restarea = area[start:]    
    end = restarea.find("from") + start
    end2 = restarea.find("import") + start    
    if end2 < end:
      end = end2 
    if (end > start):
      contents = contents[:pos-500+start] + contents[pos-500+end:]
 
 
f = open("w2v/pythontraining_edit.txt", "w")
f.write(contents)
f.close()    


pythondata = ""

#mode = "withString" #default
mode = "withoutString"    


if (len(sys.argv) > 1):
    mode = sys.argv[1]
    
#use the python tokenizer to tokenize the words in the corpus

p = subprocess.Popen(["python", "-m", "tokenize", "w2v/pythontraining" + "_edit.txt"], stdout=subprocess.PIPE)
out, err = p.communicate()

s = StringIO.StringIO(out)
count = 0
totalcount = 0
comment = 0
part = 0

for line in s:
    totalcount = totalcount+1
    count = count+1
    if(totalcount%1000 == 0):
      print(totalcount)
    position1 = line.find(":")+1
    position2 = line.find("'")
    position3 = line[position2+1:].find("'")
    
    cat = line[position1:position2]
    content = line[position2+1:-2]
    
    if ('"""' in line):
      comment = comment+1
      continue
    
    if ("COMMENT" in  cat):
      comment = comment+1
      continue
    
    
    if (mode == "withoutString"):
      if ("STRING" in cat):
        stringstart = line.find("\"")
        content = line[stringstart+1:-2]
        content = "\"string\""
    if ("NL" in cat) or ("NEWLINE" in cat):
      pythondata = pythondata + "\n"
    elif ("INDENT" in cat):
      for x in range(content.count('t')):
        pythondata = pythondata + "  "
    else:
      pythondata = pythondata + " " + content

    #save in parts to reduce computational load
    if count > 1000000:
      print("saving part " + str(part) + " (" + mode + ") " + str(totalcount))
      with open('w2v/pythontraining'+"_"+mode+"_"+str(part), 'w') as outfile:
        outfile.write(pythondata)
      pythondata = ""
      part = part+1
      count = 0

with open('w2v/pythontraining'  +"_"+mode+"_"+str(part), 'w') as outfile:
  outfile.write(pythondata)

fulltext = ""
text = []
for i in range(0,71):
  f=open("w2v/pythontraining_" + mode + "_" + str(i), "r")
  contents =f.read()
  fulltext = fulltext + contents
  print("loaded " + str(i))
with open('w2v/pythontraining_'+mode+"_X", 'w') as outfile:
  outfile.write(fulltext)
