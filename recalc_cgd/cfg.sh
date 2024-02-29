#!/bin/bash

for f in $(ls -1d ./dot-files/cfg.*.dot); do

  # Skip CFGs of functions we are not calling
  if ! grep "$(basename $f | cut -d. -f2)" ./dot-files/callgraph.dot >/dev/null; then
    printf "\nSkipping $f..\n"
    continue
  fi

  #Clean up duplicate lines and \" in labels (bug in Pydotplus)
  awk '!a[$0]++' $f > ${f}.smaller.dot
  mv $f $f.bigger.dot
  mv $f.smaller.dot $f
  sed -i s/\\\\\"//g $f
  sed -i 's/\[.\"]//g' $f
  sed -i 's/\(^\s*[0-9a-zA-Z_]*\):[a-zA-Z0-9]*\( -> \)/\1\2/g' $f

  #Compute distance
  printf "\nComputing distance for $f..\n"
  $AFLGO/distance/distance_calculator/distance.py -d $f -t ./BBtargets.txt -n ./BBnames.txt -s ./BBcalls.txt -c ./distance.callgraph.txt -o ${f}.distances.txt >> ./step${STEP}.log 2>&1 #|| FAIL=1
  if [ $? -ne 0 ]; then
    echo -e "\e[93;1m[!]\e[0m Could not calculate distance for $f."
  fi
done

cat ./dot-files/*.distances.txt > ./distance.cfg.txt
read -p "bb calc done"