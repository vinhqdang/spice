"""
Preprocessing SpiCe data
Convert numeric tokens to characters to be processed later by torch-rnn
"""

import sys
import getopt
import string
import os
import codecs

directory_base = "./"

try:
      opts, args = getopt.getopt(sys.argv[1:],"hp:d:",["problem=","dir="])
except getopt.GetoptError:
      print 'Usage: ' + sys.argv[0] + " -p problem_number -d directory_base"
      print sys.argv[0] + " -h for help"
      sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'Usage: ' + sys.argv[0] + " -p problem_number -d directory_base"
        print sys.argv[0] + " -h for help"
        sys.exit ()
    elif opt in ("-p","--problem"):
        problem_number = int (arg)
    elif opt in ("-d","--dir"):
        directory_base = arg

problem_dir = "p" + str (problem_number)

train_filename = directory_base + problem_dir + "/" + str (problem_number) + ".spice.train"

public_test_filename = directory_base + problem_dir + "/" + str (problem_number) + ".spice.public.test"

private_test_filename = directory_base + problem_dir + "/" + str (problem_number) + ".spice.private.test"

# remove pretrained files

os.system ("rm " + directory_base + problem_dir + "/*.out")
os.system ("rm " + directory_base + problem_dir + "/*.h5")
os.system ("rm " + directory_base + problem_dir + "/*.json")

# we will convert the input in numeric to character
# reserve 'a' for termination character, i.e. to predict the prefix will end
char_list = string.ascii_letters[1:] + "0123456789" + "~`!@#$%^&*()-=_+" + "[]\{}|;':\",./<>?"
for i in range (1000,8000):
   char_list = char_list + unichr(i)
terminate_char = 'a'

# update 20 - May - 2016 on problem 6
# even the maximum number of tokens is 60, not all of them will appear in training set
# for instance, problem 6 training data contains only 25 different tokens
# using token_dict to remove the size of needed characters
# token_dict contains 3,1,0 means 3 is b, 1 is c and 0 is d.
token_dict = [-2] * len (char_list)

# input: a string likes "1 4 5 14"
# output: characters correspond
def conv_num_to_char (string_in):
    line = string_in.split ()
    newline = ""
    for element in line:
        element = int (element)
        if element not in token_dict:
            _new_token_index = token_dict.index (-2)
            token_dict [_new_token_index] = element
        newline = newline + char_list[token_dict.index(element)]
    return newline

with open (train_filename) as f:
    f_out = codecs.open (train_filename + ".out", "w","utf-8")
    lines = f.readlines()

    # start with 0
    # if found new token, add the character index 0 in char_list to dictionary with the key is the new token
    # then increase cur_char_using_index to 1
    cur_char_using_index = 0

    for i in range (len (lines)):
        if i != 0:
            line_size = int (lines[i].split ()[0])

            # use [:-1] to remove newline character
            if line_size > 0:
                line = lines[i].split(' ', 1)[1][:-1]
                line = conv_num_to_char (line)

                f_out.write (line)
                if i < len (lines) - 1:
                    f_out.write ('\n')
            else:
                f_out.write ('\n')

            # replace number by character
            # line = line.split ()
            # new_line = ""
            # for element in line:
            #     new_line = new_line + char_list[int(element)]
            # line = new_line
             
            # update char_dict
            
    f_out.close ()

    # write token_dict to file to use in processing phase
    with open (directory_base + problem_dir + "/token_dict.txt", "w") as myfile:
        invalid_index = token_dict.index (-2)
        for item in token_dict[:invalid_index]:
            myfile.write (str(item) + " ")

with open (public_test_filename) as f:
    f_out = codecs.open (public_test_filename + ".out", "w", "utf-8")
    lines = f.readlines()
    for i in range (len (lines)):
        line = lines[i].split(' ', 1)[1]

        # replace number by character
        line = conv_num_to_char (line)

        f_out.write (line)
        if i < len (lines) - 1:
            f_out.write ('\n')
    f_out.close ()

if problem_number != 0:
    with open (private_test_filename) as f:
        f_out = codecs.open (private_test_filename + ".out", "w", "utf-8")
        lines = f.readlines()
        for i in range (len (lines)):
            line = lines[i].split(' ', 1)[1]

            # replace number by character
            line = conv_num_to_char (line)

            f_out.write (line)
            if i < len (lines) - 1:
                f_out.write ('\n')
        f_out.close ()
