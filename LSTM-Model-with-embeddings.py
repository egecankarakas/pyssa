import utils
import sys
import os.path
import json
from datetime import datetime
import random
import pickle
import numpy
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.preprocessing import sequence
from keras import backend as K
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.utils import class_weight
import tensorflow as tf
from gensim.models import Word2Vec, KeyedVectors
from gensim.models import FastText, KeyedVectors
from transformers import RobertaTokenizer, RobertaConfig, RobertaModel, TFAutoModel
import torch
from bert_embedding import BertEmbedding



mincount = 10
iterationen = 100
s = 200 
w = "withString" 


w2v = "word2vec_"+w+str(mincount) + "-" + str(iterationen) +"-" + str(s)
w2vmodel = "Word2v-embbeding/" + w2v + ".model"

#f2v = "fasttext_"+w+str(mincount) + "-" + str(iterationen) +"-" + str(s)
#f2vmodel = "FastText-embbeding/" + f2v + ".model"

#bert_embedding = BertEmbedding()

if not (os.path.isfile(w2vmodel)):
  print("word2vec model is still being created...")
  print("w2vmodel")
  sys.exit()


model = Word2Vec.load(w2vmodel)
word_vectors = model.wv


#model = FastText.load(f2vmodel)
#word_vectors = f2v_model.wv


with open('data/PyCommitsWithDiffs' , 'r') as infile:
  data = json.load(infile)
  
now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("finished loading. ", nowformat)


progress = 0
count = 0


restriction = [20000,5,6,10] 
step = 5 
fulllength = 200 

allblocks = []

for r in data:
  progress = progress + 1
  
  for c in data[r]:
    
    if "files" in data[r][c]:                      
      
      for f in data[r][c]["files"]:
        
        
        if not "source" in data[r][c]["files"][f]:
 
          continue
        
        if "source" in data[r][c]["files"][f]:
          sourcecode = data[r][c]["files"][f]["source"]                          
          
          allbadparts = []
          
          for change in data[r][c]["files"][f]["changes"]:
                             
                badparts = change["badparts"]
                count = count + len(badparts)
                                
                for bad in badparts:
    
                  pos = utils.findposition(bad, sourcecode)
                  if not -1 in pos:
                      allbadparts.append(bad)
                      
                      
          if(len(allbadparts) > 0):
              positions = utils.findpositions(allbadparts, sourcecode)

              blocks = utils.getblocks(sourcecode, positions, step, fulllength)
              
              for b in blocks:

                  allblocks.append(b)


keys = []

for i in range(len(allblocks)):
  keys.append(i)
random.shuffle(keys)


cutoff = round(0.7 * len(keys)) 
cutoff2 = round(0.85 * len(keys)) 

keystrain = keys[:cutoff]
keystest = keys[cutoff:cutoff2]
keysfinaltest = keys[cutoff2:]

print("cutoff " + str(cutoff))
print("cutoff2 " + str(cutoff2))


with open('data/dataset_keystrain', 'wb') as fp:
  pickle.dump(keystrain, fp)
with open('data/dataset_keystest', 'wb') as fp:
  pickle.dump(keystest, fp)
with open('data/dataset_keysfinaltest', 'wb') as fp:
  pickle.dump(keysfinaltest, fp)

TrainX = []
TrainY = []
ValidateX = []
ValidateY = []
FinaltestX = []
FinaltestY = []


print("Creating training dataset... ")
for k in keystrain:
  block = allblocks[k]    
  code = block[0]
  token = utils.getTokens(code) 
  vectorlist = []
  for t in token: 
    if t != " " and word_vectors.key_to_index.get(t):
      vector = model.wv.get_vector(t)
      vectorlist.append(vector.tolist()) 
  TrainX.append(vectorlist) 
  TrainY.append(block[1]) 

print("Creating validation dataset...")
for k in keystest:
  block = allblocks[k]
  code = block[0]
  token = utils.getTokens(code) 
  vectorlist = []
  for t in token: 
    if t != " " and word_vectors.key_to_index.get(t):
      vector = model.wv.get_vector(t)
      vectorlist.append(vector.tolist()) 
  ValidateX.append(vectorlist) 
  ValidateY.append(block[1]) 

print("Creating finaltest dataset...")
for k in keysfinaltest:
  block = allblocks[k]  
  code = block[0]
  token = utils.getTokens(code) 
  vectorlist = []
  for t in token: 
    if t != " " and word_vectors.key_to_index.get(t):
      vector = model.wv.get_vector(t)
      vectorlist.append(vector.tolist()) 
  FinaltestX.append(vectorlist) 
  FinaltestY.append(block[1]) 

#for bert
#print("Creating training dataset... ")
#for k in keystrain:
  #block = allblocks[k]    
  #code = block[0]
  #sentences = code.split('\n')
  #result = bert_embedding(sentences)
  #for i in range(len(result)):
    #token = result[i]
    #tokens = token[1]
  #TrainX.append(tokens) 
  #TrainY.append(block[1]) 

