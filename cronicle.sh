
#!/bin/bash

# Copyright (c) 2017 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

readonly PROGNAME=$(basename $0)

usage() {
    cat << EOF
USAGE: $PROGNAME FILE_NAME ROOTDIR_PATH TARGETDIR_NAME NUM_ARCHIVES

EOF
}

fullpath()
{
    echo "$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"
}

cronicle()
{
    local FILE_NAME=$1
    local ROOTDIR_PATH=$2
    local TARGETDIR_NAME=$3
    local NUM_ARCHIVES=$4

    local TARGETDIR_PATH="${ROOTDIR_PATH}/${TARGETDIR_NAME}"
    local FILE_PATH=`fullpath "${ROOTDIR_PATH}/${FILE_NAME}"`

    if [ ! -f ${FILE_PATH} ]; then
        echo "${FILE_PATH}: file not found"
        exit 1
    fi

    # Links dir processing
    mkdir -p $TARGETDIR_PATH
    pushd $TARGETDIR_PATH
    ln -s $FILE_PATH

    while IFS= read -r line; do
        OUTDATED_FILES+=("$line")
    done < <(ls -t | awk 'NR>'${NUM_ARCHIVES})
    for ((i = 0; i < ${#OUTDATED_FILES[@]}; ++i)); do
        unlink "${OUTDATED_FILES[$i]}"
    done

    popd

    # Root dir (data files) processing
    printf '%s ' "${OUTDATED_FILES[*]}"
    pushd $ROOTDIR_PATH
    for ((i = 0; i < ${#OUTDATED_FILES[@]}; ++i)); do
        occs=`find -L . -samefile ${OUTDATED_FILES[$i]} | wc -l | xargs`
        if [ $occs -eq 1 ]; then
            rm ${OUTDATED_FILES[$i]}
        fi
    done
}

main() {
    cronicle $@
}
main $@
