This is a script I have developed to create comprehensive archives of Soundcloud pages. It downloads every track available on a given Soundcloud page as an MP3 and performs appropriate ID3 tagging, along with track/album art; there is also optional functionality to download all reposts as well.

**USER INPUT**

To use this script, simply set the ``url`` to a full url address for a Soundcloud page, e.g: ``https://soundcloud.com/kendrick-lamar-music``. The ``downloadReposts`` flag can be set to ``True`` or ``False`` depending on whether you want the script to also download every track, album, etc.. that has been reposted onto the given page.

**DOWNLOAD STRUCTURE**

Running this script will create a directory under its root directory, named after the given Soundcloud page. It will create up to three subdirectories here:
- **Albums** (where all albums will be located)
- **Playlists** (see above)
- **{artist name} Soundcloud Files** (rips of every track on the page, including duplicates of those included in all Albums and Playlists, will be included here)
- **Reposts** (this will contain subdirectories for every artist whose tracks/albums/etc. were reposted onto the given page. they will each follow the same download structure recursively)

**TECHNOLOGIES USED**

Out of many packages used to power this script, these are the most essential / those which I researched the most thoroughly to make this script possible:
- **Selenium**: automates the simulated Chromium browser, which is used to load every track on the given Soundcloud page into the browser's DOM before downloading them
- **BeautifulSoup**: simplifies process of webscraping in Python; used to extract audio metadata from static Soundcloud page DOM
- **youtube_dl**: makes downloading the tracks possible in the first place; functionality regarding download quality, metadata, tagging, etc... are used extensively in this script
- **Mutagen**: Python module that provides the ID3 tagging required for MP3 downloads; allows downloads to be readily used in audio players with comprehensive metadata visualization

**CONSIDERATIONS**

This script is powered by the [Chrome WebDriver](https://sites.google.com/chromium.org/driver/), which makes it possible for Selenium to access webpages using Chrome / Chromium. This repo currently contains the WebDriver version suited for Chrome version **131.0.6778.85**. Please follow the provided link to obtain a WebDriver .exe for different Chromium versions.

While the script downloads all associated artwork from a given track, album, or playlist, it does not assign the artwork to the audio file itself via ID3 tagging. This must be done manually; I will look into providing a utility script to quickly accomplish this in the future.
