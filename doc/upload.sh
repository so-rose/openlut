#!/bin/bash

REMOTE=sofus@wakingnexus

rsync -avzP build/html/* $REMOTE:~/openlut/

#ssh $REMOTE 'bash -s'  << 'ENDSSH'
#
#cd /var/www/openlut
#chown -R www-data:www-data *
#
#ENDSSH
