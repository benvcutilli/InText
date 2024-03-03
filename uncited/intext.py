# Any numbered items commented on here refer to the stuff in the readme



# The argparse package is from ^^^pythonargparse^^^
import argparse

# pathlib from ^^^pythonpathlib^^^
import pathlib

# Using ^^^pythonre^^^ as imported package
import re

# Reference for this package: ^^^pythonjson^^^
import json

# See ^^^pythonrandom^^^ for this package
import random

# Importing ^^^pythontextwrap^^^
import textwrap

# ^^^pythonhashlib^^^ package
import hashlib

# ^^^pythoncollectionsabc^^^ import
import collections.abc

# Look at ^^^pythonsys^^^ for information about sys
import sys

# "io" is ^^^pythonio^^^
import io




commandLine = argparse.ArgumentParser()
# The file from 1
commandLine.add_argument("metadata",
                         type=str,
                         help="Contains all the information about references and which of them "
                              "each marker uses")
# 9's "inverted" folder
commandLine.add_argument("folder",
                         type=str,
                         help="Where every file in which citations need to be place is put")




commandLineOutput = commandLine.parse_args()


def noPhonies(path: pathlib.Path) -> bool:
    return not path.is_symlink()



def intextHash(content: str) -> str:

    # We don't save the output of sha256(...) to a separate variable and then call digest() on it as
    # the following way is more concise; this idea is from ^^^simplehashing^^^. 12 describes why we
    # use the hexdigest method.
    ################################################################################################
    #                                                                                              #

    feed = content.encode()
    return hashlib.sha256(feed).hexdigest()

    #                                                                                              #
    ################################################################################################




# Opening the .bib^^^inspiration1^^^-like (see 1) file
####################################################################################################
#                                                                                                  #

handle          = open(commandLineOutput.metadata)

try:
    metadata: dict  = json.load(handle)
except json.JSONDecodeError as decodeError:
    print(f"Your configuration file seems to have an issue: {decodeError}")
    sys.exit(34)

handle.close()

#                                                                                                  #
####################################################################################################



# Constants (inspiration to use them instead of being hard-coded unknown)
####################################################################################################
#                                                                                                  #

# See 1a as to why "delimiter" exists
delimiter = re.escape(metadata["delimiter"])

# Ended up using \w+ to keep it simple. Not ideal, but I didn't want to do anything else. I
# believe the "\w+" idea is from something I had done this before, just don't remember for what.
REGULAR_EXPRESSION_MARKER   = f"{delimiter}(?P<marker>\\w*){delimiter}"
# Square brackets as a set of candidate characters was inspired by something I can't remember; Using
# the dash in "a-f" was as well, although not sure where from. See 1a for more details.
REGULAR_EXPRESSION_HASH     = r"(.+)\^([a-f\d]+)"
WIDTH_LEFT                  = 40
WIDTH_RIGHT                 = 57
WIDTH_INITIAL_OFFSET        = 10
REFERENCES_SEPARATOR        = "INTEXT INTERNAL ONLY\n"
NUM_NEWLINES_BEFORE_HASHES  = 14


#                                                                                                  #
####################################################################################################



if not "refkeyToPretty" in metadata:
    metadata["refkeyToPretty"] = dict()

metadata["citeIn"] = [pathlib.Path(path) for path in metadata["citeIn"]]


# In the spirit of points 1-3 we take the files and cite within them (see recursiveBrowse, wrapper,
# and cite) as well as maintain a bibliography (createBibliography)
####################################################################################################
#                                                                                                  #

# These two lines are relevant to 9: making sure we write to the correct paths
writeRoot  = pathlib.Path(commandLineOutput.folder).absolute().parent
sourceRoot = pathlib.Path(commandLineOutput.folder).absolute()

def recursiveBrowse(where: pathlib.Path,
                    callback: collections.abc.Callable[[pathlib.Path, dict], None],
                    meta: dict,
                    shouldDescend: collections.abc.Callable[[pathlib.Path], bool])                 \
                        -> None:

    candidates = where.iterdir()
    for candidate in candidates:
        if candidate.is_dir():
            # See the conditional in wrapper(...) that uses .is_dir() for an explanation for this
            # call:
            callback(candidate, meta)
            if shouldDescend(candidate):
                recursiveBrowse(candidate, callback, meta, shouldDescend)
        elif candidate.is_file():
            callback(candidate, meta)

