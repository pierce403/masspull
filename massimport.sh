for ((i=1;i<=255;i++));
do
  echo "Importing $i.0.0.0/8"
  masscan --readscan data/$i-* -oL import/$i.txt
  screen -S $i-import -d -m python3 nweb_upload.py import/$i.txt
done

