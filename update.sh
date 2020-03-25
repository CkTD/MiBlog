#!/bin/bash

# run this script to push/pull ./docs to/from server...
#
# push: ./update.sh [delete]            sync remote docs by local ./docs and update database
# pull: ./update.sh download [delete]   sync local ./docs by remote
# !!! delete will delete files at receive side that not exist in send side !!!
#

PORT=22222
REMOTE=root@47.240.5.208
REMOTE_ROOT=/root/MicroBlog

if [ "$1" = "download" ] ; then
    if [ "$2" = "delete" ] ; then
        rsync_delete="--delete"
    fi 
    #rm -rf ./docs
    rsync -avh --progress -e 'ssh -p '$PORT'' $rsync_delete $REMOTE:$REMOTE_ROOT/docs .
    exit
fi

if [ "$1" = "delete" ] ; then
    gentool_delete=delete
    rsync_delete="--delete"
fi


echo "Backing up..."
backupdir=./backup/`date +%Y-%m-%d:%H-%M-%S`
ssh -p $PORT $REMOTE "cd $REMOTE_ROOT && mkdir -p $backupdir && cp -r ./docs $backupdir"

echo "Copying files..."
rsync -avh --progress -e 'ssh -p '$PORT'' $rsync_delete ./docs $REMOTE:$REMOTE_ROOT

echo "Updating db..."
ssh -p $PORT $REMOTE "cd $REMOTE_ROOT && ./gentool.py update_all $gentool_delete"