# Part of the Git-like checking of hashes of 10
####################################################################################################
#                                                                                                  #

if (writeRoot / "references").exists():
    handle             = (writeRoot / "references").open()
    unparsed           = handle.read()
    handle.close()
    
    # I tried to avoid using both sides of this split call because it felt familiar (I was worried I
    # was copying an idea from something or someone), but I can't think of a better way, and I guess
    # I'll just cite what I can.
    bibliography, unparsedHashes = unparsed.split(REFERENCES_SEPARATOR)

    parsed             = re.findall(REGULAR_EXPRESSION_HASH, unparsedHashes)
    hashes             = dict(parsed) 
    bibliography       = io.StringIO(bibliography)

    for key in hashes:
        handle   = open(writeRoot / key) if key != "references" else bibliography
        data     = handle.read()
        handle.close()
        saved    = hashes[key]
        # Called .digest() right off of the code that calls the constructor as in
        # ^^^simplehashing^^^. See 12 for comments related to "hexdigest".
        live     = hashlib.sha256(data.encode()).hexdigest()

        if saved != live:
            print(f"{key} hashes to a different value than expected. Did you modify it instead "
                   "of its equivalent in {sourceRoot}?")
            sys.exit(34)

# Initializing this for when we use this in createBibliography(...)
metadata["hashes"] = dict()

#                                                                                                  #
####################################################################################################



def convertToSymlink(path: pathlib.Path, _: dict) -> None:

    if path.is_symlink():

        # "where" gives us the place to write all files, as described in 9
        ############################################################################################
        #                                                                                          #

        where  = writeRoot / path.absolute().relative_to(sourceRoot)
        # It doesn't make sense to symlink to a file that is contained in commandLineOutput.folder;
        # instead, we try to do so to its equivalent in writeRoot
        if path.resolve().is_relative_to(sourceRoot):
            whereActual = writeRoot / path.resolve().relative_to(sourceRoot)
            # If a symlink is already here, we need to remove it
            where.unlink(True)
            where.symlink_to(whereActual, path.is_dir())
        else:
            # Same rationale for this call as in a few lines up
            where.unlink(True)
            where.symlink_to(path.resolve(), path.is_dir())

        #                                                                                          #
        ############################################################################################


# Regarding 3, "wrapper" was created to separate "cite" from file opening and management because we
# wanted to add the ^^^inspiration^^^ functionality of being able to cite in each entry
# created by createBibliography, and therefore cite is easily callable from that function.
def wrapper(path: pathlib.Path, meta: dict) -> None:

    if path.is_file() and not path.is_symlink():

        # Trying to catch binary and other non-compatible files with this try statement as a failure
        # to decode during .open() strongly suggests that what's inside isn't plain-text.
        # Originally, this kind of intended failure was used to catch unsupported encodings. For
        # example, default encodings on the user or system level may be
        # different^^^encodingissues^^^ than
        # expected, which could affect hashing when feeding the same file to the hashing in two
        # different encodings. However, we never ended up using this for hashing, but for avoiding
        # opening binary files; this can be very useful as a binary file is very likely to have at
        # least one invalid codepoint.
        ############################################################################################
        #                                                                                          #

        original = ""
        try:
            handle = path.open()
            original = handle.read()
            handle.close()
        except:
            # We shouldn't touch this file
            return

        #                                                                                          #
        ############################################################################################
        
        output = cite(original, meta, path)
        
        if (output != original) and not path.absolute().relative_to(sourceRoot) in meta["citeIn"]:
            print(f"{path} potentially has valid markers, but isn't listed in \"citeIn\", so "
                   "we don't have permission to cite in it")
            return

        # Making sure that the files we make don't end up back in sourceRoot (see 9)
        where  = writeRoot / path.absolute().relative_to(sourceRoot)

        # The new file as described in 2, 4
        ############################################################################################
        #                                                                                          #

        handle = where.open("w")
        handle.write(output)
        handle.close()

        #                                                                                          #
        ############################################################################################


        # This line is relevant to 10, including the call to relative_to(...) (don't write the whole
        # path because this would include (and change with) the parents of any code repository this
        # was used with; repositories on different computers that both commit will change this file
        # each time hashes are output (see 7's motivation for why this is a problem) and these
        # problematic extended paths may contain private information as well.
        meta["hashes"][where.relative_to(writeRoot)] = intextHash(output) 

    # This branch creates all directories we encounter. Walking up the tree do do this (from the
    # files) is something that I thought to do before, and it might have been inspired by
    # something, not sure. However, after thinking about doing that, we do this as we go down
    # the tree instead.
    elif path.is_dir() and not path.is_symlink():

        # Also putting these folders in the right place according to 9
        ############################################################################################
        #                                                                                          #

        where = writeRoot / path.resolve().relative_to(sourceRoot)
        where.mkdir(exist_ok=True)

        #                                                                                          #
        ############################################################################################



