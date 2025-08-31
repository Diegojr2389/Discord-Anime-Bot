from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests

session = requests.Session()

def get_anime(number):
    # Fetch the page
    page_to_scrape = session.get("https://myanimelist.net/anime/season")
    html = page_to_scrape.text

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    first_div = soup.find("div", attrs={"class":"seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1"})
    titles = first_div.find_all("a", attrs={"class":"link-title"})
    scores = first_div.find_all("span", attrs={"class":"js-score"})

    anime_list = []
    for title, score in zip(titles, scores):
        title_text = title.text.strip()
        score_text = score.text.strip()

        # Check if score is a valid float
        try:
            score_value = float(score_text)
        except ValueError:
            score_value = 0

        # Only append if score is a valid float and not 0
        if (score_value > 0):
            anime_list.append((title_text, score_text))
    
    # sort the pairs by score in descending order
    anime_list = sorted(anime_list, key=lambda x: x[1], reverse=True)

    # make the list of anime titles in order without their scores
    anime_list = [title for title, score in anime_list[:number]]
    # anime_list = [(title, score, get_anime_english_name(title['href'])) for title, score in anime_list]
    
    return anime_list

def get_top_10():
    # Fetch the page
    page_to_scrape = session.get("https://myanimelist.net/anime/season")
    html = page_to_scrape.text

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    first_div = soup.find("div", attrs={"class":"seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1"})
    titles = first_div.find_all("a", attrs={"class":"link-title"})
    scores = first_div.find_all("span", attrs={"class":"js-score"})

    pairs = []
    for title, score in zip(titles, scores):
        title_text = title.text.strip()
        score_text = score.text.strip()
        url = title['href']
        
        # Check if score is a valid float
        try:
            score_value = float(score_text)
        except ValueError:
            score_value = 0

        # Only append if score is a valid float and not 0
        if (score_value > 0):
            pairs.append((title_text, score_text, url))

    # sort the pairs by score in descending order
    pairs_sorted = sorted(pairs, key=lambda x: x[1], reverse=True)
    pairs_sorted = pairs_sorted[:10]  # Get top 10

    urls = [url for _, _, url in pairs_sorted]

    english_names = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        english_names = list(executor.map(get_anime_english_name, urls))

    pairs_sorted = [(t, s, u, en) for (t, s, u), en in zip(pairs_sorted, english_names)]
    return pairs_sorted  # Get top 10

def get_genre(specified_genre):
    # Fetch the page
    page_to_scrape = session.get("https://myanimelist.net/anime/season")
    html = page_to_scrape.text

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    first_div = soup.find("div", attrs={"class":"seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1"})
    titles = first_div.find_all("a", attrs={"class":"link-title"})
    all_genres = first_div.find_all("div", attrs={"class": "genres js-genre"})
    properties = first_div.find_all("div", attrs={"class": "properties"})

    pairs = []
    for title, genres, property in zip(titles, all_genres, properties):
        title_text = title.text.strip()
        genre = genres.find_all("a")
        prop = property.find_all("a")
        combined = genre + prop
        url = title['href']
        for c in combined:
            if c.text.strip().lower() == specified_genre.lower():
                pairs.append((title_text, url))
                break
    
    # get the english name of the anime and replace japanese name
    pairs = [(t, u, get_anime_english_name(u)) for t, u in pairs]
    return pairs
        
# make something like !trailer and have the bot send link to trailer on youtube
# get anime name from the url to the anime 
# div id="contentWrapper"
# <strong>

def get_song(anime_name):
    # Fetch the page
    page_to_scrape = session.get("https://myanimelist.net/anime/season")
    html = page_to_scrape.text

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")
    first_div = soup.find("div", attrs={"class":"seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1"})
    titles = first_div.find_all("a", attrs={"class":"link-title"})

    # find the url of the anime
    url = ""
    for title in titles:
        if anime_name == title.text.strip():
            url = title['href']
            break  

    # scrape the animes url for the song
    page_to_scrape_url = session.get(url)
    html = page_to_scrape_url.text

    soup = BeautifulSoup(html, "html.parser")
    # parent doesn't have a class, so we find the span with the class "theme-song-artist"
    # and then find its parent
    child = soup.find("span", attrs={"class":"theme-song-artist"})
    artist = child.text[3:].strip()
    parent = child.find_parent()
    song_name = parent.text.strip()

    pair = [song_name, artist]
    return pair

def get_anime_english_name(url):
    # Fetch the page
    page_to_scrape_url = session.get(url)
    html = page_to_scrape_url.text

    # parse the HTML
    soup = BeautifulSoup(html, "html.parser")
    # find the title of the anime
    title = soup.find("p", attrs={"class":"title-english title-inherit"})
   
    if title is None:
        # if no english title, use the original title
        title = soup.find("h1", attrs={"class":"title-name h1_bold_none"})
    return title.text.strip()