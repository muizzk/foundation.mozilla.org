import re
from django import template
from django.template.defaulttags import token_kwargs
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from wagtail.core.rich_text import RichText, expand_db_html

# We don't actually register any tags: the idea is to tap into
# the richtext filter, but that won't let us change _all_ the
# RichText content, so instead of setting up a filter override,
# we literally reach into the RichText class. And change it.
register = template.Library()

# We'll be wrapping the original RichText.__html__(), so make
# sure we have a reference to it that we can call.
__original__html__ = RichText.__html__

# This matches an h1/.../h6, using a regexp that is only
# guaranteed to work because we know that the source of
# the HTML code we'll be working with generates nice
# and predictable HTML code.
heading_re = r"<h(\d)[^>]*>([^<]*)</h\1>"

def add_id_attribute(match):
    """
    This is a regexp replacement function that takes
    in the above regex match results, and then turns:

        <h1>some text</h1>

    Into:

        <h1 id="some-text"><a href="#some-text">some text</a></h1>

    where the id attribute value is generated by running
    the heading text through Django's slugify() function.
    """
    n = match.group(1)
    text_content = match.group(2)
    id = slugify(text_content)
    return f'<h{n} id="{id}""><a href="#{id}">{text_content}</a></h{n}>'

def with_heading_ids(self):
    """
    We don't actually change how RichText.__html__ works, we just replace
    it with a function that does "whatever it already did", plus a
    substitution pass that adds fragment ids and their associated link
    elements to any headings that might be in the rich text content.
    """
    html = __original__html__(self)
    return re.sub(heading_re, add_id_attribute, html)

# Rebind the RichText's html serialization function such that
# the output is still entirely functional as far as wagtail
# can tell, except with headings enriched with fragment ids.
RichText.__html__ = with_heading_ids
