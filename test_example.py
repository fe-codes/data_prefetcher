import data_fetcher
import os
from skimage import io

# You need to implement a function that defines how the data is prepared, 
# this function will be called in the data thread, and a arg will be passed when it's called,
# so even if you don't need any args, keep an args variable for the function,
# if you have mutiple args, pack them in a tuple or list.
def prep_func(args):
    index = args[0]# unpack args you need
    img_path = args[1]# unpack args you need
    
    if index is None or img_path is None: # remember to consider the ending cases
        return None,None
    
    data = io.imread(img_path)# do some data preparation
    return index, data

# Commonly it is better to let the data preparing thread start before the main thread, so the main thread need not to wait for data when it starts
# you can put the params needed in a list, the data thread will call the prepare function with each of the params in the list.
pre_count = 3 # defines how many data is prefetched in advance
init_params = []
img_lst = ['./imgs/' + x for x in os.listdir('./imgs/')]
for i in range(pre_count): 
    index = i
    data = img_lst[i]
    init_params.append((index,data)) # pack multiple args in a tuple
    
df = data_fetcher.data_fetcher(prep_func,mute = True) # Construct a data_fetcher with the prepare function, mute controls whether the data_fetcher prints information, by default, it is False.
df.start(init_params)# now, start the data_fetcher, pass the list of initial params to it

try:
    for i in range(100):
        if i < 100 - pre_count:
            index,data = df.get((i + pre_count,img_lst[i + pre_count]))# call get() to fetch prepared data, pass arguments needed for the next time(next pre_countth time)
        else:
            index,data = df.get((None,None))# handle the ending case if necessary
        print index, data.shape # do some job with the data fetched.
finally:
    df.over() # call over to notify the data thread to exit
