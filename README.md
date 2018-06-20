# Panopticon

A user-focused message logger for Discord, a la the built-in logging present in many IRC clients.

## Dependencies

* Python 3.5 or greater
* [discord.py](https://github.com/Rapptz/discord.py) (rewrite branch)
* pyyaml

## Installation, setup, and usage

* Clone the repo
* Install the requirements `pip install --user -r requirements.txt`
* Copy config.py.example to config.py and edit it
* `./run.py`

## Modules

Panopticon comes with a module called `logexisting.py`. This module is not loaded in by default in the wrapper script for the very simple reason that it enables commands on the running account. If you desire to enable it, change the config file to enable it.

Enabling logexisting.py disables regular logging for that instance of panopticon for as long as it is on. This is to prevent interfering logs.

## License

Panopticon is available under the terms of the BSD 3-clause license, which is located in this repository in the LICENSE file.

logexisting.py is licensed under the AGPLv3

## Credits and Thanks

* Megumi Sonoda ([GitHub](https://github.com/megumisonoda), [Twitter](https://twitter.com/dreamyspell))
* Rapptz for [discord.py](https://github.com/Rapptz/discord.py)
* ihaveamac for his fork of panopticon ([GitHub](https://github.com/ihaveamac), [Twitter](https://twitter.com/ihaveamac))
* Cubebag (Discord user) for serverarchive.py, which helped for a starting point for logexisting.py