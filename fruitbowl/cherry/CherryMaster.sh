#!/bin/bash
usage() { echo "Usage: $0 [-d run from dois] [-p run from urls] [-s seek urls] " 1>&2; exit 1; }

while getopts ":d:p:s" o; do
    case "${o}" in
        d)
            d=${OPTARG}
            python -b initialise.py $OPTARG
            python -b collect.py "shake"
            python -b consume.py
            python -b analyse.py
            ;;
        p)
            p=${OPTARG}
            python -b initialise.py $OPTARG
            python -b collect.py "pick"
            python -b consume.py
            python -b analyse.py
            ;;
        s)
            s=${OPTARG}
            python -b initialise.py $OPTARG
            python -b seek.py 1 "uk depts.json"
            python -b consume.py
            python -b analyse.py
            ;;
        *)
            echo "No file or flag given, running from defaults"
            python -b initialise.py "infile.json"
            python -b collect.py "pick"
            python -b consume.py
            python -b analyse.py
            ;;
    esac
done
shift $((OPTIND-1))


