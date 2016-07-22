# -*- coding: utf-8 -*-
"""
    Created in Thu March  22 10:47:00 2016
    
    @author: Remi Eyraud & Sicco Verwer
    
    Tested with Python 2.7.11 and Python 3.4
"""

"""

Modified on Mon May 2 2016

@author: Vinh Dang

"""

import getopt,sys

# State the problem number
problem_number = '0'

# and the user id (given during registration)
user_id = '42'

# name of this submission (no space or special character)

name = "3gram_Baseline"

# use public or private test set
data_type = "public" #"public","private"

from numpy import *
from decimal import *
from sys import *

try:
      opts, args = getopt.getopt(sys.argv[1:],"hp:d:n:",["problem=","data=","name="])
except getopt.GetoptError:
      print "Usage"
      print sys.argv[0] 
      print "--problem=/-p" + " problem_number"
      print "--data=/-d + public/private"
      print "--name=/-n +algorithm_name"
      print sys.argv[0] + " -h for help"
      sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print "Usage"
        print sys.argv[0] 
        print "--problem=/-p" + " problem_number"
        print "--data=/-d + public/private"
        print "--name=/-n +algorithm_name"
        print sys.argv[0] + " -h for help"
        sys.exit ()
    elif opt in ("-p","--problem"):
        problem_number = arg
    elif opt in ("-d","--data"):
        data_type = arg
    elif opt in ("-n","--name"):
        name = arg

problem_dir = "spice/p" + str (problem_number)

train_file = problem_dir + "/" + problem_number + ".spice.train"
prefix_file = problem_dir + "/" + problem_number + ".spice.public.test"
if (data_type == "private"):
    prefix_file = problem_dir + "/" + problem_number + ".spice.private.test"

def number(arg):
    return Decimal(arg)

def threegramdict(sett):
 DPdict = dict()
 total = 0
 for sequence in sett:
     ngramseq = [-1,-1] + sequence + [-2]
     for start in range(len(ngramseq)-2):
         total
         end = start + 2
         if tuple(ngramseq[start:end]) in DPdict:
             table = DPdict[tuple(ngramseq[start:end])]
             if ngramseq[end] in table:
                 table[ngramseq[end]] = table[ngramseq[end]] + 1
             else:
                 table[ngramseq[end]] = 1
             table[-1] = table[-1] + 1
         else:
             table = dict()
             table[ngramseq[end]] = 1
             table[-1] = 1
             DPdict[tuple(ngramseq[start:end])] = table
 return DPdict

def threegramrank(prefix, alphabet, DPdict):
    probs=[]
    # Compute the probability for prefix to be a whole sequence
    prob = number('1.0')
    ngramseq = [-1,-1] + prefix + [-2]
    for start in range(len(ngramseq)-2):
        end = start + 2
        if tuple(ngramseq[start:end]) in DPdict and ngramseq[end] in DPdict[tuple(ngramseq[start:end])]:
            prob = prob * (number(DPdict[tuple(ngramseq[start:end])][ngramseq[end]]) / number(DPdict[tuple(ngramseq[start:end])][-1]))
        else:
            # Subsequence not in the dictionnary
            prob = number(0)
    probs.append((-1,prob))
    for x in range(alphabet):
        prob = number('1.0')
        ngramseq = [-1,-1] + prefix + [x]
        for start in range(len(ngramseq)-2):
            end = start + 2
            if tuple(ngramseq[start:end]) in DPdict and ngramseq[end] in DPdict[tuple(ngramseq[start:end])]:
                prob = prob * (number(DPdict[tuple(ngramseq[start:end])][ngramseq[end]]) / number(DPdict[tuple(ngramseq[start:end])][-1]))
            else:
                # Subsequence not in the dictionnary
                prob=number(0)
        probs.append((x,prob))
    probs=sorted(probs, key=lambda x: -x[1])
    return [x[0] for x in probs]

def readset(f):
 sett = []
 line = f.readline()
 l = line.split(" ")
 num_strings = int(l[0])
 alphabet_size = int(l[1])
 for n in range(num_strings):
     line = f.readline()
     l = line.split(" ")
     sett = sett + [[int(i) for i in l[1:len(l)]]]
 return alphabet_size, sett

def get_first_prefix(test_file):
    """ get the only prefix in test_file """
    f = open(test_file)
    prefix = f.readline()
    f.close()
    return prefix

def list_to_string(l):
    s=str(l[0])
    for x in l[1:]:
        s+= " " + str(x)
    return(s)

def formatString(string_in):
    """ Replace white spaces by %20 """
    return string_in.strip().replace(" ", "%20")

print("Get training sample")
alphabet, train = readset(open(train_file,"r"))
print ("Start Learning")
dict=threegramdict(train)
print ("Learning Ended")

# get the test first prefix: the only element of the test set
first_prefix = get_first_prefix(prefix_file)
prefix_number=1

# get the next symbol ranking on the first prefix
p=first_prefix.split()
prefix=[int(i) for i in p[1:len(p)]]
ranking = threegramrank(prefix, alphabet, dict)
ranking_string=list_to_string(ranking[:5])

print("Prefix number: " + str(prefix_number) + " Ranking: " + ranking_string + " Prefix: " + first_prefix)

# transform the first prefix to follow submission format
first_prefix = formatString(first_prefix)

# transform the ranking to follow submission format
ranking_string=formatString(ranking_string)

# create the url to submit the ranking
url_base = 'http://spice.lif.univ-mrs.fr/submit.php?user=' + user_id +\
    '&problem=' + problem_number + '&submission=' + name + '&'
url = url_base + 'prefix=' + first_prefix + '&prefix_number=1' + '&ranking=' +\
    ranking_string

# Get the website answer for the first prefix with this ranking using this
# submission name
try:
    # Python 2.7
    import urllib2 as ur
    orl2 = True
except:
    #Python 3.4
    import urllib.request as ur
    orl2 = False

response = ur.urlopen(url)
content = response.read()

if not orl2:
    # Needed for python 3.4...
    content= content.decode('utf-8')

list_element = content.split()
head = str(list_element[0])

prefix_number = 2

while(head != '[Error]' and head != '[Success]'):
    prefix = content[:-1]
    # Get the ranking
    p=prefix.split()
    prefix_list= list()
    prefix_list=[int(i) for i in p[1:len(p)]]
    ranking = threegramrank(prefix_list, alphabet, dict)
    ranking_string=list_to_string(ranking[:5])
    
    print("Prefix number: " + str(prefix_number) + " Ranking: " + ranking_string + " Prefix: " + prefix)
    
    # Format the ranking
    ranking_string = formatString(ranking_string)
    
    # create prefix with submission needed format
    prefix=formatString(prefix)
    
    # Create the url with your ranking to get the next prefix
    url = url_base + 'prefix=' + prefix + '&prefix_number=' +\
        str(prefix_number) + '&ranking=' + ranking_string
    
    # Get the answer of the submission on current prefix
    response = ur.urlopen(url)
    content = response.read()
    if not orl2:
        # Needed for Python 3.4...
        content= content.decode('utf-8')
    
    list_element = content.split()
    # modify head in case it is finished or an erro occured
    head = str(list_element[0])
    # change prefix number
    prefix_number += 1

# Post-treatment
# The score is the last element of content (in case of a public test set)
print(content)

list_element = content.split()
score = (list_element[-1])
print(score)


