#!/bin/bash

[ $# -eq 0 ] && { echo "Usage: $0 fileToConvert.pdf"; exit 1; }

# make a large preview png
convert -density 150 -antialias -background white -flatten -append -resize 720x -quality 100 "$1"  "${1%.pdf}.png"

# make a thumbnail for the index
# while portrait worked well at 320x, try 480x for landscape
convert -density 150 -antialias -background white -flatten -append -resize 480x -quality 100 "$1" "${1%.pdf}-sm.png"
