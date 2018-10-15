""" Utilities functions for dealing with the dali dataset.

It includes all the needed functions for reading files and the helpers for
transforming the annotation information.

GABRIEL MESEGUER-BROCAL 2018
"""
import copy
import glob
import gzip
import json
import os
import pickle

# ------------------------ READING INFO ----------------


def get_files_path(pth, ext='*.gz'):
    """Get all the files with a extension for a particular path."""
    return list_files_from_folder(pth, extension=ext, print_error=False)


def check_absolute_path(directory, print_error=True):
    """Check if a directory has an absolute path or not."""
    output = False
    if os.path.isabs(directory):
        output = True
    elif print_error:
        print("ERROR: Please send an absolute path")
    return output


def check_directory(directory, print_error=True):
    """Return True if a directory exists and False if not."""
    output = False
    if check_absolute_path(directory, print_error):
        if os.path.isdir(directory) and os.path.exists(directory):
            output = True
        elif print_error:
            print("ERROR: not valid directory " + directory)
    return output


def check_file(fl, print_error=True):
    """Return True if a file exists and False if not."""
    output = False
    if check_absolute_path(fl, print_error):
        if os.path.isfile(fl) and os.path.exists(fl):
            output = True
        elif print_error:
            print("ERROR: not valid file " + fl)
    return output


def read_gzip(fl, print_error=False):
    """Read gzip file."""
    output = None
    if check_file(fl, print_error):
        with gzip.open(fl, 'r') as f:
            output = pickle.load(f)
    return output


def list_files_from_folder(directory, extension, print_error=True):
    """Return all the files with a specific extension for a given folder."""
    files = []
    if check_absolute_path(directory, print_error):
        if '*' not in extension[0]:
            extension = '*' + extension
        if check_directory(directory, print_error):
            files = glob.glob(os.path.join(directory, extension))
            if not files and print_error:
                print("ERROR: not files with extension " + extension[1:])
    return sorted(files)


def write_in_gzip(pth, name, data, print_error=False):
    """Write data in a gzip file."""
    if check_directory(pth, print_error):
        save_name = os.path.join(pth, name)
        gz = gzip.open(save_name + '.gz', 'w')
        gz.write(pickle.dumps(data, protocol=2))
        gz.close()
    return


def write_in_json(pth, name, data, print_error=False):
    """Write data in a json file"""
    if check_directory(pth, print_error):
        save_name = os.path.join(pth, name)
        with open(save_name + '.json', 'w') as outfile:
            json.dump(data, outfile)
    return


def read_json(fl, print_error=False):
    """Read json file"""
    output = None
    if check_file(fl, print_error):
        with open(fl, 'r') as outfile:
            output = json.load(outfile)
    return output


def check_structure(ref, struct):
    output = False
    if isinstance(ref, dict) and isinstance(struct, dict):
        # ref is a dict of types or other dicts
        output = all(k in struct and check_structure(ref[k], struct[k])
                     for k in ref)
    else:
        # ref is the type of struct
        output = isinstance(struct, type(ref))
    return output

# -------------- TRANSFORMING THE INFO IN THE ANNOTATIONS --------------


def roll(lower, upper):
    """It merges an horizontal level with its upper. For example melody with
    words or lines with paragraphs
    """
    tmp = copy.deepcopy(lower)
    for info in tmp:
        i = info['index']
        if not isinstance(upper[i]['text'], list):
            upper[i]['text'] = []
        info.pop('index', None)
        upper[i]['text'].append(info)
    return upper


def get_text(text, output=[], m=False):
    """Recursive function for having the needed text for the unroll function.
    """
    if isinstance(text, list):
        tmp = [get_text(i['text'], output) for i in text]
        if isinstance(tmp[0], unicode) or isinstance(tmp[0], str):
                output.append(''.join(tmp))
    elif isinstance(text, unicode) or isinstance(text, str):
        output = text
    return output


def unroll(annot, output=[], depth=0, index=0, b=False):
    """Recursive function that transforms an annotation vector in the format
    vertical format into a horizontal vector:
        - annot (list): annotations vector in vertical formart.
        - output (list): internally used in the recursion, final output.
        - depth (int): depth that the recursion is going to be.
            Example:
            1 - input list of paragraph (annot)
                depth = 0 -> output = horizontal level for paragraphs,
                depth = 1 -> output = lines, depth = 2 -> output = words
                depth = 3 -> output = melody
            2 - input a list of lines (annot[paragraph_i]['text'][line_i])
                depth = 0 -> output = lines, depth = 1 -> words,
                depth = 2 -> melody,
                depth = 3 -> ERROR: not controlled behaviour
        - b (bool) = control if the horizontal level is going to have index
            or not. The paragraph level does not need it.
    """
    if depth == 0:
        """Bottom level to be merged"""
        for i in annot:
            text = get_text(i['text'], output=[])
            if isinstance(text, list):
                text = " ".join(text)
            output.append({'time': i['time'], 'freq': i['freq'], 'text': text})
            if b:
                output[-1]['index'] = index
        index += 1
    else:
        """Go deeper"""
        depth -= 1
        b = True
        for l in annot:
            output, index = unroll(l['text'], output, depth, index, b)
    return output, index


def sample(annot, time_r):
    """Transform the normal time into a discrete value with respect time_r.
    """
    output = copy.deepcopy(annot)
    for a in output:
        a['time'] = (np.round(a['time'][0]/time_r).astype(int),
                     np.round(a['time'][1]/time_r).astype(int))
    return output
