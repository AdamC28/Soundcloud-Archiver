import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import requests
from mutagen import id3, mp3
import youtube_dl
import time
from datetime import datetime

#automates scrolling down until all tracks are loaded into DOM
def scroll_down(driver):

    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:

        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page.
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:

            break

        last_height = new_height

#gets all links to upload of a specific media type defined by xpath
def get_media_links(url, linkList, xpath):
    driver.get(url)
    scroll_down(driver)
    media = driver.find_elements(By.XPATH, xpath)

    for link in media:
        linkValue = link.get_attribute('href')
        linkList.append(linkValue)
        #print(linkValue)

#function to substitute problematic characters from filenames
def sanitizeString(string):
    table = str.maketrans("/\\<>|$", "-_()-S", ":*?\"")
    return string.translate(table)

#hook function which automatically tags a file ripped by youtube_dl with MP3 metadata
def myHook(d):
        global trackIndex, info_dict

        if d['status'] == 'finished':
            print("Finished downloading track!")

            if info_dict == None or not ("entries" in info_dict.keys()):
                id3tag(d['filename'], None, trackIndex)
            else:
                id3tag(d['filename'], info_dict['entries'][trackIndex], trackIndex)
            trackIndex += 1

#function with assigns specific MP3 metadata to each ripped file, based on what media type is being downloaded
def id3tag(path, metadata, trackNum):
        
        global scrapeData

        #id3 tagging / cover art embedding
        testAudio = mp3.MP3(path)
        testAudio.tags = id3.ID3()

        #implies that this track is being ripped as a single / standalone, put in generic directory
        if metadata == None:

            #title
            testAudio['TIT2'] = id3.TIT2(encoding=3, text=scrapeData["trackName"])

            #album title
            testAudio["TALB"] = id3.TALB(encoding=3, text=f"{scrapeData['artistName']} Soundcloud Files")

            #artist
            testAudio['TPE1'] = id3.TALB(encoding=3, text=f"{scrapeData['artistName']}")

            #album artist
            testAudio['TPE2'] = id3.TALB(encoding=3, text=f"{scrapeData['artistName']}")

            #track num
            testAudio['TRCK'] = id3.TRCK(encoding=3, text="")

            #year timestamp
            testAudio['TYER'] = id3.TYER(encoding=3, text="")

        #implies that this track is being ripped as part of an album/playlist, and assigned appropriate metadata in its tags
        else:

            #title
            testAudio['TIT2'] = id3.TIT2(encoding=3, text=metadata["title"])

            #album title
            if scrapeData["schema"] == "albums" or scrapeData["schema"] == "sets":
                testAudio["TALB"] = id3.TALB(encoding=3, text=f"{scrapeData['trackName']}")

            elif scrapeData["schema"] == "reposts":
                if scrapeData["repostType"] == "sets":
                    testAudio["TALB"] = id3.TALB(encoding=3, text=f"{scrapeData['trackName']}")

                elif scrapeData["repostType"] == "tracks":
                    testAudio["TALB"] = id3.TALB(encoding=3, text=f"{profileName} Soundcloud Reposts")

            #artist
            testAudio['TPE1'] = id3.TPE1(encoding=3, text=metadata["uploader"])

            #album artist
            if scrapeData["schema"] == "reposts":
                testAudio['TPE2'] = id3.TPE2(encoding=3, text=profileName)
            else:
                testAudio['TPE2'] = id3.TPE2(encoding=3, text=scrapeData["artistName"])
            #track num
            testAudio['TRCK'] = id3.TRCK(encoding=3, text=f"{trackNum + 1}")
            #year timestamp
            testAudio['TYER'] = id3.TYER(encoding=3, text=scrapeData["pubyear"])

        #cover art
        try:
            with open(f'{path[:-3]}jpg', 'rb') as cover:
                testAudio['APIC'] = id3.APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3, desc=u'Cover',
                    data=cover.read()
                )
        except FileNotFoundError:
            print("No thumbnail available. Skipping embed...")

        testAudio.save()

