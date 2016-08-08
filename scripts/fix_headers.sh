#!/bin/bash

FILES=*.py
BLACKLIST="brewer2mpl.py" # ignore files listed here

COPYRIGHT=$(cat <<EOF
#!/usr/bin/env python\n\
#\n\
# Copyright (c) 2013-2016, ETH Zurich.\n\
# All rights reserved.\n\
#\n\
# This file is distributed under the terms in the attached LICENSE file.\n\
# If you do not find this file, copies can be found by writing to:\n\
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
EOF
)

for f in $FILES; do

	if (echo $BLACKLIST | grep $f); then
		echo "Skipping $f"
		continue;
	fi

	has_header=0
	(grep 'ETH Zurich' -q $f) && has_header=1
	(grep 'Copyright' -q $f) && has_header=1

	# Check if the header is outdated
	C_HEADER=$(grep -i 'Copyright' $f | grep '2016'); RC=$?
	if [[ $RC -eq 1  ]]; then
		echo "File $f: copyright header outdated .. "
		sed -i -e '/Copyright/d' $f

		has_header=0
	fi

	echo "$f -- header = $has_header"

	if [[ $has_header -eq 0 ]]; then

		# Replace the header
		# ------------------------------

		TMP=$(mktemp)
		echo -e ${COPYRIGHT} > $TMP
		cat $f | grep -v '#!' >> $TMP

		cp -b $TMP $f

		rm $TMP
	fi
done
