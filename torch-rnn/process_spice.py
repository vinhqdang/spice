# Date: 2016 - 04 - 27
# Version: 1.0

# For SpiCe contest 
# http://spice.lif.univ-mrs.fr/
# 
# Parameter
# No 1: problem number
# No 2: public/private
# No 3: train/test/all
# No 4: algorithm name
# 
# Example:
# python process_spice.py -d public -t all --rnn_size=256 --seq_len=5 --dropout=0.5 --batch_size=5 --max_epochs=20 -p 2

import os
#to handle parameters
import getopt
import sys
import glob
import subprocess
import random, string  
from collections import Counter
import time
import codecs

# we will convert the input in numeric to character
# reserve 'a' for termination character, i.e. to predict the prefix will end
char_list = string.ascii_letters[1:] + "0123456789" + "~`!@#$%^&*()-=_+" + "[]\{}|;':\",./<>?"
for i in range(1000,8000):
   char_list = char_list + unichr(i)
terminate_char = 'a'

# SpiCe contest requires prediction for next most 5 probable symbols
PREDICT_LENGTH = 5

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

# define init variables
# submission parameters
problem_number = -1
data_type = "public"
task = "all"
algorithm_name = randomword (15)

# train parameters
batch_size = 2
seq_len = 50
max_epochs = 10
rnn_size = 512
num_layers = 2
dropout = 0.5
learning_rate = 2e-3
grad_clip = 5
gpu = 0 #-1 for CPU mode, 0 for GPU mode
checkpoint_every = 100000    # save the model (t7 file) after how many iterations. 0 for disable

# handle parameters
try:
      opts, args = getopt.getopt(sys.argv[1:],"hp:d:t:n:bs:sl:max_epochs:rnn_size:num_layers:dropout:gpu:",["problem=","data=","task=","name=","rnn_size=","batch_size=","seq_len=","max_epochs=","num_layers=","dropout=", \
                                                "learning_rate=","grad_clip=","checkpoint_every="])
except getopt.GetoptError as e:
      print "Error of parameters"
      print e
      print sys.argv[0] + " -h for help"
      sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'Usage: ' + sys.argv[0] + " -p problem_number -d public/private -t train/test/all -n algorithm_name"
        print 'Usage: ' + sys.argv[0] + " --problem problem_number --data public/private --task train/test/all --name algorithm_name"
        print sys.argv[0] + " -h for help"
        sys.exit ()
    elif opt in ("-p","--problem"):
        problem_number = int (arg)
    elif opt in ("-d","--data"):
        data_type = arg
    elif opt in ("-t","--task"):
        task = arg
    elif opt in ("-n","--name"):
        algorithm_name = arg
    elif opt in ("-bs","--batch_size"):
        batch_size = int (arg)
    elif opt in ("-sl","--seq_len"):
        seq_len = int (arg)
    elif opt in ("--max_epochs"):
        max_epochs = int (arg)
    elif opt in ("--rnn_size"):
        rnn_size = int (arg)
    elif opt in ("--num_layers"):
        num_layers = int (arg)
    elif opt in ("--dropout"):
        dropout = float (arg)
    elif opt in ("--learning_rate"):
        learning_rate = float (arg)
    elif opt in ("--grad_clip"):
        grad_clip = int (arg)
    elif opt in ("--checkpoint_every"):
        checkpoint_every = int (arg)
    elif opt in ("-gpu"):
        gpu = arg


problem_dir = "spice/p" + str (problem_number)

origin_train_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.train"

train_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.train.out"

public_test_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.public.test.out"

private_test_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.private.test.out"

train_h5_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.train.h5"

train_json_filename = "./" + problem_dir + "/" + str (problem_number) + ".spice.train.json"

token_dict_filename = "./" + problem_dir + "/token_dict.txt"

public_test_length_filename = "./" + problem_dir + "public_test_len.txt"

private_test_length_filename = "./" + problem_dir + "private_test_len.txt"

test_length_filename = public_test_length_filename

checkpoint_prefix = "cv/spice_p" + str(problem_number)

test_string = ""

token_dict = None

TEST_MAX_LEN = 0

def get_max_token (origin_train_filename):
    f = open (origin_train_filename)
    first_line = f.readline()
    return int (first_line.split()[1])

def read_token_dict (token_dict_filename):
    res = None
    with open (token_dict_filename, "r") as token_dict_file:
        token_dict_str = token_dict_file.readline ()
        res = map (int, token_dict_str.split ())
    return res

# number of different symbols in the dataset
max_token = get_max_token (origin_train_filename)

