# Vanity PyGP

## What is it
This tool will securely generate a certification-only (pass `--signing-key` if you also want sign capability) ed25519 PGP master key with ID matching your specified filter (ie: 0x1234567890FILTER), using a hardened configuration.

More specifically, a temporary directory `/tmp/gnupg_XXX_%Y%m%d_%H%M%S` will be used as ephemeral GNUPGHOME and securely erased when finished. All necessary files will be encrypted with an automatically-generated encryption key.

Currently, generated keys are not protected with a passphrase, so you should add one if you wish. You should then take care to generate encryption, signing and, authentication subkeys (this could be automated, if requested).

Every 10 seconds during the key generation process, the available entropy will be checked and, if it falls below 2000, the script will pause for 60 seconds giving you the chance to input random data.

## Requirements
**1)** `gpgme` (see table below)<br />
**2)** Install python requirements with: `pip install -r requirements.txt`

OS | package | example command
---|---|---
alpine | py3-gpgme | `apk add py3-gpgme`
debian / ubuntu | python3-gpg | `apt install python3-gpg`
MacOS (homebrew) | gpgme | `brew install gpgme`

## How to use it
Launch `generate.py` and pass your filter as argument (ie. `python3 generate.py -f FILTER`). When prompted, you should disable networking. You'll then be able to enter your name and email address for the uid of the pgp key (or pass them with `-n NAME -e EMAIL`). When a key matching your filter is found, the secret key and the revocation certificate will be encrypted and copied with the public key in the designated directory.

If you don't want any prompts, you can run the command below:
```
generate.py -f FILTER -n NAME -e EMAIL
```
If you want no verbosity at all, remove `-s` and pass `-q`

Alternatively, run `python3 generate.py -c` to only check the available entropy.

Usage:
```
generate.py [-h] [-f FILTER] [-n NAME] [-e EMAIL] [-p PATH] [-q] [--disable-stats] [--signing-key] [-c]
```

Short | Argument | Info
---|---|---
`-h` | `--help` | show this help message and exit
`-f FILTER` | `--filter FILTER` | Find a key with ID matching this filter
`-n NAME` | `--name NAME` | Specify the uid name
`-e EMAIL` | `--email EMAIL` | Specify the uid email
`-p PATH` | `--path PATH `| Specify a path to save the generated key
`-q` | `--quiet` | Disable the majority of prompts and verbosity
/ | `--disable-stats` | Disable stats every 10 seconds
/ | `--signing-key` | Add sign capability to the master key
`-c` | `--check-entropy` | Check the available entropy, then exit

## How to decrypt saved files
Simply run `decrypt.py` from within the folder that contains the encrypted files. You can either decrypt all files at once with `-a` or only the files you need with `-f FILE` (one at the time).

Note: make sure that `encryption-key.key` is present otherwise you won't be able to decrypt any file.

Usage:
```
decrypt.py [-h] [-a | -f FILE]
```
Short | Argument | Info
---|---|---
`-h` | `--help` | show this help message and exit
`-a` | `--all` | Decrypt all files
`-f FILE` | `--file FILE` | Specify a file to decrypt

## Contributions
Contributions are welcome and appreciated, feel free to submit issues and/or pull requests.

### To-Do
- Further improve key generation speed

### Known issues

## Credits
Tips and hardened gpg.conf from [YubiKey-Guide](https://github.com/drduh/YubiKey-Guide)

## LICENSE

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

"Vanity PyGP" - Securely generate PGP keys with a custom ID.<br />
Copyright (C) 2022 Andrea Varesio <https://www.andreavaresio.com/>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a [copy of the GNU General Public License](https://github.com/andrea-varesio/vanity-PyGP/blob/main/LICENSE)
along with this program.  If not, see <https://www.gnu.org/licenses/>.

<div align="center">
<a href="https://github.com/andrea-varesio/vanity-PyGP/">
  <img src="http://hits.dwyl.com/andrea-varesio/vanity-PyGP.svg?style=flat-square" alt="Hit count" />
</a>
</div>
