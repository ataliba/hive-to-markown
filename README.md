# hive-to-markdown

This script automates the process of retrieving blog posts from Hive or Steemit blockchain accounts, downloading associated images, and saving the posts as Markdown files with YAML front-matter. It is particularly useful for archiving or republishing content from Hive or Steemit.

## Features

- Fetches posts from a Hive or Steemit account.
- Filters posts by date: yesterday (default), today, all, or just the last one.
- Downloads all images referenced in a post (both `json_metadata` and inline Markdown) and rewrites the links to local filenames.
- Skips posts tagged `actifit` by default.
- Writes each post as a `.md` file with YAML front-matter (title, date, permlink, categories, tags, author) and a footer linking back to the original post.

## Requirements

- Python 3
- Dependencies listed in `requirements.txt` (`beem`, `requests`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python hive-to-markdown.py <author> <output_path> [options]
```

### Arguments

| Argument | Description |
|---|---|
| `author` | Account name on Hive or Steemit |
| `path` | Path where the Markdown files will be saved |

### Options

| Option | Description |
|---|---|
| `--last` | Get only the last post |
| `--actifit` | Include posts with the `actifit` tag (excluded by default) |
| `--all` | Get all posts, ignoring the date filter |
| `--today` | Get only today's posts |
| `--steemit` | Use the Steemit network instead of Hive |

### Examples

```bash
# Yesterday's posts (default) from a Hive account
python hive-to-markdown.py alice ./posts

# Only the last post
python hive-to-markdown.py alice ./posts --last

# All posts, ignoring the date filter
python hive-to-markdown.py alice ./posts --all

# Today's posts on Steemit
python hive-to-markdown.py alice ./posts --today --steemit
```

## Docker

```bash
docker build -t hive-to-markdown .
docker run -v $(pwd)/output:/output hive-to-markdown alice /output --all
```

## Output

Each post is saved as `<path>/<date>_<permlink>.md`, e.g. `./posts/2026-07-26_my-post-permlink.md`, with front-matter like:

```yaml
---
title: My Post
date: 2026-07-26 12:00:00
permlink: /hive/my-post-permlink
type: posts
categories:
  - Photography
  - Hive
tags:
  - photography
  - hive
author: alice
---
```

Downloaded images are saved alongside the Markdown files with a unique filename and referenced from the post content.
