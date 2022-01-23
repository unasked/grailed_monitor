from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from discord.ext import commands
import os
from dotenv import load_dotenv


bot = commands.Bot(command_prefix='!')
load_dotenv()

# Token associated with your Discord bot goes in a .env file
TOKEN = os.getenv("TOKEN")
PATH = r"C:\Program Files (x86)\chromedriver.exe"


def get_new_grailed_items(unfiltered_list, filtered_list):
    """
    Retrieves only *newly-posted* items from the feed.

    :param unfiltered_list: list of items to extract from
    :param filtered_list: list to append the new items to

    """

    # Looping through every element on the page and only extracting the ones that are new, not bumped
    for element in unfiltered_list:

        # This xpath gets the children of the current element. Used to check # of children -- see below
        children = element.find_elements_by_xpath('.//*')

        # If there is one child, it is known that the current element is a new listing and not a bumped one
        if len(children) == 1:
            # Only extracting the necessary part of the link (ex: https://www.grailed.com/listings/23474046)
            link = element.find_element_by_xpath("parent::*").get_attribute("href")[:41]
            # Accounting for any new items
            filtered_list.append(link)


async def send_alert(items_to_alert, prev_items, ctx):
    """
    Sends a Discord message to the user when a new item is posted.

    :param items_to_alert: list of items to notify user of
    :param prev_items: new items that the user has already been notified of
    :param ctx: the context in which a command is being invoked under

    """

    if len(items_to_alert) > 0:
        # Send a notification for every item in items_to_alert
        for item in items_to_alert:

            if item not in prev_items and len(prev_items) >= 40:
                # If the item hasn't already been accounted for and the storage of previous items is full,
                # then discard the oldest item and add this one
                prev_items.pop()
                prev_items.insert(0, item)

            elif item not in prev_items and len(prev_items) < 40:
                # If not full, proceed normally
                prev_items.insert(0, item)

            await ctx.author.send(f"New item found! {item}")


def grailed_init(feed_link, driver, past_new_items):
    """
    Initializes the browser after the Discord command.

    :param feed_link: Grailed custom feed link to be monitored
    :param driver: WebDriver
    :param past_new_items: new items that the user has already been notified of

    """

    driver.get(feed_link)

    driver.set_page_load_timeout(45)
    driver.implicitly_wait(5)

    # Scrolling and zooming out to retrieve more items than needed; this should prevent notifications of old items
    # ex: A handful of items on the current page are deleted. This would bring older items into view,
    # when they would have been "hidden" due to lazy-loading if the items hadn't been deleted.
    # The below seeks to account for this:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # For some reason, setting the zoom level triggers lazy load
    driver.execute_script("document.body.style.zoom='50%'")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 100);")
    time.sleep(2)

    # Gets all initial feed items via CSS selector, up to 80 for a full feed
    items = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located
                                            ((By.CSS_SELECTOR, '.listing-age.sub-title')))

    # Explicit wait for link to be accessible -- just in case
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "date-ago")))

    # Only extracting items that are newly posted, not old listings that have been bumped to the top
    get_new_grailed_items(items, past_new_items)

    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")

    driver.refresh()
    time.sleep(3)
