#!/bin/bash

# run this script to push ./docs to server...
# delete is dangerous...


if [ "$1" = "delete" ] ; then
    gentool_delete=delete
    rsync_delete="--delete"
else
    gentool_delete=""
    rsync_delete=""
fi

PORT=27173
REMOTE=root@server
REMOTE_ROOT=/root/MiBlog

#scp -p -r -P $PORT ./docs $REMOTE:$REMOTE_ROOT/docs
rsync -av -e 'ssh -p '$PORT'' $rsync_delete ./docs $REMOTE:$REMOTE_ROOT


# easy but dirty...
ssh -p $PORT $REMOTE "cd $REMOTE_ROOT && ./gentool.py update_all $gentool_delete"
