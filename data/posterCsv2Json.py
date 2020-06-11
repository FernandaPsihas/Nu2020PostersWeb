#!/usr/bin/python3
import csv
from optparse import OptionParser
import json
from io import StringIO
from urllib.parse import urlparse
import os
# upload-required includes
import argparse
import http.client as httplib
# check with Fernanda import httplib2
import random
import time
# check with Fernanda import google.oauth2.credentials
# check with Fernanda import google_auth_oauthlib.flow
# check with Fernanda from googleapiclient.discovery import build
# check with Fernanda from googleapiclient.errors import HttpError
# check with Fernanda from googleapiclient.http import MediaFileUpload
# check with Fernanda from google_auth_oauthlib.flow import InstalledAppFlow

Debug = True;
Verbose = True;
UploadVideos = False;

DownloadAnything = False;
DummyPdfname = "pdf/mock_poster_2.pdf";
DummyVideo = "https://www.youtube.com/embed/ne7wTZ1AjG8";
DummyFilename = "img/mock_poster_2.png";
DummySmallFilename = "img/mock_poster_2-sm.png";
DummyContestLink = "https://docs.google.com/forms/d/e/1FAIpQLSeSZc02g5bPzP-ishvKyRADUwqAy4h0FZe6zD44G-WfgbMEhA/viewform";
DummyPresentLink  = "https://nu2020-hubs.org/#/";

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
# check with Fernanda httplib2.RETRIES = 1
# Maximum number of times to retry before giving up.
MAX_RETRIES = 10
# Always retry when these exceptions are raised.
# check with Fernanda RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
# check with Fernanda   httplib.IncompleteRead, httplib.ImproperConnectionState,
# check with Fernanda   httplib.CannotSendRequest, httplib.CannotSendHeader,
# check with Fernanda   httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
CLIENT_SECRETS_FILE = 'client_secret.json'

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')

class Poster:                 # a poster data structure
    def __init__(self):
        self.posterID = ''
        self.authorName = ''
        self.otherNames = ''
        self.collaboration = ''
        self.category = ''
        self.track = ''
        self.filename = ''
        self.smallFilename = ''
        self.pdfname = ''
        self.posterTitle = ''
        self.videoLink = ''
        self.videoName = ''
        self.videoFileName = ''
        self.presentLink = ''
        self.abstract = ''
        self.miniAbstract = ''
        self.session = ''
        self.contestLink = ''
        self.youtubeID = ''

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
            'track': self.track,
            'filename': self.filename,
            'smallFilename': self.smallFilename,
            'pdfname': self.pdfname,
            'posterTitle': self.posterTitle,
            'videoLink': self.videoLink,
            'videoName': self.videoName,
            'videoFileName': self.videoFileName,
            'presentLink': self.presentLink,
            'abstract': self.abstract,
            'miniAbstract': self.miniAbstract,
            'session': self.session,
            'contestLink': self.contestLink,
            'youtubeID':self.youtubeID
            }, indent=2, sort_keys=True)
    # maybe add ensure_ascii=False to get unicode to come out ok

# grab poster pdf
def fetchfile(url,filename):
    global Debug
    global Verbose
    if (Verbose):
        print('Fetching ',url)
        cmd = "wget " + url + " -O " + filename
    else:
        cmd = "wget -o /dev/null " + url + " -O " + filename
    return os.system(cmd)

# print warning messages
# dump right now, but might want different handling than just "print"
def LogWarning(warnString):
    print(warnString)

def dealWithPdf(poster):
    global Debug
    global Verbose

    url = poster.pdfname
    posterID = poster.posterID
    # places to put stuff.  relative to index.html's subdir
    # eg, data/posterCsv2Json.py --verbose data/newdata.csv data/newdata.json
    # should make these runtime parameters
    tmpdir = "/tmp/"
    imgdir = "img/"
    pdfdir = "pdf"   # if we keep them.  Prob. leave on indico instead

    # form image filenames
    pdfName = tmpdir + "posterPDF-" + posterID + ".pdf"
    imageName = "posterPDF-" + posterID + ".png"
    imageName_sm = "posterPDF-" + posterID + "-sm.png"

    # grab it
    fetchError = fetchfile(url,pdfName)
    if (fetchError):
        print("fetchpdf error ",fetchError)
        exit(fetchError)
    # got it ok
    if (Debug):
        print("got pdf ok")

    # make pngs
    cmd = "pdf/posterPdfToPng.sh " + pdfName
    os.system(cmd)  # should check for error
    # move image files to the right place
    os.system("mv " + tmpdir + imageName + " " + imgdir)
    os.system("mv " + tmpdir + imageName_sm + " " + imgdir)
    # delete pdf from tmpdir
    os.system("rm " + pdfName)
    # fill values in the poster object
    poster.filename = imgdir + imageName
    poster.smallFilename = imgdir + imageName_sm


def dealWithVideo(poster):
    global Debug
    global Verbose

    url = poster.videoName
    posterID = poster.posterID
    # places to put stuff.  relative to index.html's subdir
    # eg, data/posterCsv2Json.py --verbose data/newdata.csv data/newdata.json
    filedir = "vid/"
    poster.videoFileName = filedir + "posterVideo-" + posterID + "." + url.split('.')[-1]

    # grab it
    fetchError = fetchfile(url,poster.videoFileName)
    if (fetchError):
        print("fetchfile error ",fetchError)
        exit(fetchError)
    # got it ok
    if (Debug):
        print("got video ok")

# UPLOAD FUNCTIONS #
# Authorize the request and store authorization credentials.
def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_console()
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def initialize_upload(youtube, thisposter):
  tags = None
