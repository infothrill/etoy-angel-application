#!/bin/sh

# find lines having a print statement that is not commented:
find ./ -name '*.py' -print0 | xargs -0 grep -n '^[[:space:]]*print.*'
