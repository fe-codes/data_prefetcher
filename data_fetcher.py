import threading
import Queue
# This file is used to create an independent thread that prefetch data for the main thread
# this is typically useful for the following scenarios:
# one is that preparing data for training takes a lot operation(time) so it is not time-efficient to wait for data preparation in each iteration
# another is that the data is too large to be put in memory at once, so it must be read in part by part via I/O
# it is also useful when the main thread is doing computation on GPUs while the data thread is preparing data with CPUs.
class data_thread(threading.Thread):#m2d main thread release to data thread/d2m data thread release to main thread
    def __init__(self,sema_m2d,sema_d2m,event_term,dq,aq,prepare_data,mute = False):
        self.sema_m2d = sema_m2d
        self.sema_d2m = sema_d2m
        self.event_term = event_term
        self.dq = dq
        self.aq = aq
        self.prepare_data = prepare_data
        self.mute = mute
        threading.Thread.__init__(self)
        
    def listen(self):
        self.sema_m2d.acquire() #block here, when the data is rettrieved, one signal is released and a new data operation is taken below
        if self.event_term.isSet():# since the data thread is often in blocking, when it is waked, the first thing to check is whether to terminate.
            return 'T'
##        print 'data requested'
        self.dq.put(self.prepare_data(self.aq.get()))#prepare data and put data in the data queue. arguments for preparing data (such as indexing data )can be passed through aq
        self.sema_d2m.release() # increase the counter of available data for the main thread.
        
    def serve_forever(self):
        while True:
            if self.event_term.isSet():
                if not self.mute:
                    print 'data service over'
                return 'Terminated'
            self.listen() # the data thread is constantly blocked in the listen operation, this means that there are N data prepared in the buffer
            
    def run(self):# Thread.start() will call this automatically in a new thread
        if not self.mute:
            print 'start data service'
        self.serve_forever()
        
class data_fetcher:
    '''
    A function func_prepare_data(arg) for doing the data preparation is required,
    arg takes the arguments in a tuple, even if no arguments is required, arg should be presented
    1, construct method takes func_prepare_data as input
    2, call start(init_params) to start data thread, init_params contains the params needed for preparing data in advancce
    3, call over() at the end of the program
    4, call get( param_next) to get data
    '''
    def __init__(self,func_prepare_data,mute = False):# if mute is true, the data thread will not print anything
        self.sema_m2d = threading.Semaphore(0)
        self.sema_d2m = threading.Semaphore(0)
        self.event_term = threading.Event() # the main thread can terminate the data thread through this object
        self.dq = Queue.Queue()# data queue
        self.aq = Queue.Queue()# arguments queue to the data worker
        self.d_t = data_thread(self.sema_m2d,self.sema_d2m,self.event_term,self.dq,self.aq,func_prepare_data,mute)
        
    def start(self,init_params = None):
        self.event_term.clear()
        self.d_t.start()
        if init_params is None:
            for i in range(2):
                self.aq.put(i)
                self.sema_m2d.release()# keep 2 free data in advance by default
        else:
            for params in init_params:
                self.aq.put(params)
                self.sema_m2d.release()
                
    def over(self):# this should be called at the end of program, or the data thread will not be terminated
        self.event_term.set()
        self.sema_m2d.release() # the data thread is constantly blocked for this signal before it can check the termination signal
        self.d_t.join()
        
    def get(self, next_params = None):
        self.aq.put(next_params) # put the params needed for next time
        self.sema_m2d.release()# notify the data thread the new job
        self.sema_d2m.acquire() # blocked until there is new data prepared, it should never be blocked if the data thread is puting data in advance
        data = self.dq.get()
        return data