#  if thisposter.keywords:
#    tags = thisposter.keywords.split(',')
  body=dict(
    snippet=dict(
      title=thisposter.posterTitle,
      description=thisposter.authorName,
      # description = 'Poster by {}\n\n {}'.format(thisposter.authorName, thisposter.posterTitle)
      tags=tags,
      categoryId=thisposter.category
    ),
    status=dict(
      privacyStatus="private"
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=','.join(body.keys()),
    body=body,
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting 'chunksize' equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(thisposter.videoFileName, chunksize=-1, resumable=True)
  )

  resumable_upload(insert_request, thisposter)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(request, thisposter):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print ('Uploading file...')
      status, response = request.next_chunk()
      if response is not None:
        if 'id' in response:
          print ('Video id "%s" was successfully uploaded.' % response['id'])
          thisposter.youtubeID=response['id']
# this is the plain youtube webpage
#          thisposter.videoLink="https://www.youtube.com/watch?v="+thisposter.youtubeID
# this is the embed link we shove into the iframe alter
          thisposter.videoLink="https://www.youtube.com/embed/"+thisposter.youtubeID
        else:
          exit('The upload failed with an unexpected response: %s' % response)
    except (HttpError, e):
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status,
                                                             e.content)
      else:
        raise
    except (RETRIABLE_EXCEPTIONS, e):
      error = 'A retriable error occurred: %s' % e

    if error is not None:
      print (error)
      retry += 1
      if retry > MAX_RETRIES:
        exit('No longer attempting to retry.')

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print ('Sleeping %f seconds and then retrying...' % sleep_seconds)
      time.sleep(sleep_seconds)

#Do it
def main():
    global Debug
    global Verbose

# check with Fernanda     if ( UploadVideos ):
# check with Fernanda         youtube = get_authenticated_service()

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
            # write the leading [
            outfile.write("[\n")
            next(posterReader)
            for row in posterReader:
                if (Debug):  print(row)
                # make a new Poster()
                thisPoster = Poster()

                # digest csv data, store in poster object
                thisPoster.posterID = row[0]
                thisPoster.posterTitle = row[1]
                thisPoster.authorName = row[2] # Presenter, anyway
                thisPoster.otherNames = row[3] # Authors, always includes Presenter
                # add in co-Authors field if present
                if (row[4]): thisPoster.otherNames += ', ' + row[4]
                thisPoster.collaboration = row[5]
#                thisPoster.session = row[9]
# for test, make session posterid % 4
                thisPoster.session = str((int(thisPoster.posterID) % 4) + 1)
                thisPoster.track = row[10]
                thisPoster.category = row[11]
                thisPoster.abstract = row[8]
                thisPoster.miniAbstract = row[6]

                # row[7] is the hard one, links
                # should contain one pdf and one other movie file
                # pdf should be fetched, then pngs made
                # store pdf locally or delete and point back to indico?

                # don't mess with this field in test mode.  Otherwise, 
                # fill the json with placeholders
                if (DownloadAnything):
                    # let's search that string for a pdf URL and save that
                    # use the csv library to chop things in that row
                    f = StringIO(row[7])
                    linkReader = csv.reader(f, delimiter=',')
                    # should be only one row here, calling it "links"
                    for links in linkReader:
                        # loop over items in the links column
                        for i in range(len(links)):
                            # parse string into url
                            link = urlparse(links[i].strip())
                            # take the first link ending in .pdf to be the poster
                            if (Debug): print(link)
                            if(link.path[-4:].lower()=='.pdf'):
                                if (thisPoster.pdfname):
                                    LogWarning("poster " + thisPoster.posterID + " has too many pdfs")
                                else:
                                    thisPoster.pdfname = link.geturl()
                                continue
                            # take the first link ending in .mp4 or .mov to be the video
                            if ((link.path[-4:].lower()=='.mp4') or (link.path[-4:].lower()=='.mov')):
                                if (thisPoster.videoName):
                                    LogWarning("poster " + thisPoster.posterID + " has too many videos")
                                else:
                                    thisPoster.videoName = link.geturl()
                                continue
                            # don't know about this filetype
                            LogWarning("poster " + thisPoster.posterID + " has unknown type")

                    # go grab pdf, shell out convert to png
                    if (thisPoster.pdfname != ""): dealWithPdf(thisPoster)
                    # if no pdf, skip to next thing so empty crap does
                    # not end in the json
                    else:
                        LogWarning("poster " + thisPoster.posterID + " has no pdf, skipping")
                        continue

                    if ((thisPoster.videoName != "") and UploadVideos): 
                        dealWithVideo(thisPoster)
                        if ( UploadVideos ):
                            try:
                                initialize_upload(youtube, thisPoster)
                            except (HttpError, e):
                                print ('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

                else:  # no downloads, stuff with dummy values
                    thisPoster.pdfname = DummyPdfname
                    thisPoster.videoLink = DummyVideo
                    thisPoster.filename = DummyFilename
                    thisPoster.smallFilename = DummySmallFilename
                    thisPoster.contestLink = DummyContestLink
                    thisPoster.presentLink = DummyPresentLink

                # write out and store the poster
                posterList.append(thisPoster) # why?  dunno, could be handy
                # if not the first row, add a comma to last entry
                if (rownum > 0): outfile.write(",\n")
                outfile.write(thisPoster.__str__())
                rownum += 1

            # write the trailing ]
            outfile.write("\n]\n")
            outfile.close
        infile.close
        if (Verbose): print("non-header rows: ",rownum)


if __name__ == "__main__":
    main()