def get_first_prefix(test_file):
    """ get the only prefix in test_file """
    f = open(test_file)
    prefix = f.readline()
    f.close()
    return prefix

def formatString(string_in):
    """ Replace white spaces by %20 """
    return string_in.strip().replace(" ", "%20")

def convert_num_to_char (num_list):
    output = ""
    # for element in num_list:
    #     output = output + char_list[element]
    for element in num_list:
        _num_index = token_dict.index (element)
        output = output + char_list [_num_index]
    return output

def convert_char_to_num (string_in):
    # print string_in
    num_output = list ()
    # for char in string_in:
    #     num_char = 0
    #     if char == 'a':
    #         num_char = -1
    #     else:
    #         num_char = char_list.index (char)
    #         if num_char >= max_token:
    #             num_char = -1
    #     num_output.append (num_char)
    
    for char in string_in:
        num_char = 0
        if char == 'a':
            num_char = -1
        else:
            _num_char_index = char_list.index (char)
            if _num_char_index >= max_token:
                num_char = -1
            num_char = token_dict [_num_char_index]
        num_output.append (num_char)

    return " ".join (str(x) for x in num_output)


"""
@brief      Sort a string by frequency of character from highest to lowest and remove the duplicate. In case of equality, follow the alphabet order.

@param      string_in  The input string

@return     the string with character sorted by frequency in the input string

Example:

'abcacc' --> 'cab'
"""

def sort_by_freq (string_in):
    counts = Counter(string_in)
    sorted_string = sorted(counts, key=lambda character: (-counts[character], character))
    return sorted_string

def train ():
    # convert the training set to hdf5

    # http://www.jeffreythompson.org/blog/2016/03/25/torch-rnn-mac-install/

    # python scripts/preprocess.py --input_txt data/tiny-shakespeare.txt --output_h5 data/tiny_shakespeare.h5 --output_json data/tiny_shakespeare.json

    preprocess_train_command = "python scripts/preprocess.py --input_txt " + train_filename + " --output_h5 " \
                            + train_h5_filename + " --output_json " + train_json_filename

    os.system (preprocess_train_command)

    # training RNN 

    # th train.lua -input_h5 data/tiny_shakespeare.h5 -input_json data/tiny_shakespeare.json

    train_command = "th train.lua -input_h5 " + train_h5_filename + " -input_json " + train_json_filename \
                    + " -checkpoint_name " + checkpoint_prefix \
                    + " -batch_size " + str(batch_size) \
                    + " -seq_length " + str(seq_len) \
                    + " -max_epochs " + str(max_epochs) \
                    + " -checkpoint_every " + str(checkpoint_every) \
                    + " -rnn_size " + str(rnn_size) \
                    + " -dropout " + str(dropout) \
                    + " -num_layers " + str(num_layers) \
                    + " -learning_rate " + str(learning_rate) \
                    + " -grad_clip " + str(grad_clip) \
                    + " -gpu " + str(gpu)

    os.system (train_command)


def predict (prefix):
    # After training
    # find the latest t7 file created, which is the model
    latest_t7_filename = max((os.stat(x)[8], x) for x in glob.glob(checkpoint_prefix+"*"))[1] 

    test_string_len = len (prefix)

    predict_command = "th sample.lua -checkpoint " + latest_t7_filename \
                    + " -length " + str (test_string_len + 1) \
                    + " -start_text " + '\"' + prefix + '\"' \
                    + " -gpu -1"

    # print (predict_command)

    # predict_output = list ()

    # version 2 of prediction
    # run many times then sort by frequency
    # for i in range (1000):
    #     # output = subprocess.check_output(predict_command, shell=True)
    #     output = os.popen(predict_command).read()
    #     output = output[test_string_len]
    #     if output not in char_list:
    #         output = 'a'
    #     predict_output.append (output)
    #     predict_output = sort_by_freq (predict_output)
         
    # update the code
    # only accept different symbols in the output
    
    # while True:
    #     output = os.popen(predict_command).read()
    #     output = output[test_string_len]
    #     if output not in char_list:
    #         output = 'a'
    #     if output not in predict_output:
    #         predict_output.append (output)
    #     if (len (predict_output) == PREDICT_LENGTH):
    #         break

    # version 3:
    # read 5 most probable directly from the output of Lua code (modified for SpiCe)
    predict_output = os.popen(predict_command).read()
    # print (predict_output)
    predict_output = predict_output.split ()
    # predict_output = "".join(i if i in char_list else 'a' for i in output) # not need because 'a' is written already by lua app
    # print ("".join (predict_output[1:6]))
    # raw_input ("Enter to continue..")
    predict_output = "".join (predict_output[0:5])

    return formatString (convert_char_to_num (predict_output))

