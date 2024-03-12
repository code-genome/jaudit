#!/usr/bin/python3

import sys
import json

print(json.dumps(json.load(sys.stdin), separators=(',',':')))