# See 1a and 1b for details about what this function is looking for
def cite(text: str, meta: dict, path: pathlib.Path) -> str:


    # This function does the actual in-text citing, not the bibliography part, though
    def convert(match: re.Match) -> str:

        marker = match.group("marker")

        output = ""

        # We do this because ^^^inspiration^^^ provides the warnings as well. It also
        # inspired just leaving the attempted in-text citation be. The second if's purposed is
        # similar, but handles the case where someone forgot to put something between what is in the
        # "delimiter" variable; I don't know what ^^^inspiration^^^ does in this scenario.
        ############################################################################################
        #                                                                                          #

        if (not marker in meta["markers"]) and marker != "":
            print(f"Found {marker} in {path}, but {marker} doesn't exist. Skipping.")
            return match[0]

        if marker == "":
            print(f"Found {metadata["delimiter"]}{metadata["delimiter"]} in {path}, but can't"
                  " cite based off this. Skipping.")
            return match[0]

        #                                                                                          #
        ############################################################################################


        for entry in meta["markers"][marker]:

            # Using the same citation style of "[<key>, <locator>]" that can be found elsewhere (I
            # can't remember where, possibly derivative of ^^^citationsinspiration^^^, though there
            # could be others) except the numbers are actually random hexadecimal strings (see the
            # actual generation of those strings for more information); however, we put each
            # citation directly next to each other with nothing separating them. We don't combine
            # citations if they use the same reference; instead, each of them are separate
            # citations, which is prescribed in ^^^secondaryieee^^^.
            ########################################################################################
            #                                                                                      #

            if not entry["refkey"] in meta["refkeyToPretty"]:

                # 7's code
                ####################################################################################
                #                                                                                  #

                if not entry["refkey"] in meta["references"]:
                    print(f"Marker {marker} uses {entry["refkey"]}, but no such reference exists")
                    continue

                referenceInformation = meta["references"][entry["refkey"]]

                engine = hashlib.sha256()
                for thing, associate in referenceInformation.items():
                    engine.update(thing.encode() + associate.encode())
                # Just taking a chunk of the hash, which is common practice. Please read comment 12
                # as it relates to engine.hexdigest()
                prettyReferenceName = engine.hexdigest()[-6:]

                #                                                                                  #
                ####################################################################################

                meta["refkeyToPretty"][entry["refkey"]] = prettyReferenceName

            else:

                prettyReferenceName = meta["refkeyToPretty"][entry["refkey"]]


            # Putting a comma within the citation to separate the locator from the rest might be
            # specifically from something I can't remember and can't figure out with Google
            output += f"[{prettyReferenceName}"

            if "locator" in entry:
                output += f", {entry["locator"]}]"
            else:
                output += f"]"

            #                                                                                      #
            ########################################################################################

        return output


    return re.sub(REGULAR_EXPRESSION_MARKER, convert, text)



