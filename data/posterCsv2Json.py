#!/usr/bin/python3
import csv
from optparse import OptionParser
import json
from io import StringIO
from urllib.parse import urlparse

Debug = False;
Verbose = False;

class Poster:                 # a poster data structure
    def __init__(self):
        self.posterID = ''
        self.authorName = ''
        self.otherNames = ''
        self.collaboration = ''
        self.category = ''
        self.filename = ''
        self.smallFilename = ''
        self.pdfname = ''
        self.posterTitle = ''
        self.videoLink = ''
        self.videoName = ''
        self.presentLink = ''
        self.abstract = ''
        self.miniAbstract = ''
        self.session = ''

#    def __repr__(self):
#        return "<Test a:%s b:%s>" % (self.a, self.b)
# I am ok with the default of return "<%s instance at %s>" % (self.__class__.__name__, id(self))

    # spit self out as a string.  Might as well be a json string
    def __str__(self):
        return json.dumps({
            'posterID': self.posterID,
            'authorName': self.authorName,
            'otherNames': self.otherNames,
            'collaboration': self.collaboration,
            'category': self.category,
            'filename': self.filename,
            'smallFilename': self.smallFilename,
            'pdfname': self.pdfname,
            'posterTitle': self.posterTitle,
            'videoLink': self.videoLink,
            'videoName': self.videoName,
            'presentLink': self.presentLink,
            'abstract': self.abstract,
            'miniAbstract': self.miniAbstract,
            'session': self.session

            },indent=2)

#Do it
def main():
    global Debug
    global Verbose

    # a list/array of posters
    posterList = []

    #Grab options
    usage = "usage: %prog [options] infile.csv outfile.json"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug", action="store_true", dest="Debug",
                      help="enable debug printing", default=False)
    parser.add_option("-v", "--verbose", action="store_true", dest="Verbose",
                      help="echo student output to screen", default=False)
    (options, args) = parser.parse_args()
    Verbose = options.Verbose
    Debug = options.Debug
    if (len(args) != 2):
        parser.error("Specify input and output files")
        sys.exit(1)

    # grab the first (and second) arguments as strings
    infilename  = str(args.pop(0))
    outfilename = str(args.pop(0))

    if (Verbose): print("Reading from ", infilename, ", writing to ",outfilename)
    # consume infile

    with open(infilename, 'r') as infile:
        posterReader = csv.reader(infile, delimiter=',')
        # could do this with csv.DictReader and give keys instead of
        # hassling with manual row indexes
        rownum = 0
        with open(outfilename, 'w') as outfile:
            next(posterReader)
            for row in posterReader:
                if (Debug):  print(row)
                # make a new Poster()
                thisPoster = Poster()

                # digest csv data, store in poster object
                thisPoster.posterID = row[0]
                thisPoster.authorName = row[1] # Presenter, anyway
                thisPoster.otherNames = row[2] # Co-authors, might result in duped names
                # is row[3] Co-Authors used?
                # need thisPoster.collaboration in there
                thisPoster.session = row[7]
                thisPoster.category = row[8]
                # need thisPoster.posterTitle = row[]
                thisPoster.abstract = row[6]
                thisPoster.miniAbstract = row[4]

                # row[5] is the hard one, links
                # should contain one pdf and one other movie file
                # pdf should be fetched, then pngs made
                # store pdf locally or delete and point back to indico?

                # let's search that string for a pdf URL and save that
                # use the csv library to chop things in that row
                f = StringIO(row[5])
                linkReader = csv.reader(f, delimiter=',')
                # should be only one row here, calling it "links"
                for links in linkReader:
		    # loop over items in the links column
                    for i in range(len(links)):
                        # parse string into url
                        link = urlparse(links[i].strip())
                        # take the last link ending in .pdf to be the poster
                        if(link.path[-4:]=='.pdf'):
                            thisPoster.pdfname = link.geturl()
                        # take the last link ending in .mp4 to be the video
                        if(link.path[-4:]=='.mp4'):
                            thisPoster.videoName = link.geturl()
                    # should throw exception on links that aren't one of the
                    # above, so that we can parse it manually?

                # go grab pdf, shell out concert to png
                # same with mp4s, upload to outube, get back link?

                # write out and store the poster
                posterList.append(thisPoster) # why?  dunno, could be handy
                outfile.write(thisPoster.__str__())
                outfile.write("\n")
                rownum += 1

            outfile.close
        infile.close
        if (Verbose): print("non-header rows: ",rownum)

if __name__ == "__main__":
    main()
    
