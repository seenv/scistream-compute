# First Run:
# >>> from globus_compute_sdk import Client
# >>> gcc = Client() | Client()



from globus_compute_sdk import Executor
    """
    The Executor class, a subclass of Python’s 
    concurrent.futures.Executor, is the preferred 
    approach to collecting results from the Globus 
    Compute web services.
    
    Executor class instantiates an AMQPS connection 
    that streams results directly and immediately as 
    they arrive at the server.
    
    pointers:
        - A Executor instance is associated with a 
          specific endpoint
        - The waiting or “blocking” for a result is 
          automatic. The .submit() call returns a 
          Future immediately; the actual HTTP call 
          to the Globus Compute web-services will 
          not have occurred yet, and neither will 
          the task even been executed (remotely), 
          much less a result received. The .result() 
          call blocks (“waits”) until all of that has 
          completed, and the result has been received 
          from the upstream services
        - 
    """
def double(x):
    return x * 2

this_gce_id = '77d689b7-080a-480e-b356-1fc8047e443e'
with Executor(endpoint_id=this_gce_id) as gce:
    fut = gce.submit(double, 7)

    print(fut.result())




"""
# Points from `https://globus-compute.readthedocs.io/en/latest/index.html`

with Executor(endpoint_id = this_gce_id) as gce:        # create the executor
    future = gce.submit(add_func, 5, 10)                # submit the executor
    print(future.result())                              # wait for the result




"""


