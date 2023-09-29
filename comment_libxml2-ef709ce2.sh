#!/bin/bash
# set -e: Instructs the script to exit immediately if any command within it returns a non-zero exit status.
# set -u: If the script tries to access a variable that has not been set or assigned a value, it will cause the script to exit.
# set -o pipefail: This option sets the exit status of a pipeline to the rightmost command that returns a non-zero exit status. By default, the exit status of a pipeline is the exit status of the last command in the pipeline. However, with pipefail enabled, the script will consider the pipeline as failed if any command within the pipeline fails, providing a more accurate status.
set -euo pipefail



git clone https://gitlab.gnome.org/GNOME/libxml2.git libxml2_ef709ce2
cd libxml2_ef709ce2; git checkout ef709ce2


# ls:
# source_file.c makefile *obj-aflgo,*obj-aflgo/temp

# SUBJECT = .
# TMP_DIR = ./obj-aflgo/temp
# targets = ./obj-aflgo/temp/BBtargets.txt
# outdir = ./obj-aflgo/temp
# AFLGO should be expert !

mkdir obj-aflgo; mkdir obj-aflgo/temp

export SUBJECT=$PWD; export TMP_DIR=$PWD/obj-aflgo/temp
export CC=$AFLGO/instrument/aflgo-clang; export CXX=$AFLGO/instrument/aflgo-clang++
export LDFLAGS=-lpthread
export ADDITIONAL="-targets=$TMP_DIR/BBtargets.txt -outdir=$TMP_DIR -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"


# define targets
git diff -U0 HEAD^ HEAD > $TMP_DIR/commit.diff
wget https://raw.githubusercontent.com/jay/showlinenum/develop/showlinenum.awk
chmod +x showlinenum.awk
mv showlinenum.awk $TMP_DIR
cat $TMP_DIR/commit.diff |  $TMP_DIR/showlinenum.awk show_header=0 path=1 | grep -e "\.[ch]:[0-9]*:+" -e "\.cpp:[0-9]*:+" -e "\.cc:[0-9]*:+" | cut -d+ -f1 | rev | cut -c2- | rev > $TMP_DIR/BBtargets.txt


# make clean
./autogen.sh; make distclean

# cd obj-aflgo. compile the file for the first time!
cd obj-aflgo; CFLAGS="$ADDITIONAL" CXXFLAGS="$ADDITIONAL" ../configure --disable-shared --prefix=`pwd`
make clean; make -j4
# After compliling, BBnames.txt, BBcalls.txt etc files has been generated

# Shape BBnames.txt, BBcalls.txt files
cat $TMP_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > $TMP_DIR/BBnames2.txt && mv $TMP_DIR/BBnames2.txt $TMP_DIR/BBnames.txt
cat $TMP_DIR/BBcalls.txt | sort | uniq > $TMP_DIR/BBcalls2.txt && mv $TMP_DIR/BBcalls2.txt $TMP_DIR/BBcalls.txt


# distance calculation HERE
$AFLGO/distance/gen_distance_orig.sh $SUBJECT/obj-aflgo $TMP_DIR xmllint

# compile the file for the second time!
CFLAGS="-distance=$TMP_DIR/distance.cfg.txt" CXXFLAGS="-distance=$TMP_DIR/distance.cfg.txt" ../configure --disable-shared --prefix=`pwd`
make clean; make -j4

# disable the -e option
set +e

# Run fuzzer
mkdir in; cp $SUBJECT/test/dtd* in; cp $SUBJECT/test/dtds/* in
$AFLGO/afl-2.57b/afl-fuzz -m none -z exp -c 45m -i in -o out ./xmllint --valid --recover @@
