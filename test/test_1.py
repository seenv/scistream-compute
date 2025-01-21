from globus_compute_sdk import Executor
import os

def get_info():
    import os  
    return os.uname()

this = '77d689b7-080a-480e-b356-1fc8047e443e'
swell = 'fb0f280f-dc0f-4bd6-83d0-83153ca9df4d'
p2cs = '2fa4f42e-2172-4bdf-baee-00febc902fe9'
with Executor(endpoint_id=swell) as gce:
    future = gce.submit(get_info)

    print(future.result())
