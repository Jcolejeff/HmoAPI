#!/bin/bash
cd ../api/$1
mkdir $2
cd $2
files_to_create=("models" "router" "schemas" "services" "exceptions")

for i in ${files_to_create[@]}
do 
    touch "$i".py
done

touch __init__.py


# TODO: Add boilerplate code into the files