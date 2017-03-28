import json
import sys

if __name__ == '__main__':
    parsed = json.load(sys.stdin)

    print( json.dumps(parsed, sort_keys = True, indent = 4) )
