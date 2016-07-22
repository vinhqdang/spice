# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 10:47:00 2016

@author: Remi Eyraud

Tested with Python 2.7 and Python 3.4
"""

"""

Modified on Mon May 2 2016

@author: Vinh Dang

"""

import getopt,sys

# State the problem number
problem_number = '1'

# and the user id (given during registration)
user_id = '42'

#set parameter values

#Estimated rank of the Hankel matrix
rank = 30

#Allow only some of the possible rows and columns of the matrix
partial = True

#Set max length of elements for rows and column
lrows = 7
lcolumns = 7

#Set which version of the matrix you want to work with
version = "factor"  # "classic" , "prefix", "suffix" , "factor"

#Set whether you want to use the sparse of the classic version of the matrix
sparse = True

# name of this submission (no space or special character)
algorithm_name = "rank_" + str(rank) + "_sparse_" + version + "_lrows_lcolumns_" + str(lrows)

# use public or private test set
data_type = "public" #"public","private"

# handle parameters
try:
    opts, args = getopt.getopt(sys.argv[1:],"hp:d:n:",["problem=","data=","name=","rank=","lrows=","lcols=","version=","partial="])
except getopt.GetoptError as e:
    print ('Error parsing the command: ' + str(e))
    print "Usage"
    print sys.argv[0] 
    print "--problem=/-p" + " problem_number"
    print "--data=/-d + public/private"
    print "--name=/-n +algorithm_name"
    print "--rank= rank"
    print "--lrows= length of row"
    print "--lcols= length of columns"
    print "--version= classic/prefix/suffix/factor"
    print "--partial= True/False"
    print sys.argv[0] + " -h for help"
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print "Usage"
        print sys.argv[0] 
        print "--problem=/-p" + " problem_number"
        print "--data=/-d + public/private"
        print "--name=/-n +algorithm_name"
        print "--rank= rank"
        print "--lrows= length of row"
        print "--lcols= length of columns"
        print "--version= classic/prefix/suffix/factor"
        print "--partial= True/False"
        print sys.argv[0] + " -h for help"
        sys.exit ()
    elif opt in ("-p","--problem"):
        problem_number = arg
    elif opt in ("-d","--data"):
        data_type = arg
    elif opt in ("-n","--name"):
        algorithm_name = arg
    elif opt in ("--rank"):
        rank = int (arg)
    elif opt in ("--seq_len"):
        seq_len = int (arg)
    elif opt in ("--lrows"):
        lrows = int (arg)
    elif opt in ("--lcols"):
        lcolumns = int (arg)
    elif opt in ("--version"):
        version = arg
    elif opt in ("--partial"):
        partial = bool (arg)

problem_dir = "spice/p" + str (problem_number)

train_file = problem_dir + "/" + problem_number + ".spice.train"
prefix_file = problem_dir + "/" + problem_number + ".spice.public.test"
if (data_type == "private"):
    prefix_file = problem_dir + "/" + problem_number + ".spice.private.test"

def learn(train_file, parameter):
    """ Learn a weighted automaton using spectral approach
        parameter is the rank
        """
    # Import the SPiCe spectral learning toolbox
    import sp2learn.learning as LC
    from sp2learn.sample import Sample
    print ("file : ", train_file)
    # Get the learning sample in needed format
    pT = Sample(adr=train_file, lrows=lrows, lcolumns=lcolumns,
                version=version, partial=partial)
        
    # Create a learning instance
    S_app = LC.Learning(sample_instance=pT)
                
    # Learn an automaton (see documentation for other possible parameters)
    A = S_app.LearnAutomaton(rank=parameter, lrows=lrows,
                             lcolumns=lcolumns, version=version,
                             partial=partial, sparse=sparse)

    # Transform the automaton in order to compute prefix weights instead of sequence weight
    Ap = A.transformation(source="classic", target="prefix")

    return Ap


def next_symbols_ranking(model, prefix, k=5):
    """ Give the sorted list of the k more frequent next symbols of the prefix in the automaton 
        The model needs to compute prefix weights (and not sequence weight)
        Output
        """
    # Word has to be a list of integer (and not a string)
    # First element is the length of the prefix and thus has to be erased
    word = prefix.split()
    word = [int(i) for i in word][1:]

    # Compute the weight of the prefix
    p_w = model.val(word)
    for i in range(model.nbL):
        p_w -= model.val(word+[i])

    # Symbol -1 correspond to end of sequence
    # If the weight is negative it does not carry any semantic
    l = [(-1, max(p_w, 0))]
    s = max(p_w, 0)

    # Compute the weight of the prefix concatenated to each possible symbol
    for i in range(model.nbL):
        l.append((i, max(model.val(word+[i]), 0)))
        s += max(model.val(word+[i]), 0)

    # Sort the symbol by decreasing weight
    l = sorted(l, key=lambda x: -x[1])

    if s != 0:
        # At least one symbol has a strictly positive weight
        # Return a string containing the sorted k most probable next symbols separted by spaces
        mot = trans_string([x[0] for x in l][0:k])
        return mot
    else:
        # All symbols have a non-positive weight in the model
        # Return the k first symbols...
        return trans_string([x for x in range(-1, k-1)][0:k])


def trans_string(list):
    """ Transform a list of interger into a string of elements separated by a space """
    mot = ""
    for w in list:
        mot +=  str(w) + ' '
    return mot


def get_first_prefix(test_file):
    """ get the only prefix in test_file """
    f = open(test_file)
    prefix = f.readline()
    f.close()
    return prefix


def formatString(string_in):
    """ Replace white spaces by %20 """
    return string_in.strip().replace(" ", "%20")


# learn the model
print ("Start Learning")
model = learn(train_file, rank)
print ("Learning Ended")

# get the test first prefix: the only element of the test set
first_prefix = get_first_prefix(prefix_file)

# get the next symbol ranking on the first prefix
ranking = next_symbols_ranking(model, first_prefix)

print ("Prefix number: 1 Ranking: " + ranking + " Prefix: " + first_prefix)

# transform ranking to follow submission format (with %20 between symbols)
ranking = formatString(ranking)

# transform the first prefix to follow submission format
first_prefix = formatString(first_prefix)

# create the url to submit the ranking
url_base = 'http://spice.lif.univ-mrs.fr/submit.php?user=' + user_id +\
           '&problem=' + problem_number + '&submission=' + algorithm_name + '&'
url = url_base + 'prefix=' + first_prefix + '&prefix_number=1' + '&ranking=' +\
      ranking

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
    ranking = next_symbols_ranking(model, prefix)
    
    print("Prefix number: " + str(prefix_number) + " Prefix: " + str (prefix) + "\n" + " Ranking: " + ranking.replace("%20"," "))
    raw_input()
    
    # Format the ranking
    ranking = formatString(ranking)

    # create prefix with submission needed format
    prefix=formatString(prefix)

    # Create the url with your ranking to get the next prefix
    url = url_base + 'prefix=' + prefix + '&prefix_number=' +\
        str(prefix_number) + '&ranking=' + ranking

    # Get the answer of the submission on current prefix
    response = ur.urlopen(url)
    content = response.read()
    print ("Get response")
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
