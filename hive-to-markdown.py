#!/usr/bin/python
# -*- coding: utf-8 -*-

from beem import Hive
from beem.account import Account
import os
import io
import argparse
import requests
import uuid
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta

def download_image(image_url, path):
    try:
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
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
        else:
            print(f"Error downloading the image: {image_url} (Status Code: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error processing the image {image_url}: {e}")
        return None

def extract_images_from_markdown(markdown_content):
    # Search for images in the format ![alt](image_url)
    image_urls = re.findall(r'!\[.*?\]\((.*?)\)', markdown_content)
    return image_urls

def main(author, path, last=False, include_actifit=False, all_posts=False, today=False, platform="hive"):
    # Select the blockchain based on the platform
    if platform == "hive":
        node_url = "https://api.hive.blog"
    else:  # steemit
        node_url = "https://api.steemit.com"

    # Connect to the Hive or Steemit blockchain
    hive = Hive(node=node_url)
    account = Account(author, blockchain_instance=hive)
    
    # Yesterday's and today's dates
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    today_date = datetime.utcnow().date()

    # Get the account's posts
    posts = account.get_blog(limit=500)  # Adjust the limit as needed
    
    if last:
        # Get only the last post
        posts = [posts[0]] if posts else []
    
    # Process each post
    for post in posts:
        if post["author"] != author:
            continue
        
        # Check if the 'actifit' tag is in the post
        if 'actifit' in post.get('json_metadata', {}).get('tags', []):
            if not include_actifit:
                print(f"Post skipped due to 'actifit' tag: {post['title']}")
                continue
        
        # Use the 'created' field directly as datetime
        post_date = post["created"].date()
        
        # Conditions for --all, --today, and yesterday's posts
        if not all_posts:
            if today:
                if post_date != today_date:
                    continue
            else:
                if post_date != yesterday:
                    continue
        
        markdown_content = post['body']
        title = post['title']
        permlink = post['permlink']
        link_for_post = f'https://{platform}.blog/@{author}/{permlink}'
        
        # Download images and replace the links in markdown
        images = post.get('json_metadata', {}).get('image', [])
        
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
        
        post_final = f'---\n<br />**Originally posted on {platform.capitalize()} network: [{link_for_post}]({link_for_post})** <br />\n----'
        yaml_prefix = '---\n'
        TitleYaml = title.replace(':', '').replace('\'', '').replace('#', '').replace('(', '').replace(')', '')

        # Get the post tags and categories
        tags = post.get('json_metadata', {}).get('tags', [])
        tags_str = "\n".join([f"  - {tag}" for tag in tags])

        # Set the category as the first tag or "General" if there are no tags
        category = tags[0] if tags else "General"
        if platform == 'hive':
            category_str = f'  - {category.capitalize()}\n  - Hive\n'
        else:
            category_str = f'  - {category.capitalize()}\n  - Steemit\n'

        # Build the YAML prefix
        yaml_prefix += f'title: {TitleYaml}\n'
        yaml_prefix += f'date: {post["created"]}\n'
        yaml_prefix += f'permlink: /{platform}/{permlink}\n'
        yaml_prefix += 'type: posts\n'
        yaml_prefix += f'categories:\n{category_str}\n'
        yaml_prefix += f'tags:\n{tags_str}\n'
        yaml_prefix += f'author: {author}\n---\n'
        
        # Filename
        filename = os.path.join(path, f"{post_date}_{permlink}.md")
       
        # Save the content to a Markdown file
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(yaml_prefix + markdown_content + post_final)
        
        print(f"Post saved: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("author", help="Account name on Hive or Steemit")
    parser.add_argument("path", help="Path where the Markdown files will be saved")
    parser.add_argument("--last", action="store_true", help="Get only the last post")
    parser.add_argument("--actifit", action="store_true", help="Include posts with the 'actifit' tag")
    parser.add_argument("--all", action="store_true", help="Get all posts, ignoring the date filter")
    parser.add_argument("--today", action="store_true", help="Get only today's posts")
    parser.add_argument("--steemit", action="store_true", help="Use the Steemit network instead of Hive")
    
    args = parser.parse_args()
    
    # Define the platform (Hive or Steemit)
    platform = "steemit" if args.steemit else "hive"
    
    main(args.author, args.path, args.last, args.actifit, args.all, args.today, platform)