def downloadMedia(list, mediaType):
    for link in list:

        print(f"Downloading {link}")

        global scrapeData, trackIndex
        repostType = ""

        #timestamping
        scrapeTime = time.time()

        source = requests.get(link)

        #THE IMPORTANT FIX THAT LETS THIS SCRIPT WORK WITH UNICODE CHARACTERS!
        source.encoding = 'utf-8'

        soup = BeautifulSoup(source.text, "html.parser")
        nScript = soup.body.find_all('noscript')[1].article

        #track and artist name are contained in hyperlinks
        links = nScript.header.h1.find_all('a')

        trackName = links[0].text
        artistName = links[1].text

        #retrieves release date from formatted time tag
        pubdate = (nScript.time.text).split('T')[0]
        pubyear = pubdate.split('-')[0]

        print(f'Title: {trackName}\nArtist: {artistName}\nYear: {pubyear}')

        sanitizedTitle = sanitizeString(trackName)
        sanitizedArtist = sanitizeString(artistName)

        print(f'{artistName} - {sanitizedArtist}')
        print(f'{trackName} - {sanitizedTitle}')

        if mediaType == "albums":
            outputTemplate = f'{str(sanitizedArtist)}/Albums/{str(sanitizedTitle)}/{str(sanitizeString("%(title)s"))}.%(ext)s'
        elif mediaType == "sets":
            outputTemplate = f'{str(sanitizedArtist)}/Playlists/{str(sanitizedTitle)}/{str(sanitizeString("%(title)s"))}.%(ext)s'
        elif mediaType == "tracks":
            outputTemplate = str(sanitizedArtist) + "/" + str(sanitizedArtist) + " Soundcloud Files/" + str(sanitizedTitle) + ".%(ext)s"
        elif mediaType == "reposts":
            if link.split("/")[4] == "sets":
                outputTemplate = f'{profileName}/Reposts/{str(sanitizedArtist)}/{str(sanitizedTitle)}/{str(sanitizeString("%(title)s"))}.%(ext)s'
                repostType = 'sets'
            
            else:
                outputTemplate = profileName + "/Reposts/" + str(sanitizedArtist) + "/" + str(sanitizedTitle) + ".%(ext)s"
                repostType = 'tracks'

        #ripping sc file with youtube_dl
        ydl_opts = {
            "outtmpl": outputTemplate,
            "writethumbnail": True,
            "quiet": True,
            "verbose": False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }],
            'progress_hooks': [myHook]
        }

        scrapeData = {
            "trackName": trackName,
            "artistName": artistName,
            "pubyear": pubyear,
            "repostType": repostType,
            "schema": mediaType
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            global info_dict
            info_dict = ydl.extract_info(link, download=False)
            
            try:
                ydl.download([link])
            except:
                print(f"----ERROR WHILE DOWNLOADING {link}")

        trackIndex = 0
        scrapeData = None
        repostType = ""
        info_dict = None

        #sleep for 3 seconds between successful track rip to minimize bandwidth usage
        time.sleep(3)

##################
### USER INPUT ###
##################

url = ""
downloadReposts = True

#######################
### WEBDRIVER SETUP ###
#######################

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("headless")
options.add_argument("--log-level=OFF")

driver = webdriver.Chrome(options=options)
driver.get(url)
driver.execute_script("document.body.style.zoom='80%'")

wait = WebDriverWait(driver, 10)
wait.until(EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))).click()

time.sleep(2)
profileName = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[2]/div/div[1]/div/div[2]/h2').text

try:
    verified = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[2]/div/div[1]/div/div[2]/h2/div/span/span')
except NoSuchElementException:
    print("Profile is not verified!")
else:
    profileName = " ".join(profileName.split(" ")[:-1])

print(profileName)

albumLinks = []
playlistLinks = []
trackLinks = []
mainXpath = '//*[@id="content"]/div/div[4]/div[1]/div/div[2]/div/ul/li/div/div/div[2]/div[1]/div/div/div[2]/a'

repostLinks = []
repostXpath = '//*[@id="content"]/div/div[4]/div[1]/div/div[2]/div/ul/li/div/div/div/div[2]/div[1]/div/div/div[2]/a'

print("--- Getting main media ---")
get_media_links(f'{url}/albums', albumLinks, mainXpath)
get_media_links(f'{url}/sets', playlistLinks, mainXpath)
get_media_links(f'{url}/tracks', trackLinks, mainXpath)

if downloadReposts:
    print("--- Getting reposts ---")
    get_media_links(f'{url}/reposts', repostLinks, repostXpath)

driver.quit()

################
### DOWNLOAD ###
################

info_dict = None
trackIndex = 0
scrapeData = None
repostType = ""

startTime = datetime.now()
timestampString = f'{startTime.month}-{startTime.day}-{startTime.year}-{startTime.hour}-{startTime.minute}-{startTime.second}'

downloadSchemas = {
    "albums": albumLinks,
    "sets": playlistLinks,
    "tracks": trackLinks
}
if downloadReposts:
    downloadSchemas["reposts"] = repostLinks

for schema, list in downloadSchemas.items():
    downloadMedia(list, schema)