#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import io
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from beem import Hive
from beem.account import Account


def download_image(image_url, path):
    try:
        response = requests.get(image_url, timeout=30)
    except requests.RequestException as e:
        print(f"Error processing the image {image_url}: {e}")
        return None

    if response.status_code != 200:
        print(f"Error downloading the image: {image_url} (Status Code: {response.status_code})")
        return None

    # Extract the file extension
    parsed_url = urlparse(image_url)
    _, ext = os.path.splitext(parsed_url.path)

    # Generate a unique filename with UUID
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(path, unique_filename)

    # Save the image to disk
    with open(file_path, 'wb') as f:
        f.write(response.content)

    print(f"Image downloaded and saved as: {file_path}")
    return unique_filename


def extract_images_from_markdown(markdown_content):
    # Search for images in the format ![alt](image_url)
    image_urls = re.findall(r'!\[.*?\]\((.*?)\)', markdown_content)
    return image_urls


def fetch_posts(account, last, all_posts, today, today_date, yesterday):
    # The node caps get_blog at 20 per call, so page through it with
    # start_entry_id until we have what we need.
    page_limit = 20
    posts = []
    start_entry_id = 0
    while True:
        page = account.get_blog(start_entry_id=start_entry_id, limit=page_limit)
        if not page:
            break
        posts.extend(page)

        if last:
            break

        if not all_posts:
            # Blog entries come back newest first, so once we've paged past
            # the target date window there's nothing older left to find.
            oldest_date = page[-1]["created"].date()
            target_date = today_date if today else yesterday
            if oldest_date < target_date:
                break

        if len(page) < page_limit:
            break
        start_entry_id += len(page)

    if last:
        posts = [posts[0]] if posts else []
    return posts


def save_post(post, path, author, platform):
    markdown_content = post['body']
    title = post['title']
    permlink = post['permlink']
    link_for_post = f'https://{platform}.blog/@{author}/{permlink}'

    # Download images and replace the links in markdown
    images = post.get('json_metadata', {}).get('image', [])
    if isinstance(images, str):
        images = [images]

    if images:
        print(f"Images found in the post (json_metadata): {images}")

    # Extract images from markdown
    markdown_images = extract_images_from_markdown(markdown_content)

    if markdown_images:
        print(f"Images found in markdown: {markdown_images}")

    # Download all images found in json_metadata and markdown
    all_images = images + markdown_images
    for image_url in all_images:
        downloaded_image_name = download_image(image_url, path)
        if downloaded_image_name:
            markdown_content = markdown_content.replace(image_url, downloaded_image_name)

    post_final = (
        f'---\n<br />**Originally posted on {platform.capitalize()} network: '
        f'[{link_for_post}]({link_for_post})** <br />\n----'
    )
    yaml_prefix = '---\n'
    title_yaml = title
    for char in (':', '\'', '#', '(', ')'):
        title_yaml = title_yaml.replace(char, '')

    # Get the post tags and categories
    tags = post.get('json_metadata', {}).get('tags', [])
    tags_str = "\n".join([f"  - {tag}" for tag in tags])

    # Set the category as the first tag or "General" if there are no tags
    category = tags[0] if tags else "General"
    network_label = "Hive" if platform == 'hive' else "Steemit"
    category_str = f'  - {category.capitalize()}\n  - {network_label}\n'

    # Build the YAML prefix
    yaml_prefix += f'title: {title_yaml}\n'
    yaml_prefix += f'date: {post["created"]}\n'
    yaml_prefix += f'permlink: /{platform}/{permlink}\n'
    yaml_prefix += 'type: posts\n'
    yaml_prefix += f'categories:\n{category_str}\n'
    yaml_prefix += f'tags:\n{tags_str}\n'
    yaml_prefix += f'author: {author}\n---\n'

    # Filename
    post_date = post["created"].date()
    filename = os.path.join(path, f"{post_date}_{permlink}.md")

    # Save the content to a Markdown file
    with io.open(filename, "w", encoding="utf-8") as f:
        f.write(yaml_prefix + markdown_content + post_final)

    print(f"Post saved: {filename}")


def main(author, path, last=False, include_actifit=False, all_posts=False,
         today=False, platform="hive"):
    # Select the blockchain based on the platform
    node_url = "https://api.hive.blog" if platform == "hive" else "https://api.steemit.com"

    # Connect to the Hive or Steemit blockchain
    hive = Hive(node=node_url)
    account = Account(author, blockchain_instance=hive)

    # Yesterday's and today's dates
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    today_date = datetime.now(timezone.utc).date()

    posts = fetch_posts(account, last, all_posts, today, today_date, yesterday)

    # Process each post
    for post in posts:
        if post["author"] != author:
            continue

        # Check if the 'actifit' tag is in the post
        if 'actifit' in post.get('json_metadata', {}).get('tags', []):
            if not include_actifit:
                print(f"Post skipped due to 'actifit' tag: {post['title']}")
                continue

        # Conditions for --last, --all, --today, and yesterday's posts
        if not all_posts and not last:
            post_date = post["created"].date()
            target_date = today_date if today else yesterday
            if post_date != target_date:
                continue

        save_post(post, path, author, platform)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("author", help="Account name on Hive or Steemit")
    parser.add_argument("path", help="Path where the Markdown files will be saved")
    parser.add_argument("--last", action="store_true", help="Get only the last post")
    parser.add_argument("--actifit", action="store_true",
                         help="Include posts with the 'actifit' tag")
    parser.add_argument("--all", action="store_true",
                         help="Get all posts, ignoring the date filter")
    parser.add_argument("--today", action="store_true", help="Get only today's posts")
    parser.add_argument("--steemit", action="store_true",
                         help="Use the Steemit network instead of Hive")

    args = parser.parse_args()

    # Define the platform (Hive or Steemit)
    selected_platform = "steemit" if args.steemit else "hive"

    main(args.author, args.path, args.last, args.actifit, args.all, args.today, selected_platform)