def submit (first_prefix, output):
    # constant values
    # just for my account
    user_id = 42

    url_base = 'http://spice.lif.univ-mrs.fr/submit.php?user=' + str(user_id) +\
           '&problem=' + str(problem_number) + '&submission=' + algorithm_name + '&'
    url = url_base + 'prefix=' + str (len(first_prefix)) + '%20'+ formatString(convert_char_to_num(first_prefix)) + '&prefix_number=1' + '&ranking=' +\
          output
    if problem_number == 7:
        url = url_base + 'prefix=' + "21" + '%20'+ formatString(convert_char_to_num(first_prefix)) + '&prefix_number=1' + '&ranking=' + output
    # print (url)
    print("Prefix number: " + str(1) + " Prefix: " + str(convert_char_to_num(first_prefix)) + "\n" + " Ranking: " + output.replace("%20"," "))
    print ("-------------")
    
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
        # Get rid of Line feed
        prefix = content[:-1]

        prefix = prefix.split ()

        # prefix_len is sent from server
        # it should be the length of the prefix, so we can calculate automatically
        # however, to prevent any conflict, we use the number from server
        prefix_len = prefix[0]

        prefix = prefix[1:]

        prefix = list (int (x) for x in prefix)

        print ("Problem:" + str(problem_number))
        print ("Prefix number: " + str(prefix_number) + "/" + str (TEST_MAX_LEN))
        print ("Prefix: " + str(prefix))
	
        
        # Get the ranking
        ranking = predict(convert_num_to_char(prefix))
        
        print(" Ranking: " + ranking.replace("%20"," "))
        
        # Format the ranking
        ranking = formatString(ranking)

        # create prefix with submission needed format
        prefix=formatString(str (prefix_len) + " " + " ".join (list (str(x) for x in prefix)))

        # Create the url with your ranking to get the next prefix
        url = url_base + 'prefix=' + prefix + '&prefix_number=' +\
            str(prefix_number) + '&ranking=' + ranking

        # print url
        print "----------"

        # Get the answer of the submission on current prefix
        response = ur.urlopen(url)
        content = response.read()
        if not orl2:
            # Needed for python 3.4...
            content= content.decode('utf-8')
        list_element = content.split()

        # print list_element
        # print '------------'

        # modify head in case it is finished or an error occurred
        head = str(list_element[0])

        # change prefix number
        prefix_number += 1

    # Post-treatment
    # The score is the last element of content (in case of a public test set)
    print(content)

    list_element = content.split()
    score = (list_element[-1])
    print(score)

    print ("Parameters used: " + str(sys.argv[1:]))
    print ("Time " + str (time.strftime("%Y-%m-%d %H:%M")))

    # write to log file
    with open("spice/p" + str(problem_number) + "/log.txt", "a") as myfile:
        myfile.write ("Parameters used: " + str(sys.argv[1:]) + "\n")
        myfile.write ("Time " + str (time.strftime("%Y-%m-%d %H:%M")) + "\n")
        myfile.write ("Score = " + str(score) + "\n")
        myfile.write ("-------------------------------\n")

    # write number of test case to file
    with open (test_length_filename, "w") as myfile:
        myfile.write (str(prefix_number - 1))

# convert data
print 'Convert data'
os.system ("python spice/preprocess_scice.py " + " -p " +str(problem_number) + " -d ./spice/")
print 'Converting done'

# run the job
if task == "train" or task == "all":
    print 'Training'
    train()
if task == "test" or task == "all":
    # reading token dictionary
    # token dict is written by preprocessing python script
    # token dict contains the order of tokens, correspond with character
    # for example, if token_dict file contains 3 1 0, i.e 3 corresponds with b, 1 with c and 0 with d
    token_dict = read_token_dict (token_dict_filename)

    print 'Testing and Submitting'
    # run prediction on public test or private test
    test_filename = public_test_filename

    if data_type == 'private':
        test_filename = private_test_filename  
        test_length_filename = private_test_length_filename

    # read maximum number of test cases from file
    if (os.path.isfile (test_length_filename)):
        with open (test_length_filename, "r") as myfile:
            line = myfile.readline() 
            TEST_MAX_LEN = int (line)
    test_string = get_first_prefix (test_filename)
    predict_string = predict (test_string)
    submit (test_string,predict_string)


