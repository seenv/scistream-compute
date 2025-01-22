#!/bin/bash
# Generate a key
openssl genrsa -out server.key 2048

# Create the server.conf file with the required contents
cat <<EOL > server.conf
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = 128.135.24.119

[v3_req]
subjectAltName = IP:128.135.24.117, IP:128.135.24.118, IP:128.135.164.119, IP:128.135.24.119, IP:128.135.164.120, IP:128.135.24.120
EOL

openssl req -new -key server.key -out server.csr -config server.conf
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -extfile server.conf -extensions v3_req

cp server.crt server.key /tmp/

# Print success message
echo "RSA key and server.conf have been created successfully."

# Start scistream's control server
s2cs --verbose --port=5007 --listener-ip=128.135.24.119 --type=Haproxy


