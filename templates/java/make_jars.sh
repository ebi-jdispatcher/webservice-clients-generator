#!/bin/sh

ant -lib lib resolve
ant -lib lib

rm -rf bin lib

for j in *.jar
do
    echo Processing $j
    tmpfile=$(mktemp /tmp/abc-script.XXXXXX)
    cp jar_header.sh $tmpfile
    cat $j >> $tmpfile
    mv $tmpfile ${j}
    chmod 755 ${j}
done

echo "Completed"
