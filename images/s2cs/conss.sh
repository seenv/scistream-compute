#!/bin/bash

sleep 15
cp /tmp/server.crt /tmp/server.key ./

sleep 5
s2cs --verbose --port=5007 --listener-ip=128.135.24.120 --type=Haproxy

