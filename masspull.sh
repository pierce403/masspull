for ((i=1;i<=254;i++)); 
do 
  echo "Scanning $i.0.0.0/8"
  ./masscan $i.0.0.0/8 -p `cat ports.txt` --excludefile exclude.conf --rate 1000000 -oB $i-`date +%s`.bin
done

