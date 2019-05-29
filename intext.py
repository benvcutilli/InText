# IMPORTANT: All things in the comments that look like
#   <capitalized letter>#[number][(roman numeral)]
# refer to points made in the README

# json from <see hbbf>
import json
# random from <see eagg>
import random
# sys from <see eagi>
import sys
# pathlib from <see igji>, using Path class is from <see igji: Introduction section>
from pathlib import Path

# The indicators that users must use in their input files to indicate where
# a marker is
markerStart = "^^^"
markerStop  = "^^^"

# Which characters are allowed in a marker key
validMarkerCharacters = "abcdefghijklmnopqrstuvwxyz" +\
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +\
                        "1234567890"

# The function that does InText's default in-text citation formatting, including
# placing the locators:
def intextCitationStyle(infos, bk):
    result = ""
    for info in infos:
        if info["refkey"] not in bk:
            # Creating a key for the reference in the bibliography
            random.seed()
            newKey = None
            while True:
                newKey = "".join(random.choices("abcdefghij", k=4))
                if newKey not in bk.values():
                    break
            bk[info["refkey"]] = newKey
        result += "<see " + bk[info["refkey"]] + \
                  ((": " + info["locator"]) if "locator" in info else "") + \
                  ">"
    return result


# The default InText plugin that formats a bibliography:
def intextBibliographyStyle(keyMapping, config):

    flippedMapping = {}
    for key in keyMapping:
        flippedMapping[keyMapping[key]] = key

    # Sorting the references alphabetically by their B#3 keys:
    l = list(flippedMapping.items())
    def byBibliographyKey(pair):
        return pair[0]
    l = sorted(l, key=byBibliographyKey)

    ############################################################################
    # Calculating the maximum between the maximum length of a field name in a
    # formatted reference and the length of the key given to the reference in
    # the bibliography

    maxLength = -1
    for ref in l:
        refInfo   = config["references"][ref[1]]
        for field in refInfo:
            length = len(field)
            if length > maxLength:
                maxLength = length
    keyLength = len(list(flippedMapping.keys())[0])
    maxLength = keyLength if keyLength > maxLength else maxLength

    ############################################################################

    ############################################################################
    # Now formatting the bibliography

    def formatLine(text, maxLength):
        difference = maxLength - len(text)
        return " "*(difference) + text

    final = ""
    for ref in l:
        # Putting the key first on top of the stack of reference information
        final += " "*len(ref[0]) + formatLine(ref[0], maxLength) + "\n"

        ########################################################################
        # Now going through each field of the reference and putting it on a
        # line:

        info       = config["references"][ref[1]]
        for field in info:
            final += formatLine(field, maxLength)
            final += " - " + info[field] + "\n"

        # Separating this reference from all the other references:
        final += "\n"

        ########################################################################

    ############################################################################

    return final


# The function that performs (as disccused in C) the stylization of a formatted
# in-text citation:
citationStylizerPlugin = intextCitationStyle

# The bibliography style plugin from C
formattingBibliographyPlugin = intextBibliographyStyle

# Saving the JSON path for later when we cite within the JSON file, and loading
# the JSON file from the README.
configPath = sys.argv[1]
f          = open(configPath)
config     = json.load(f)
f.close()

# Function that gets all file-only paths in the tree rooted at root:
def descend(root):
    paths = []
    for child in root.iterdir():
        if child.is_file():
            paths.append(child)
        elif child.is_dir():
            paths += descend(child)
    return paths

root  = Path("intext")
# Paths (relative to the "intext" folder's parent directory) of files with
# markers. Adding the JSON configuration file's path to the list of files that
# need to be cited.
paths = descend(root)
paths.append(configPath)

# This dictionary holds the keys (from B#3) used for each formatted reference.
bibliographyKeys = {}


# This function returns the start of a marker and the postion after the marker's
# last character
def findNextMarker(content, s, e):
    startMarker = None
    startRest   = None

    i = 0
    while (i + len(s) + len(e)) <= len(content):
        if content[i:i+len(s)] == s:
            startMarker  = i
            break
        else:
            i += 1
    if startMarker == None:
        return None

    i = 0
    while (i + len(e)) <= len(content[startMarker + len(s):]):
        if content[( startMarker+len(s)+i ) : ( startMarker+len(s)+i+len(e) )] == e:
            startRest = startMarker + len(s) + i + len(e)
            break
        else:
            i += 1
    if startRest == None:
        return None

    return (startMarker, startRest)

# Holds the string with the contents of the JSON configuration file, but cited
citedConfigText = ""

for p in paths:
    ############################################################################
    # Cite the file at the path

    f        = open(p)
    content  = f.read()
    f.close()

    pathText = ""
    while True:

        # Getting the next available marker bounds
        result = findNextMarker(content, markerStart, markerStop)

        # Such a marker may not exist; we are done citing this file
        if result == None:
            break

        a         = result[0]
        b         = result[1]
        # Getting the key for the marker's information in the JSON configuration
        # file:
        markerKey = content[a + len(markerStart) : b - len(markerStop)]

        #######################################################################
        # Checking for valid marker keys

        if len(markerKey) == 0:
            break
        # The validKey variable and its subsequent usage was necessary as the
        # <see afdj> code would fail to be processed by InText as the break
        # that was where validKey = False was would just break out of the
        # surrounding for loop, not the while loop (this is besides the fact
        # that break was the wrong choice; continue was the right way to go,
        # though this may not have been revealed by the aforementioned failure)
        validKey = True
        for c in markerKey:
            if c not in validMarkerCharacters:
                validKey = False
        if not validKey:
            # The next two lines were necessary as InText would hang on the code
            # from <see afdj> if continue were to occur as the beginning
            # signal of the invalid marker wouldn't be passed after key
            # validity failed (therefore causing the same marker signal to
            # be detected in the next loop, causing an infinite loop)
            pathText += content[:a + len(markerStart)]
            content   = content[a + len(markerStart):]
            continue

        #######################################################################

        # Now looking up the objects containing which references are used in the
        # marker and the locators for those references:
        infos     = config["markers"][markerKey]

        # Using the style plugin (point C) to create a formatted in-text
        # citation for this marker:
        allCitations = citationStylizerPlugin(infos, bibliographyKeys)

        # Placing the formatted in-text citations within the text
        pathText += content[:a]
        pathText += allCitations
        content = content[b:]

    pathText += content

    ############################################################################

    # Special case where we store the cited JSON configuration file text in a
    # variable to be re-read as JSON:
    if p == configPath:
        citedConfigText = pathText
    else:
        # Removing the "intext" folder from the path
        p = Path(*p.parts[1:])

        # Creating all parent folders if necessary:
        dir = Path(*p.parts[:-1])
        dir.mkdir(parents=True, exist_ok=True)

        # Saving the formatted file
        outFile = open(p, "w")
        outFile.write(pathText)
        outFile.close()

# We now need to create the bibliography. We use the bibliography plugin
# (point C) to do this. However, we first need to re-load the JSON config from
# the cited JSON config.
config = json.loads(citedConfigText)
bibOut = formattingBibliographyPlugin(bibliographyKeys, config)
f = open("references", "w")
f.write(bibOut)
f.close()
