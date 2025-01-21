def ids(endpoint):
    # Define the list of endpoints and their corresponding gce_ids
    endpoints = ["this", "swell", "neat", "that_prods",
                "prod_merrow", "cons_merrow", "p2cs_merrow", "c2cs_merrow"
                ]
    gce_ids = [
            '77d689b7-080a-480e-b356-1fc8047e443e', 'fb0f280f-dc0f-4bd6-83d0-83153ca9df4d',
            '007cb806-29a8-4fb6-a587-7244be75cb8f', '66f15123-7928-4367-9fc6-08a4897b3a49',
            'f343aea9-e68d-4d04-b844-0e55a5948156', 'de3c4d68-0dc4-43e1-a6ee-12d42de698e0',
            '2fa4f42e-2172-4bdf-baee-00febc902fe9', 'f4f453b2-9bbc-4aea-bdfd-08dcdcb62a2f'
            ]
    end_ids = dict(zip(endpoints, gce_ids))
    
    print(f"Endpoint: {endpoint}, GCE ID: {end_ids.get(endpoint, None)}") 

    return end_ids.get(endpoint, None)
