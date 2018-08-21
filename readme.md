# MiBlog

A light dynamic blog server powered by [bottle](http://bottlepy.org/docs/dev/), [sqlite](https://www.sqlite.org/) and [mistune](https://pypi.org/project/mistune/), written in python.

## Features

- Render markdown to HTML 
- Build directories automatically
- Easy to post, update, delete articles
- Comment support (and quote)
- All in python (web-framework, database and markdown renender).
- Python3 only!! (which sqlite is buildin)

## Dependence

Depend on the following python modules

- bottle (framework)
- bottle_sqlite (sqlite database plugin)
- mistune (markdown renderer)

These three module files have been copied to project dirctory.

## Usage

1. Prepare your documents  
   Organise your markdown file and images in categories, and put them in  `/docs` folder. It should like this:
   
    ```
    |---docs 
    |     |---category_1
    |     |      |---passage_1
    |     |      |      |------passage_name.md
    |     |      |      |------image1
    |     |      |      |------image2
    |     |      |      |        .
    |     |      |      |        .
    |     |      |      |        .
    |     |      |      
    |     |      |---passage_2
    |     |      |      .
    |     |      |      .
    |     |      |      .
    |     |
    |     |---category_2
    |     |      .
    |     |      .
    |     |      .
    ```

    `category_n` will be the category name  
    `passage_name` will be the passage title(underline will be replaced by whitespace)  

2. Initialization  
   In project directory, run

   ```
   python gentool.py init
   ```

   This will create several table in database, render md file and save the result in database, relink and rename the image, then put them in the `/static` folder.

3. Run the server

    ```
    python server.py
    ```


To add, delete or modify, just change the categories and files in `/docs` folder and run one of the following command:

- `./gentool.py update_category` 
- `./gentool.py update_article`
- `./gentool.py update_all`

Any of this command will update the database according to the content in `/docs` folder. But won't delete anything in database that has been deleted in  `/docs` folder. However, you can specify arguement `delete=True` to delete them. 

## Use at your own risk!