# The ordering of data output of this function is discussed by 11
def createBibliography(meta: dict):

    # This function pops but returns the popped-from string as well; it can also pop multiple lines
    # like -- to the best I can remember; I don't know origin of said function -- popn(...) (at
    # least that's what I think it was called, but again, I don't know where it is from). This
    # function isn't general purpose, so 1. it was moved into here with the future goal of allowing
    # different functions for different styles to be specified to match the functionality of
    # ^^^style^^, and 2. having the functionality that "buffer" provides here is most
    # convenient.
    def oneLine(tooLong: str, upTo: int, buffer: str) -> tuple[str, str]:
        if len(buffer) + len(tooLong) <= upTo:
            return buffer + tooLong, ""
        else:
            return buffer + tooLong[:upTo - len(buffer)], tooLong[upTo - len(buffer):]

    # Accumulating all strings into "total" and substrings into "part". This is a technique that is
    # common yet I feel I need to point out that I had some other reference(s) in mind that I had
    # see using this technique when I thought to do it. I just can't remember what it was. It wasn't
    # necessarily specific to strings; just that you repeatedly add something to something else
    # which is outside the loop, no matter the data type.
    ################################################################################################
    #                                                                                              #

    total = ""
    # See 6 for why we just go through the refkeyToPretty entry (those are the only references that
    # were used within the directory of 9 and the configuration file)
    for refkey, pretty in meta["refkeyToPretty"].items():

        part = ""
        info = meta["references"][refkey]
        for which, (title, content) in enumerate(info.items()):

            # We cite here (following the behavior of ^^^inspiration^^^, all of this is
            # described in 3) because these items can also have citations in them
            ########################################################################################
            #                                                                                      #

            content = cite(content, meta, commandLineOutput.metadata)
            title   = cite(title,   meta, commandLineOutput.metadata)

            #                                                                                      #
            ########################################################################################

            if which == 0:
                title = f"{pretty:<{WIDTH_INITIAL_OFFSET}}  {title}"
            else:
                title = f"            {title}"

            # Calls to max(...) inspired by common formulations of ReLU^^^deepsparse^^^. Repeating
            # strings with * is from somewhere; not my idea.
            ########################################################################################
            #                                                                                      #

            count   = len(content) // WIDTH_RIGHT - len(title) // WIDTH_LEFT 
            title   = title    +  " "  *  (WIDTH_LEFT  *  max(count, 0))

            count   = len(title) // WIDTH_LEFT - len(content) // WIDTH_RIGHT
            content = content  +  " "  *  (WIDTH_RIGHT  *  max(count, 0))

            #                                                                                      #
            ########################################################################################

            for place in range(0, len(content), WIDTH_LEFT):
                buffer = " " * (WIDTH_INITIAL_OFFSET + 2)
                if place == 0:
                    buffer = ""
                segContent, content = oneLine(content, WIDTH_RIGHT, "")
                segTitle,   title   = oneLine(title, WIDTH_LEFT, buffer)
                # We insert line breaks so that they don't get too long (we try to keep a file width
                # of 100), a page taken from multiple styles (it's just standard practice at this
                # point)
                part = f"{part}{segTitle:<{WIDTH_LEFT}}{segContent.strip():>{WIDTH_RIGHT+3}}\n"

        total = f"{total}\n{part}"

    #                                                                                              #
    ################################################################################################

    total = f"{total}{"\n" * NUM_NEWLINES_BEFORE_HASHES}"

    # Writing the hashes as described in 10
    ################################################################################################
    #                                                                                              #

    meta["hashes"]["references"] = intextHash(total)

    total = f"{total}{REFERENCES_SEPARATOR}"
    for path in meta["hashes"]:
        total = f"{total}{path}^{meta["hashes"][path]}\n"

    #                                                                                              #
    ################################################################################################

    handle = (writeRoot / "references").open("w")
    handle.write(total)
    handle.close()

#                                                                                                  #
####################################################################################################






# Kick everything off
recursiveBrowse(
    pathlib.Path(commandLineOutput.folder),
    wrapper,
    metadata,
    noPhonies
)

# Gotta handle symbolic links
recursiveBrowse(
    pathlib.Path(commandLineOutput.folder),
    convertToSymlink,
    metadata,
    noPhonies
)

# Calling a function similar to ^^^printbibliography^^^ in that, if you don't, you don't get a
# bibliography. I had that functionality somewhat in mind when I decided to place this here as
# opposed to somewhere else; it usually follows the rest of the code that results in the rended
# paper made by ^^^inspiration^^^.
createBibliography(metadata)
