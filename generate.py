#!/bin/python3

#https://github.com/andrea-varesio/vanity-PyGP

print('\n**************************************************')
print('"Vanity PyGP" - Securely generate PGP keys with a custom ID.')
print('Copyright (C) 2022 Andrea Varesio (https://www.andreavaresio.com/).')
print('This program comes with ABSOLUTELY NO WARRANTY')
print('This is free software, and you are welcome to redistribute it under certain conditions')
print('Full license available at https://github.com/andrea-varesio/vanity-PyGP')
print('**************************************************\n\n')

import sys
import os
import subprocess
import time
import tempfile
import wget
from datetime import datetime

def getEntropy():
    f = open('/proc/sys/kernel/random/entropy_avail','r')
    entropy = int(f.readlines()[0])
    f.close()
    return entropy

def checkEntropy():
    entropy = getEntropy()
    if entropy<2000:
        print('Entropy: ',entropy)
        print('Not enough entropy')
        print('Trying again in 60 seconds')
        print('Use this time to type as many random characters as possible\n')
        time.sleep(60)
        entropy = getEntropy()
        if entropy<2000:
            print('\nEntropy: ',entropy)
            print('Not enough entropy')
            print('Try again when the entropy is above 2000')
            print('You can check the available entropy with "generate.py -e"')
            print('Exiting...')
            sys.exit(1)
        else:
            print('\n\n\n')

def createVCcontainer():
    subprocess.run(
    r'''
        source var.tmp
        printf '\nCreating a new VeraCrypt container...\n'
        veracrypt -t -c --volume-type normal --size=500M --encryption=AES-Twofish-Serpent --hash=Whirlpool --filesystem=EXT4 --pim=0 --keyfiles="" vanity-pygp-$FILTER.hc
        printf '\nMounting the newly created container...\n'
        veracrypt -t -k "" --pim=0 --keyfiles="" --protect-hidden=no vanity-pygp-$FILTER.hc /media/veracrypt44
        gpg --gen-random --armor 0 24 > /media/veracrypt44/passphrase.txt
    '''
    ,
    shell=True, check=True,
    executable='/bin/bash')

if len(sys.argv)<2:
    print('ERROR    :   You need to pass one argument\n')
    print('USAGE    :   generate.py [FILTER] [-e]\n')
    print('-e       :   check available entropy')
    print('FILTER   :   find a key with ID matching this filter')
    sys.exit(1)
else:
    if sys.argv[1] == '-e':
        print('Entropy :', getEntropy())
        sys.exit(0)
    elif '-' in sys.argv[1]:
        print('ERROR    :   Invalid argument\n')
        print('USAGE    :   generate.py [FILTER] [-e]\n')
        print('-e       :   check available entropy')
        print('FILTER   :   find a key with ID matching this filter')
        sys.exit(1)
    else:
        filter = sys.argv[1]
        print('Looking for keys matching',filter)

checkEntropy()

now = datetime.now()
now = (now.strftime('_%Y%m%d_%H%M%S'))

with tempfile.TemporaryDirectory(prefix='gnupg_', suffix=now) as GNUPGHOME:

    f = open('var.tmp', 'w')
    f.write('export GNUPGHOME=' + GNUPGHOME + '\nexport FILTER=' + filter)
    f.close()
    print('Downloading gpg.conf')
    wget.download('https://raw.githubusercontent.com/drduh/config/master/gpg.conf', GNUPGHOME)
    print('\n\nIt is now recommended that you DISABLE networking for the remainder of the process')
    input('Press ENTER to continue\n')

    createVCcontainer()

    realname = input('\nEnter your Name: ')
    email = input('Enter your Email: ')
    f = open('/media/veracrypt44/passphrase.txt','r')
    passphrase = f.readlines()[0]
    f.close()
    f = open('/media/veracrypt44/gpg_batch.txt', 'w')
    f.writelines(['Key-Type: 22','\nKey-Curve: ed25519', '\nKey-Usage: cert', '\nName-Real: ' + realname, '\nName-Email: ' + email, '\nExpire-Date: 0', '\nPassphrase: ' + passphrase])
    f.close()
    passphrase = None; del passphrase

    match = 'no'
    i = 0
    start=datetime.now()
    while 'no' in match:
        checkEntropy()
        subprocess.run(
        r'''
            source var.tmp
            export FILTER_LEN=${#FILTER}
            export KEYID="$(gpg --batch --gen-key /media/veracrypt44/gpg_batch.txt 2>&1 | grep -o -P '(?<= )[A-Z0-9]{16}')"
            export KEYFINGERPRINT="$(gpg --with-colons --fingerprint --list-secret-keys $KEYID 2>&1 | sed -n 's/^fpr:::::::::\([[:alnum:]]\+\):/\1/p')"
            export NEWKEY=${KEYFINGERPRINT:(-${FILTER_LEN})}
            if [ "${NEWKEY}" == "${FILTER}" ];
            then
                export match="yes"
                printf "\nMatch found: ${KEYFINGERPRINT}\n"
                gpg --armor --export ${KEYFINGERPRINT} > /media/veracrypt44/publickey.asc
                gpg --batch --pinentry-mode loopback --passphrase-file /media/veracrypt44/passphrase.txt --quiet --armor --export-secret-keys ${KEYFINGERPRINT} > /media/veracrypt44/secretkey.key
                cp -ar $GNUPGHOME /media/veracrypt44/keyring/
                gpg --batch --yes --delete-secret-keys ${KEYFINGERPRINT}
                srm -r $GNUPGHOME || rm -rf $GNUPGHOME
                unset GNUPGHOME
                veracrypt -d vanity-pygp-$FILTER.hc
            else
                export match="no"
                rm ${GNUPGHOME}/openpgp-revocs.d/*
                gpg --batch --yes --delete-secret-keys ${KEYFINGERPRINT}
                gpg --batch --yes --delete-keys ${KEYFINGERPRINT}
            fi
            echo "${match}" > match.tmp
        ''',
        shell=True, check=True, capture_output=False,
        executable='/bin/bash')
        f = open('match.tmp','r')
        match = f.readlines()[0]
        i += 1
        entropy = getEntropy()
        print('Elapsed time: ' + str(datetime.now()-start) + ' | Entropy: ' + str(entropy) + ' | Try #' + str(i))

print('If you are in an ephemeral environment, make sure to save the VeraCrypt container somewhere safe and recoverable! ')
print('\nExiting...\n')

os.remove('var.tmp')
os.remove('match.tmp')

sys.exit(0)
