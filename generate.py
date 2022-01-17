#!/bin/python3

#https://github.com/andrea-varesio/vanity-PyGP

print('\n**************************************************')
print('"Vanity PyGP" - Securely generate PGP keys with a custom ID.')
print('Copyright (C) 2022 Andrea Varesio (https://www.andreavaresio.com/).')
print('This program comes with ABSOLUTELY NO WARRANTY')
print('This is free software, and you are welcome to redistribute it under certain conditions')
print('Full license available at https://github.com/andrea-varesio/vanity-PyGP')
print('**************************************************\n\n')

import gpg
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
    '''
    , shell=True, check=True, executable='/bin/bash')

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

    c = gpg.Context(armor=True, offline=True, home_dir=GNUPGHOME)

    f = open('var.tmp', 'w')
    f.write('export GNUPGHOME=' + GNUPGHOME + '\nexport FILTER=' + filter)
    f.close()

    print('Downloading gpg.conf')
    wget.download('https://raw.githubusercontent.com/drduh/config/master/gpg.conf', GNUPGHOME)
    print('\n\nIt is now recommended that you DISABLE networking for the remainder of the process')
    input('Press ENTER to continue\n')

    createVCcontainer()
    encrContainer = '/media/veracrypt44/'

    realname = input('\nEnter your Name: ')
    email = input('Enter your Email: ')
    userid = realname + ' <' + email + '>'

    i = 0
    start = datetime.now()

    while True:
        checkEntropy()
        dmkey = c.create_key(userid, algorithm='ed25519', expires=False, sign=False, certify=True, force=True)
        fingerprint = format(dmkey.fpr)
        i += 1
        entropy = getEntropy()
        print('Elapsed time: ' + str(datetime.now()-start) + ' | Entropy: ' + str(entropy) + ' | Try #' + str(i))
        if fingerprint[-len(filter):] == filter:
            break
        else:
            f = open('fp.tmp', 'w')
            f.write('export fingerprint=' + fingerprint)
            f.close()
            subprocess.run(
            r'''
                source fp.tmp
                source var.tmp
                gpg --batch --yes --delete-secret-and-public-keys ${fingerprint}
            '''
            , shell=True, check=True, executable='/bin/bash')
            os.remove(GNUPGHOME + '/openpgp-revocs.d/' + fingerprint + '.rev')

    print('\nMATCH FOUND')
    keyid = fingerprint[-16:]

    f = open(encrContainer + 'publickey-0x' + keyid + '.asc', 'wb')
    f.write(c.key_export(pattern=fingerprint))
    f.close()

    f = open(encrContainer + 'secretkey-0x' + keyid + '.key', 'wb')
    f.write(c.key_export_secret(pattern=fingerprint))
    f.close()
    os.chmod(encrContainer + 'secretkey-0x' + keyid + '.key', 0o600)

    shutil.copytree(GNUPGHOME, encrContainer + os.path.basename(GNUPGHOME))
    print('Securely erasing tmp files and unmounting encrypted container...')
    subprocess.run(
    r'''
        source var.tmp
        srm -r $GNUPGHOME || rm -rf $GNUPGHOME
        veracrypt -d /media/veracrypt44 || echo 'Could not unmount container'
    '''
    , shell=True, check=True, executable='/bin/bash')

print('If you are in an ephemeral environment, make sure to save the VeraCrypt container somewhere safe and recoverable!')

if os.path.isfile('fp.tmp'):
    os.remove('fp.tmp')
os.remove('var.tmp')

print('\nExiting...\n')
sys.exit(0)
