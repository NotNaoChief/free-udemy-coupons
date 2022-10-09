"""
Scrape r/FreeUdemyCoupons for posts in the lasts two days.

This scraper goes through the 200 newest posts the r/FreeUdemyCoupons.
If a posts title is in english, checked via google translates' detect
language, is less than 2 days old, and not in the already owned courses
whitelist dictionary, the posts title and coupon url will be added to a
list. The list will then be used to enroll in the free course. The post
title will be added to the whitelist dictionary. So it can be ignored,
in future posts.
"""
import datetime as dt
import json
import praw
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox
from circumventGoogleTest.encodeURL import encode_url

# initiate scraper with 'coupon_scraper' site_settings.
reddit = praw.Reddit(site_name='coupon_scraper')

# Pick a subreddit
subreddit = reddit.subreddit('FreeUdemyCoupons')

# sort by newest, limit to 200 posts.
r_free_udemy_coupons_new = subreddit.new(limit=10)

# Initialize Selenium Browser
options = Options()
options.add_argument("--headless")
browser = Firefox(options=options)
browser.implicitly_wait(10)


def convert_date(created_utc: int):
    """Convert Reddit Timestamp to Datetime Object"""
    return dt.datetime.fromtimestamp(created_utc)



encoding_data = {
    '`': '%60',
    '@': '%40',
    '#': '%23',
    '$': '%24',
    '%': '%25',
    '^': '%5E',
    '&': '%26',
    '=': '%3D',
    '+': '%2B',
    '[': '%5B',
    ']': '%5D',
    '{': '%7B',
    '}': '%7D',
    '/': '%2F',
    '|': '%7C',
    ';': '%3B',
    ':': '%3A',
    "'": '%27',
    '"': '%22',
    ',': '%2C',
    '<': '%3C',
    '>': '%3E',
    '?': '%3F',
    ' ': '%20'
}


# To prevent errors with title to url conversion
def encode_url(text):
    temp = []
    temp.append('https://translate.google.com/?sl=auto&tl=en&text=')
    for char in text:
        if char in encoding_data:
            temp.append(encoding_data[char])
        else:
            temp.append(char)
    temp.append('&op=translate')
    return ''.join(temp)


def is_english(post_title: str):
    """
    Via Google Translate, determine post title is in english.

    The post_title arg is passed to the encode_url function, which encodes
    the text to be URL UTF-8 compliant. It is then joined with the first
    half and last half of a google translate URL.

    Selenium is used to access the url, and extra the element with the
    detected language. This element is stored as 'language'. The .text
    attribute holds the string 'SOMELANGUAGE - DETECTED', where
    SOMELANGUAGE is the language found. To get just the language, for
    comparison, the 'language.text' attribute is split, and then index 0
    is taken.

    'language' is then compared to the string 'ENGLISH', to determine if
    the text is in english.

    :param post_title: Title of Reddit Post.
    :type post_title: str
    :return: True if English, False if Not
    :rtype: BOOL

    """
    url = encode_url(post_title)
    browser.get(url=url)
    language = browser.find_element_by_css_selector('#c1 > span')
    language = language.text.split()[0]

    if language == 'ENGLISH':
        language = True
    else:
        language = False

    return language


# Whitelist Dict of owned courses.
with open('ownedCourses.json', 'r') as f:
    owned_courses = json.load(f)

found_coupons = {}

# Extract title, time, and coupon url, from new posts, that are in
# in english, and I don't already have.
for post in r_free_udemy_coupons_new:

    # Determine time passed since posted.
    now = dt.datetime.now()
    post_time = convert_date(post.created_utc)
    time_passed = now - post_time
    days_passed = time_passed.days
    days_passed = int(days_passed)

    # Clean up the title, they all say '[100% off]'
    post_title = post.title.strip('[100% off]')
    
    # Assigns True or False to post_in_eng
    post_in_eng = is_english(post_title)

    coupon_link = post.url

    # Is the link still fresh?
    if days_passed < 2:

        # Is the title in english, continue if not.
        if post_in_eng is True:

            # Do I already have this course, continue if so.
            if post_title not in owned_courses.keys():
                # Save Link, add course to list of courses.
                found_coupons[post_title] = coupon_link

            # Already have this course
            else:
                pass
        # Not in english, continue to next post.
        else:
            continue
    # Link older than 2 days, dead link.
    else:
        break

browser.close()

with open('ownedCourse.json', 'w') as f:
    json.dump(found_coupons, fp=f, indent=4)
