# get target
TARGET=`curl https://masspull.org/getwork | jq '.target'`

mkdir -pv output # ensure the output dir exists

# ensure the target is a number between 0 and 255 (exclusive)
if [ "$TARGET" -gt 0 ] && [ "$TARGET" -lt 255 ]
then
  echo "Scanning $TARGET.0.0.0/8"

  if test -f paused.conf
  then
    echo "found pause file!"
    masscan --resume paused.conf

  else
    masscan $TARGET.0.0.0/8 -p `cat ports.txt` --excludefile exclude.conf --rate 1000000 -oL output/$TARGET-`date +%s`.txt

  fi
  exit
fi

echo illegit target?!

