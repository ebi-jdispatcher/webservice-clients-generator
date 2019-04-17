#!/bin/sh
# This is a simple header which can make a standard executable JAR into a
# true executable on Linux. It should be prepended to the start of the JAR
# file. Note the 4 empty lines on the end are important
MYSELF=`which "$0" 2>/dev/null`
[ $? -gt 0 -a -f "$0" ] && MYSELF="./$0"
java=java
if test -n "$JAVA_HOME"; then
    java="$JAVA_HOME/bin/java"
fi
exec "$java" $java_args -jar $MYSELF "$@"
exit 0