#print("Creating validation dataset...")
#for k in keystest:
  #block = allblocks[k]
  #code = block[0]
  #sentences = code.split('\n')
  #result = bert_embedding(sentences)
  #for i in range(len(result)):
   #token = result[i]
    #tokens = token[1]
  #ValidateX.append(tokens) 
  #ValidateY.append(block[1]) 

#print("Creating finaltest dataset...")
#for k in keysfinaltest:
  #block = allblocks[k]  
  #code = block[0]
  #sentences = code.split('\n')
  #result = bert_embedding(sentences)
  #for i in range(len(result)):
    #token = result[i]
    #tokens = token[1]
  #FinaltestX.append(tokens)  
  #FinaltestY.append(block[1]) 


print("Train length: " + str(len(TrainX)))
print("Test length: " + str(len(ValidateX)))
print("Finaltesting length: " + str(len(FinaltestX)))
now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("time: ", nowformat)



X_train =  numpy.array(TrainX)
y_train =  numpy.array(TrainY)
X_test =  numpy.array(ValidateX)
y_test =  numpy.array(ValidateY)
X_finaltest =  numpy.array(FinaltestX)
y_finaltest =  numpy.array(FinaltestY)
print(X_train.shape)
for i in range(len(y_train)):
  if y_train[i] == 0:
    y_train[i] = 1
  else:
    y_train[i] = 0
    
for i in range(len(y_test)):
  if y_test[i] == 0:
    y_test[i] = 1
  else:
    y_test[i] = 0
    
for i in range(len(y_finaltest)):
  if y_finaltest[i] == 0:
    y_finaltest[i] = 1
  else:
    y_finaltest[i] = 0


now = datetime.now() 
nowformat = now.strftime("%H:%M")
print("numpy array done. ", nowformat)

print(str(len(X_train)) + " samples in the training set.")      
print(str(len(X_test)) + " samples in the validation set.") 
print(str(len(X_finaltest)) + " samples in the final test set.")
  
csum = 0
for a in y_train:
  csum = csum+a
print("percentage of vulnerable samples: "  + str(int((csum / len(X_train)) * 10000)/100) + "%")
  
testvul = 0
for y in y_test:
  if y == 1:
    testvul = testvul+1
print("absolute amount of vulnerable samples in test set: " + str(testvul))

max_length = fulllength 
  

#hyperparameters for the LSTM model

dropout = 0.2
neurons = 100
optimizer = "adam"
epochs = 100
batchsize = 128

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("Starting LSTM: ", nowformat)


print("Dropout: " + str(dropout))
print("Neurons: " + str(neurons))
print("Optimizer: " + optimizer)
print("Epochs: " + str(epochs))
print("Batch Size: " + str(batchsize))
print("max length: " + str(max_length))


X_train = sequence.pad_sequences(X_train, maxlen=100, dtype='float32')
X_test = sequence.pad_sequences(X_test, maxlen=100, dtype='float32')
X_finaltest = sequence.pad_sequences(X_finaltest, maxlen=100, dtype='float32')

#creating the model  
model = Sequential()
model.add(LSTM(neurons, dropout = dropout, recurrent_dropout = dropout)) #around 50 seems good
model.add(Dense(1, activation='sigmoid'))
model.compile(loss=utils.f1_loss, optimizer='adam', metrics=[utils.f1])

now = datetime.now() 
nowformat = now.strftime("%H:%M")
print("Compiled LSTM: ", nowformat)


class_weights = class_weight.compute_class_weight('balanced', numpy.unique(y_train), y_train)
class_weights = dict(enumerate(class_weights))
y_train = tf.cast(y_train, tf.float32)

history = model.fit(X_train, y_train, epochs=epochs, batch_size=batchsize, class_weight=class_weights)



for dataset in ["train","test","finaltest"]:
    print("Now predicting on " + dataset + " set (" + str(dropout) + " dropout)")
    
    if dataset == "train":
      yhat_classes = (model.predict(X_train) > 0.5).astype("float32")
      accuracy = accuracy_score(y_train, yhat_classes)
      precision = precision_score(y_train, yhat_classes)
      recall = recall_score(y_train, yhat_classes)
      F1Score = f1_score(y_train, yhat_classes)
      
    if dataset == "test":
      yhat_classes = (model.predict(X_test) > 0.5).astype("float32")
      accuracy = accuracy_score(y_test, yhat_classes)
      precision = precision_score(y_test, yhat_classes)
      recall = recall_score(y_test, yhat_classes)
      F1Score = f1_score(y_test, yhat_classes)
      
      
    if dataset == "finaltest":
      yhat_classes = (model.predict(X_finaltest) > 0.5).astype("float32")
      accuracy = accuracy_score(y_finaltest, yhat_classes)
      precision = precision_score(y_finaltest, yhat_classes)
      recall = recall_score(y_finaltest, yhat_classes)
      F1Score = f1_score(y_finaltest, yhat_classes)
      
    print("Accuracy: " + str(accuracy))
    print("Precision: " + str(precision))
    print("Recall: " + str(recall))
    print('F1 score: %f' % F1Score)
    print("\n")



now = datetime.now() 
nowformat = now.strftime("%H:%M")
print("saving LSTM model "  ". ", nowformat)
model.save('model/LSTM_model.h5')  
print("\n\n")



