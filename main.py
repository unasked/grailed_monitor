from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv


"""

Web scraper that monitors an online marketplace ("Grailed", for new/used menswear).
The page is scraped every ~ 15 seconds for new listings, and the user is notified of said new listings.


Using Selenium, the program scrapes the page's HTML to find specific elements that would be useful
in signifying when something has changed. Using the Discord API simplifies notification and control
functionality (user can easily start/stop the program and receive messages from Discord).


I've had this idea for a while now, so finally bringing it to life is incredibly rewarding!
Working at it and seeing it come to fruition has been a great learning experience.


@author Joshua Boehm

This program was made and intended for educational/personal use.

"""

# TODO:
# Add message embeds to clean up messages
# Implement classes?
# Add README

# FIXME:
# Make sure driver closes correctly after calling !stop


# Small testing link: "https://www.grailed.com/shop/Vd-HjojbEg"
# Large testing link: "https://www.grailed.com/shop/38QUFy4BTg"
# Yeezy slide link: "https://www.grailed.com/shop/XxQ6Xdknxg"
# Yeezy slide link (sorted by new): https://www.grailed.com/shop/-aQYuBVGUQ

bot = commands.Bot(command_prefix='!')
load_dotenv()

TOKEN = os.getenv("TOKEN")
GRAILED_RATE = 15
PATH = r"C:\Program Files (x86)\chromedriver.exe"
stop = False


# -------------------------------------- "Helper" methods --------------------------------------


def get_new_grailed_items(unfiltered_list, filtered_list):
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
    driver.get(feed_link)

    driver.set_page_load_timeout(45)
    driver.implicitly_wait(5)

    # Scrolling and zooming out to retrieve more items than needed.
    # In theory this will prevent notifications of old items
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


# ----------------------------------------------------------------------------------------------


@tasks.loop(seconds=15)
async def grailed_monitor(ctx, driver, past_new_items):
    try:
        if stop:
            print("About to quit")
            driver.quit()
            print("After quit")

            grailed_monitor.stop()

        # Gets up to 40 feed items (page lazy-loads 40 at a time)
        items = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located
                                                ((By.CSS_SELECTOR, '.listing-age.sub-title')))

        # new_items will contain all of the new items after the refresh
        # Used for comparison with the links that have been accounted for
        new_items = []

        # Explicit wait for safety
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "date-ago")))

        # Only getting new items
        get_new_grailed_items(items, new_items)

        # Calculating difference between sets reveals any items that haven't been accounted for
        items_to_alert = set(new_items) - set(past_new_items)

        # Send the alert
        await send_alert(items_to_alert, past_new_items, ctx)

    except (StaleElementReferenceException, TimeoutException):
        # Saving a screenshot to examine the issue
        driver.save_screenshot('screenie.png')

    finally:
        print(len(past_new_items))
        print(past_new_items)
        # Regardless of the outcome, refresh the page and try again
        driver.refresh()

        # Waiting until three iframe tags are present might fix the issue of irrelevant items being picked up?
        # FIXME: there must be a cleaner way to do this. Also sometimes there are 5 iframes? Investigate
        # iframes = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
        #
        # while len(iframes) < 4:
        #     iframes = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
        #     print(len(iframes))

        # WebDriverWait in conjunction with JS to wait until the page is loaded after refresh
        WebDriverWait(driver, 10).until(lambda tmp: driver.execute_script
                                        ('return (document.readyState === "complete")'))


@bot.command(
    name='hi',
    help="An amicable greeting."
)
async def say_hi(ctx):
    await ctx.author.send("Hey there")


@bot.command(
    name='monitor',
    help='Type !monitor [insert Grailed link] to receive live notifications'
)
async def grailed_start(ctx, feed_link):
    global stop
    stop = False

    past_new_items = []
    driver = webdriver.Chrome(PATH)

    # Open page for the first iteration (needs to be handled separately)
    grailed_init(feed_link, driver, past_new_items)
    # tasks.loop begins afterwards
    grailed_monitor.start(ctx, driver, past_new_items)


@bot.command(
    name='stop',
    help='Stops monitoring your feed.'
)
async def grailed_stop(ctx):
    if grailed_monitor.is_running():
        # TODO: Quit session
        global stop
        stop = True

    else:
        await ctx.author.send("You are not currently monitoring anything.")


@bot.event
async def on_connect():
    print("Connected")


bot.run(TOKEN)
