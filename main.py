from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from helper import *
from discord.ext import tasks


"""

Web scraper that monitors an online marketplace (Grailed, for new/used menswear).
The page is scraped every ~ 15 seconds for new listings and the user is notified of said new listings.

Using Selenium, the program scrapes the page's HTML to find specific elements that would be useful
in signifying when something has changed. Using the Discord API simplifies notification and control
functionality (e.g. user can easily start the program and receive messages from Discord).

This program was made and intended for educational/personal use.

"""


# TODO:
# Consider adding Discord message embeds to clean up messages
# Investigate issues with stop command; occasional duplicate/irrelevant notifications


@tasks.loop(seconds=15)
async def grailed_monitor(ctx, driver, past_new_items):
    """
    Loop that begins on user prompt and continuously monitors the given link every 15 seconds.

    :param ctx: the context in which a command is being invoked under
    :param driver: WebDriver
    :param past_new_items: new items that the user has already been notified of
    """

    # Try-catch for the rare occurrence of TimeoutException/StaleElementReferenceException
    # Handling of this has essentially no impact on the functionality
    # (ostrich algorithm, kind of)
    try:
        # Closing the browser
        if grailed_monitor.is_being_cancelled():
            driver.quit()
            await ctx.author.send("Monitoring stopped ... ?")

        # Gets up to 40 feed items (page lazy-loads 40 at a time)
        items = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located
                                                ((By.CSS_SELECTOR, '.listing-age.sub-title')))

        # new_items will contain all of the new items after the refresh
        # Used for comparison with the links that have been accounted for
        new_items = []

        # Explicit wait for safety
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "date-ago")))

        get_new_grailed_items(items, new_items)

        # Calculating difference between sets reveals any items that haven't been accounted for
        items_to_alert = set(new_items) - set(past_new_items)

        await send_alert(items_to_alert, past_new_items, ctx)

    except (StaleElementReferenceException, TimeoutException):
        # Saving a screenshot to examine the issue
        driver.save_screenshot('screenie.png')

    finally:
        print(len(past_new_items))
        print(past_new_items)
        # Regardless of the outcome, refresh the page and try again
        driver.refresh()
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
    """
    Discord command for initial monitor/browser setup.

    :param ctx: the context in which a command is being invoked under
    :param feed_link: Grailed custom feed link to be monitored

    """

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
    """
    Stops the monitor process upon user command.

    :param ctx: the context in which a command is being invoked under

    """

    if grailed_monitor.is_running():
        grailed_monitor.cancel()

    else:
        await ctx.author.send("You are not currently monitoring anything.")


@bot.event
async def on_connect():
    print("Connected")


bot.run(TOKEN)
