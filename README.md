# data_prefetcher
A way to create a data thread that prefetches data for the main thread.

You can use this code to create an independent thread that prefetch data for the main thread, this is typically useful for the following scenarios:
One is that preparing data for training takes a lot operation(time) so it is not time-efficient to wait for data preparation in each iteration. Another is that the data is too large to be put in memory at once, so it must be read in part by part via I/O. It is also useful when the main thread is doing computation on GPUs while the data thread is preparing data with CPUs.

In short, you can use the code by 
    1. Implement a function that defines how the data is prepared, construct a data_fetcher with it
    2. Call data_fetcher.start() to start the data thread
    3. Call data_fetcher.get() to get data
    4. Call data_fetcher.over() to terminate the data thread
