import re
import requests
import util
import bs4
import queue
import sys
import csv
import pandas as pd
import data_scraping

def crawler():
    # starting_url = "https://www.teenlife.com/search/?q=None&l=None&c=Summer%20Program&p=1"
    starting_url = "https://www.summerdiscovery.com/finder?location=&grade=&length="
    limiting_domain = "www.summerdiscovery.com"

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
        make_index(index_list, page_link)
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
        index_list: list of dictionaries for individual programs
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
    find_links(soup, url, post_url, page_parser_q, pull_info_q, links_visited, limiting_domain)



def find_links(soup, url, post_url, page_parser_q, pull_info_q, links_visited, limiting_domain):
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
    tag_list = soup.find_all("div", attrs = {"class": "program_listing"})
    link_list = tag_list[0].find_all('li', {"class": "revealer"})
    for link in link_list:
        possible_link = link.findChild().get("href")
        actual_link = util.convert_if_relative_url(post_url, possible_link)
        if actual_link is not None and actual_link not in links_visited:
            if util.is_url_ok_to_follow(actual_link, limiting_domain):
                pull_info_q.put(actual_link)
    links_visited.append(url)
    if post_url != url:
        links_visited.append(post_url)


def make_index(index_list, link):
    '''
    Adds dictionaries to the index list.
    Inputs:
        index_list: list of dictionaries that maps words to course identifiers
        link: current webpage link
    '''
    # link2 = "https://www.summerdiscovery.com/ucla/academic-options"
    page = requests.get(link)
    link2 = link + "/academic-options"
    page2 = requests.get(link2)
    if page is None or page2 is None:
        return
    soup2 = bs4.BeautifulSoup(page2.content, "html.parser")

    courses = soup2.findAll("ul", {"class": "academics_pro"})
    desc_dict = {}
    for course in courses:
        course_name = course.findAll("span", {"class": "academics_subjectName"})[0].text
        course_name = ''.join([i for i in course_name if not i.isdigit()]).strip().lower()
        if course_name not in desc_dict:
            desc_dict[course_name] = ''
        descriptions = course.findAll("span", {"class": "academics_courseBody"})
        for description in descriptions:
            desc = description.findAll("p")[0].text.lower()
            old_desc = desc_dict[course_name]
            desc_dict[course_name] = old_desc + ' ' + desc


    # link = "https://www.summerdiscovery.com/ucla"
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    all_camps = soup.findAll("span", {"class": "datesAndPrices"})
    camps = all_camps[0].findAll("li")

    program = soup.findAll("h3", {"class": "location_subPageSectionHeader"})
    program = program[0].text.lower()

    location = soup.findAll("div", {"class": "locLocation_header"})
    location = ''.join(location[0].text.lower().split(','))
    age_grade = soup.findAll("span", class_="locHeader3")
    age_grade = age_grade[0].text.lower()
    rough_grades = re.search('grades(.+?)[(]', age_grade).group(1).split(",")
    grades = []
    for grade in rough_grades:
        grade = grade.replace(' ', '')
        grades.append(grade)
    ages = re.search('[(](.+?)[)]', age_grade).group(1).replace('-',',')
    ages = re.sub(r'[a-z]+', ' ', ages).strip(' ').split(',')

    for camp in camps:
        dct = {"ages": ages, "grades": grades, "location": location, "website": link}
        tuition = camp.findAll("span", {"class": "dpTuition"})
        tuition = ''.join(tuition[0].text.lower().split('$')[1].split(','))
        dct["minimum cost"] = tuition
        dates = camp.findAll("span", {"class": "dpHeader"})
        dates = dates[0].text.lower()
        dates = dates[:len(dates) - len(tuition) - 1]
        start_date = dates.split('-')[0][:-1]
        dct["session start"] = start_date
        duration = camp.findAll("span", {"class": "dpDuration"})
        prog = duration[0].text.split(' (')[0].lower()
        dct["program"] = program + ' ' + prog
        dct["session length"] = ' '.join(duration[0].text.lower().split(' ')[:2])
        category = camp.findAll("span", {"class": "dpAcademics"})
        dct["category"] = category[0].text.lower()
        categories = dct["category"]
        text = ''
        for cat in categories.split(', '):
            if cat in desc_dict:
                text += desc_dict[cat]
                text += '\n'
        dct["description"] = text
        index_list.append(dct)
