import re
import util
import bs4
import queue
import sys
import pandas as pd
import data_scraping

def crawler():
    # starting_url = "https://www.teenlife.com/search/?q=None&l=None&c=Summer%20Program&p=1"
    starting_url = "https://rusticpathways.com/students/programs?_=1584132668586&page=1"
    limiting_domain = "rusticpathways.com"

    numpages = 0
    links_visited = []
    index_list = []
    pages_crawled = 0
    page_parser_q = queue.Queue()
    pull_info_q = queue.Queue()
    page_parser_q.put(starting_url)
    while page_parser_q.empty() == False:
        link = page_parser_q.get()
        mini_crawler(link, page_parser_q, pull_info_q, links_visited, limiting_domain, index_list)
        numpages += 1

    while pull_info_q.empty() == False:
        page_link = pull_info_q.get()
        # print(page_link)
        request = util.get_request(page_link)
        if request is not None:
            html = util.read_request(request)
            soup = bs4.BeautifulSoup(html, features="html5lib")
            make_index(soup, index_list, page_link)
            # print(index_list)
    df = pd.DataFrame(index_list)
    return df




def mini_crawler(url, page_parser_q, pull_info_q, links_visited, limiting_domain, index_list):
    '''
    Crawl the college catalog and adds to an index list to map set of
    words with associated course identifier.

    Inputs:
        url: starting url to begin crawling with
        q: queue of urls in line to be crawled
        links_visited: list of visited links
        limiting_domain: domain name
        index_list: list of dictionaries for each webpage
    '''
    if url in links_visited:
        return
    request = util.get_request(url)
    if request is None:
        return
    post_url = util.get_request_url(request)
    if post_url in links_visited:
        return
    html = util.read_request(request)
    soup = bs4.BeautifulSoup(html, features="html5lib")
    find_links(soup, url, post_url, pull_info_q, links_visited, limiting_domain)
    tag_list = soup.find_all("ul", attrs = {"class": "Pagination"})
    pages = tag_list[0].find_all("li")
    pages = pages[1:]
    for page in pages:
        page_parser_q.put(page.findChild().get('href'))



def find_links(soup, url, post_url, pull_info_q, links_visited, limiting_domain):
    '''
    Adds links to be visited to the queue 'q' and adds links visited to the list
    'links_visited.'

    Inputs:
        soup: soup object from the text of the HTML document
        url: starting url to begin crawling with
        post_url: this is the processed absolute url
        q: queue of urls that is being added to for each url crawled
        links_visited: list of visited links
        limiting_domain: domain name
    '''
    tag_list = soup.find_all("div", attrs = {"class": "Grid Grid--SpacingResponsiveLarge"})
    link_list = tag_list[0].find_all('h3', {"class": "Card__Title"})
    for link in link_list:
        possible_link = link.findChild().get("href")
        # possible_link = parsing_default_domain + possible_link
        actual_link = util.convert_if_relative_url(post_url, possible_link)
        if actual_link is not None and actual_link not in links_visited:
            if util.is_url_ok_to_follow(actual_link, limiting_domain):
                pull_info_q.put(actual_link)
    links_visited.append(url)
    if post_url != url:
        links_visited.append(post_url)

def make_index(soup, index_list, link):
    '''
    Adds dictionaries to the index list.

    Inputs:
        soup: soup object from the text of the HTML document
        index_list: list of dictionaries that maps words to course identifiers
        link: current webpage link
    '''
    sidebar = {}
    title = soup.find_all("title")[0].text
    title = re.sub(r'[^\w\s]','',title).lower()
    title = title.strip()
    title = re.sub('\n+','', title)
    title = re.sub('\s+',' ', title)
    sidebar['title'] = title
    tags = soup.find_all("div", class_ = "Layer Layer--BackgroundWatercolor Util__MobileOnly Special__PrintProgramDetails")
    tags = tags[0].find_all("li", class_ = "Table__Row")
    for tag in tags[::]:
        sidebar['website'] = link
        name, value = pull_values(tag)
        value = value.strip('\n')
        if name == 'ages':
            value = value.replace('-',',')
            value = re.sub(r'[a-z]+', ' ', value).strip(' ').split(',')
            value_list = []
            for val in value:
                val = val.strip('\n')
                value_list.append(val)
            value = value_list
        if name == "service types":
            value = re.sub('\n+',' ', value)
        if name == 'cost':
            name = 'minimum_cost'
            value = value.split('plus')[0]
            value = re.sub('\D','', value)
        if name == 'session length':
            value = re.sub('\D','', value)
            value = int(value) // 7
        if name == 'program types':
            value = re.sub('\n+',' ', value)
        sidebar[name] = value
    tags1 = soup.find_all("div", class_ = "Layer Layer--PaddingBottomLarge")
    description = tags1[0].find_all("div", class_="TextBlock")
    description = description[0].find_all('p')
    description = description[0].text.lower()
    description = re.sub(r'[^\w\s]','',description).strip()
    description = re.sub('\n+',' ', description)
    sidebar['description'] = description
    dates = soup.find_all("h4", class_ = "Heading Heading--Title Heading--FontSizeSmaller Heading--FontWeightLight")
    session_start = []
    for date in dates:
        date = date.text.lower()
        date = date.split(' ')[0]
        date = date.strip('\n')
        session_start.append(date)
    sidebar['session start'] = session_start
    index_list.append(sidebar)


def pull_values(tag):
    '''
    Matches categories to their values.

    Inputs:
        tag: div tag object from the soup object

    Outputs:
        (words, course_id): (set of words tied to the course identifier,
        course identifier)
    '''
    name_tag = tag.find_all("div", class_="Heading Heading--Label")
    name = name_tag[0].text
    name = re.sub(r'[^\w\s]','',name).lower()
    name = name.strip()
    if name == 'duration':
        name = 'session length'
    if name == 'country':
        name = 'location'
    if name == 'programtypes':
        name = 'category'
    value_tags = tag.find_all("span", class_="Heading Heading--Datum")
    if value_tags == []:
        value_tags = tag.find_all("h3", class_="Heading Heading--Datum")
        actual_tag = value_tags[0].find_all('a', class_="FlagLink")
        if len(actual_tag) > 0:
            actual_tag = actual_tag[0].text.lower()
        else:
            actual_tag = ""
    else:
        actual_tag = value_tags[0].text.lower()
    return (name, actual_tag)
