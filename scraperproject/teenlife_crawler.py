import re
import util
import bs4
import queue
import sys
import csv
import pandas as pd


def crawler():
    # starting_url = "https://www.teenlife.com/search/?q=None&l=None&c=Summer%20Program&p=1"
    starting_url = "https://www.teenlife.com/search?q=&l=&c=Summer%20Program&p=1"
    limiting_domain = "www.teenlife.com"
    parsing_default_domain = "https://www.teenlife.com/search"

    numpages = 0
    links_visited = []
    index_list = []
    pages_crawled = 0
    page_parser_q = queue.Queue()
    pull_info_q = queue.Queue()
    page_parser_q.put(starting_url)
    while page_parser_q.empty() == False:
        link = page_parser_q.get()
        mini_crawler(link, page_parser_q, pull_info_q, links_visited, limiting_domain, index_list, parsing_default_domain)
        numpages += 1
        print(link, "link")

    while pull_info_q.empty() == False:
        page_link = pull_info_q.get()
        print(page_link, "page_link")
        request = util.get_request(page_link)
        if request is not None:
	        html = util.read_request(request)
	        soup = bs4.BeautifulSoup(html, features="html5lib")
	        make_index(soup, index_list)


    df = pd.DataFrame(index_list)

    return df



def mini_crawler(url, page_parser_q, pull_info_q, links_visited, limiting_domain, index_list, parsing_default_domain):
    '''
    Crawl the college catalog and adds to an index dictionary to map set of
    words with associated course identifier.

    Inputs:
        url: starting url to begin crawling with
        q: queue of urls in line to be crawled
        links_visited: list of visited links
        limiting_domain: domain name
        index_list: dictionary that maps words to course identifiers
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
    tag_list = soup.find_all("ul", attrs = {"class": "pagination"})
    current_page = tag_list[0].find_all("li", attrs = {"class": "current"})
    next_page = current_page[0].next_sibling.next_sibling.findChild()
    next_page_href = next_page.get('href')
    next_page_href = util.convert_if_relative_url(post_url, next_page_href)
    page_parser_q.put(next_page_href)



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
    tag_list = soup.find_all("div", attrs = {"class":"search-listing-content"})
    for tag in tag_list:
        href_tag = tag.findChild()
        possible_link = href_tag.get('href')
        actual_link = util.convert_if_relative_url(post_url, possible_link)
        if actual_link is not None and actual_link not in links_visited:
            if util.is_url_ok_to_follow(actual_link, limiting_domain):
                pull_info_q.put(actual_link)
    links_visited.append(url)
    if post_url != url:
        links_visited.append(post_url)


def make_index(soup, index_list):
    '''
    Adds words

    Inputs:
        soup: soup object from the text of the HTML document
        index_list: dictionary that maps words to course identifiers
    '''

    #iterate through the q delete the links as you go
    sidebar = {}
    tags = soup.find_all("div", class_ = "row field")
    for tag in tags:
        name, value = pull_values(tag)
        sidebar[name] = value
    location = soup.find_all("div", itemprop="location")
    if location != []:
        location = location[0].text
        location = re.sub(r'[^\w\s]','',location).lower()
        sidebar['location'] = location
    link = soup.find_all("div", id="website_link")
    if link != []:
        href = link[0].a.get("href")
        sidebar['website'] = href
    title = soup.find_all("title")
    if title != []:
        title = title[0].text
        title = re.sub(r'[^\w\s]','',title).lower()
        title = title.replace("\n", " ")
        sidebar['title'] = title
    description1 = soup.find_all("div", class_="listing-description")
    if description1 != []:
        description1 = description1[0].text.lower()
        description1 = re.sub(r'[^\w\s]','',title).strip()
    description2 = soup.find_all("div", class_="listing-more-info")
    if description2 != []:
        description2 = description2[0].text.lower()
        description2 = re.sub(r'[^\w\s]','',title).strip()
    description = description1 + description2
    sidebar['description'] = description
    index_list.append(sidebar)



def pull_values(tag):
    '''
    Creates a set of words and the associated course identifier.

    Inputs:
        tag: div tag object from the soup object

    Outputs:
        (words, course_id): (set of words tied to the course identifier,
        course identifier)
    '''
    #string with ascii values, can I replace 6 or 8 with *? using regex?
    #way to pull list of
    # name_tag = tag.find_all("div", class_="small-6 columns field-name") \d
    name_tag = tag.find_all("span", class_="field-name")
    name = name_tag[0].text
    name = re.sub(r'[^\w\s]','',name).lower()
    value_tags = tag.find_all("div", class_=re.compile(r'field-value'))
    # if len(values_tags) == 1:
    actual_tag = value_tags[0].find_all('span')
    values = []
    for value in actual_tag:
        value = value.text
        value = re.sub(r'[^\w\s]','',value).lower()
        value = value.strip()
        values.append(value)
    if len(values) == 1:
        values = values[0]
    if name == 'entering grades':
        grades = []
        for grade in values:
            grade = re.sub('[^0-9]','', grade)
            grades.append(grade)
        values = grades

    return (name, values)
    # if numbers need to be integer, then would be integer
