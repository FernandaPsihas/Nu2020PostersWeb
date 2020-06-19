#!/cvmfs/larsoft.opensciencegrid.org/products/python/v3_7_2/Linux64bit+3.10-2.17/bin/python
import csv
from optparse import OptionParser
import json

Debug = True;
Verbose = True;
UploadVideos = False;
DownloadVideos = False;
Number = -1;

#Do it
def main():
    global Debug
    global Verbose
    global Number

    #Grab options
    usage = "usage: %prog [options] posters.json rooms.json combined.json"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug", action="store_true", dest="Debug",
                      help="enable debug printing", default=False)
    parser.add_option("-v", "--verbose", action="store_true", dest="Verbose",
                      help="echo output to screen", default=False)
    parser.add_option("-n", "--number", type="int", nargs=1, dest="Number",
                      help="do this many poster entries", default=-1)
    (options, args) = parser.parse_args()
    Verbose = options.Verbose
    Debug = options.Debug
    Number = options.Number
    if (len(args) != 3):
        parser.error("Specify 2x input and 1x output files")
        sys.exit(1)

    # grab the first (and second) arguments as strings
    posterfilename  = str(args.pop(0))
    roomfilename = str(args.pop(0))
    outfilename = str(args.pop(0))

    if (Verbose): print("Reading from ", posterfilename, " and ", roomfilename, " writing to ",outfilename)
    # consume infile
    if (Verbose):
        if (Number > 0):
            print("Doing the first " + str(Number) + " poster entries")
        else:
            print("Doing all poster entries")

    found = 0
    with open(posterfilename) as poster_json_file:
        with open(roomfilename) as room_json_file:
            posterdata = json.load(poster_json_file)
            roomdata = json.load(room_json_file)
            for poster in posterdata:
#                print('Poster #' + poster['posterID'] + '\n')
                for room in roomdata:
                    # find match, save presentLink
                    if (int(poster['posterID']) == room['poster_id']):
                        print("Poster #",poster['posterID']," has link ",room['room_link'])
                        poster['presentLink'] = room['room_link']
                        found += 1
                        break

    # done looping a lot
    poster_json_file.close
    room_json_file.close

    # spit out new json
    print('Found ',found,' room links')
    with open(outfilename, 'w') as outfile:
        json.dump(posterdata, outfile, indent=2, sort_keys=True)
    outfile.close

if __name__ == "__main__":
    main()
