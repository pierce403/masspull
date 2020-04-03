for ((i=1;i<=254;i++));
do
  echo "Importing $i.0.0.0/8"
  masscan --readscan $i-* -oJ $i.json
  screen -S $i-import -d -m python3 masscan_upload.py $i.json
done

