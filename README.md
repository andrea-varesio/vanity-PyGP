# Vanity PyGP

## What is it
This tool will securely generate a certification-only ed25519 PGP master key with ID matching your specified filter (ie: 0x1234567890FILTER), using a hardened configuration.

More specifically, a temporary directory `/tmp/gnupg_XXX_%Y%m%d_%H%M%S` will be used as ephemeral GNUPGHOME and securely erased when finished. An encrypted VeraCrypt container will be created and populated with ~passphrase,~ secret key, public key, and keyring (with revocation certificate), generated.

Currently, generated keys are not protected with a passphrase, so you should add one if you wish. You should then take care to generate encryption, signing and, authentication subkeys (this could be automated, if requested).

At every iteration of the key generation process, the available entropy will be checked and, if it falls below 2000, the script will pause for 60 seconds giving you the chance to input random data.

## Requirements
- `gpgme` (see table below)
- Install python requirements with: `pip install -r requirements.txt`
- VeraCrypt ([download](https://veracrypt.fr/en/Downloads.html))
- `secure-delete` is also strongly recommended (ie. `sudo apt install secure-delete`)

OS | package | example command
---|---|---
alpine | py3-gpgme | `apk add py3-gpgme`
debian / ubuntu | python3-gpg | `apt install python3-gpg`
MacOS (homebrew) | gpgme | `brew install gpgme`

## How to use it
Launch `generate.py` and pass your filter as argument (ie. `python3 generate.py FILTER`). You'll then be asked for a password for the creation of a VeraCrypt container. When prompted, you should disable networking. You'll then be able to enter your name and email address for the uid of the pgp key. When a key matching your filter is found, the secret key along the public key and the keyring will be copied into the VeraCrypt container, which will then be dismounted. At this point you should save this container somewhere safe and recoverable.

Alternatively, run `python3 generate.py -e` to only check the available entropy.

## Contributions
Contributions are welcome and appreciated, feel free to submit issues and/or pull requests.

### To-Do
- Further improve key generation speed
- Move away from subprocess: look into native solutions for:
  - creating encrypted containers
  - deleting unused keys from keyring
  - secure-deleting tmp directory
- Improve argument parsing system

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
