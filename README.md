# grailed_monitor

The idea for this project had been floating around in my head for a long time, so being able to bring it to life
was incredibly rewarding. If interested, you can find some general commentary/issues encountered during development below:

Integrating the Discord API was incredibly helpful. Of course, Discord in and of itself is a messaging app, so it's
easy to send an accessible notification to a user who can see it from their own phone or computer. 
The function decorator @tasks.loop is an integral part of the functionality, as it provides a fairly
stress-free way to loop something without having to worry about timeouts, disconnections, or anything similar.

Selenium is another key component of the program. WebDriverWait is used to wait until specific HTML elements
are available before trying to access them. Selenium also provides a fairly simple way to access web elements -
by class name, xpath, id, or whatever is needed. Different elements in the HTML required different ways to
access those elements. For example, some items were only available via xpath, links had to be extracted, 
and some elements were only easily accessible by retrieving a child element.

Of course, there were obstacles posed by the nature of the site. I'll give a quick rundown of how the site
works and how the program consequently works. Grailed can more or less be thought of as eBay but exclusively
for fashion-related items, and new items are constantly being posted. There's a feature on Grailed that allows
a user to create their own "custom feeds," in which they can choose which items to see. For example, a user
could create a custom feed which would only show all Nike high-top sneakers in size 11 and under $200. 
These custom feeds are generally used to only find specific items that someone would potentially be interested
in buying. Every custom feed has a unique link. The program takes the link as input and does the work from 
there.

Items are generally shown on the feed in order date newest -> oldest. An item is considered "new" if 
it was just posted, or if it was posted a while ago and "bumped" back to the top. It makes sense for
a user to only want to be notified of truly new listings, and not ones that have been bumped. (The idea
is that if a great deal on an item comes up, you'd want to be notified ASAP.) New items can be separated
from bumped items by examining a certain HTML element. In short, if this specific element has one child,
it's guaranteed to be a new listing. If there are two children, it was bumped, e.g. not new. The program
accounts for this, and only takes into consideration those items that are truly new.
The program keeps track of all the new items that have been "seen" already, so that there's no chance of a 
duplicate notification being sent.

Grailed also uses lazy-loading in their feed. By default, 40 items are displayed on a page until the user
scrolls down far enough, at which point 40 more listings are loaded ad infinium. Initially I was examining
the first 40 listings to be loaded and comparing the page on the next refresh to the previous one.
But what if some items happen to be deleted? In that case, items outside of the first 40 would creep back
up into the initial view, and then some of those items might be considered "new" by the program since they
hadn't been seen before. The user shouldn't be notified of these items since they could have been posted
hours ago. To remedy this, I executed Javascript on the page to scroll down, trigger the lazy-load, and
consequently get the first 40+40 items. However, on every consequent refresh, only the first 40 are examined.
In this way, the program initially "looks at more items than it needs to" to account for this particular
situation.

I would occasionally come across StaleElementReferenceExceptions, and after countless hours of testing I could
never find out how to remedy it 100%. By adding necessary waits to ensure the page is loaded correctly,
the frequency of this occurring was sharply lowered but is still not 100% clean. Thankfully the standard for
error handling in Python is "to ask for forgiveness rather than permission," so I ended up just wrapping the
affected code in a try-catch. If this exception is ever encountered (which is rare now), the program simply 
refreshes the page and tries again.

Finally, I came across an issue with item links. Each link is formatted as such:
https://www.grailed.com/listings/######## .... Each link always ends with eight numbers followed by associated
keywords separated by dashes. For some reason, the keywords would occasionally change despite the item staying
the same otherwise. This would throw off the program and cause it to "not recognize" an item that had previously
been recognized. This fix was pretty easy -- I just truncated all the keywords and left the unique eight-digit
identifier, since I knew that would always be the same.
