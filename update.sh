#!/bin/bash

# run this script to push/pull ./docs to/from server...
#
# push: ./update.sh [delete]            sync remote docs by local ./docs and update database
# pull: ./update.sh download [delete]   sync local ./docs by remote
# !!! delete will delete files at receive side that not exist in remote side !!!
#

PORT=27173
REMOTE=root@server
REMOTE_ROOT=/root/MiBlog

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
else
    gentool_delete=""
    rsync_delete=""
fi

#scp -p -r -P $PORT ./docs $REMOTE:$REMOTE_ROOT/docs
rsync -avh --progress -e 'ssh -p '$PORT'' $rsync_delete ./docs $REMOTE:$REMOTE_ROOT

# easy but dirty...
ssh -p $PORT $REMOTE "cd $REMOTE_ROOT && ./gentool.py update_all $gentool_delete"
