#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import shutil
import hashlib
import sqlite3

from functools import wraps

from config import db_path, docs_dir, static_dir, images_dir

import mistune


class myRenderer(mistune.Renderer):
    def image(self, src, title, text):
        """Rendering a image with title and text.

        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """

        doc_src = self.options['image_handler'](src)[1:]

        src = mistune.escape_link(doc_src)
        text = mistune.escape(text, quote=True)
        if title:
            title = mistune.escape(title, quote=True)
            html = '<img src="%s" alt="%s" title="%s"' % (
                src, text, title)
        else:
            html = '<img src="%s" alt="%s"' % (src, text)
        if self.options.get('use_xhtml'):
            return '%s />' % html
        return '%s>' % html


def get_subdirs(parent_dir):
    sub_dirs = os.listdir(parent_dir)
    for sub_dir in sub_dirs:
        if not os.path.isdir(os.path.join(parent_dir, sub_dir)):
            sub_dirs.remove(sub_dir)
    return sub_dirs


def gen_filename(pathname):
    with open(pathname, 'rb') as f:
        m = hashlib.md5()
        m.update(f.read())
    name = m.hexdigest()
    ext = os.path.splitext(pathname)[-1]
    if ext:
        name = name + ext
    return name


def optional_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        new = False
        if 'cur' not in kwargs or not kwargs['cur']:
            conn = sqlite3.connect(db_path)
            kwargs['cur'] = conn.cursor()
            new = True
        res = func(*args, **kwargs)

        if new:
            conn.commit()
            conn.close()
        return res
    return wrapper


def create_db():
    if os.path.isfile(db_path):
        print("Site already exist.")
        exit()
    print("Create database.")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE category(
            id              INTEGER PRIMARY KEY,
            name            TEXT,
            articles_count  INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE article(
            id            INTEGER PRIMARY KEY,
            title         TEXT,
            html          TEXT,
            publish_time  INT,
            modify_time   INT,
            category_id   INTEGER,
            FOREIGN KEY(category_id) REFERENCES category(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE images(
            id          INTEGER PRIMARY KEY,
            file_name   TEXT,
            article_id  INTEGER,
            FOREIGN KEY(article_id) REFERENCES article(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE comment(
            id         INTEGER PRIMARY KEY,
            time       INTEGER,
            name       TEXT,
            ip         TEXT,
            email      TEXT,
            comment    TEXT,
            quote_id   INTEGER,
            article_id INTEGER,
            FOREIGN KEY(quote_id) REFERENCES comment(id),
            FOREIGN KEY(article_id) REFERENCES article(id)
        )
    ''')
    conn.commit()
    conn.close()


@optional_db
def add_category(name, cur):
    cur.execute('INSERT INTO category VALUES(NULL,?,0)',
                (name,))


@optional_db
def delete_category(id, cur):
    articles = cur.execute(
        'SELECT * FROM article WHERE category_id=?',
        (id,)).fetchall()
    for article in articles:
        print('Delete Article: %s' % article[1])
        delete_article(article[0], cur=cur)

    cur.execute('DELETE FROM category WHERE id=?',
                (id,))


def gen_image_handler(article_dir, res):
    def image_handler(src):

        docs_image_path = os.path.join(article_dir, src)
        if not os.path.isfile(docs_image_path):
            print("\t!!! missing images !!! %s" %docs_image_path)
            return ""
        new_image_name = gen_filename(docs_image_path)
        static_image_path = os.path.join(images_dir, new_image_name)

        print('\tAdd New image %s' % new_image_name)
        res[new_image_name] = (static_image_path, open(
            docs_image_path, 'rb').read())
        #shutil.copyfile(docs_image_path, static_image_path)

        # ccur.execute('INSERT INTO images VALUES(NULL,?,?)',
        #             (new_image_name, article_id))
        return static_image_path
    return image_handler


def find_files(dir, ext):
    l = []
    for f in os.listdir(dir):
        tnm, text = os.path.splitext(f)
        file_path = os.path.join(dir, f)
        if os.path.isfile(file_path) and text == '.'+ext:
            l.append(file_path)
    return l


def get_title_by_file(filename):
    return ' '.join(filename.split('_'))


def get_article_text_img(md_path, article_dir):
    images = {}
    with open(md_path, 'r', encoding='UTF-8') as md:
        myrenderer = myRenderer(
            image_handler=gen_image_handler(article_dir, images))
        markdown = mistune.Markdown(renderer=myrenderer)
        html = markdown(md.read())
    return html, images


@optional_db
def add_article(article_dir, category_id, cur):
    try:
        md_path = find_files(article_dir, 'md')[0]
    except IndexError:
        print('Pass empty article directory: %s' % article_dir)
        return

    print('\tAdd md file: %s' % md_path)
    os.utime(md_path, None)
    time = int(os.path.getmtime(md_path))
    title = get_title_by_file(os.path.split(article_dir)[1])
    html, images = get_article_text_img(md_path, article_dir)

    cur.execute('INSERT INTO article VALUES(NULL,?,?,?,?,?)',
                (title, html, time, time, category_id))
    article_id = cur.lastrowid
    for name in images:
        path, data = images[name]
        cur.execute('INSERT INTO images VALUES(NULL,?,?)',
                    (name, article_id))
        open(path, 'wb').write(data)
    cur.execute(
        'UPDATE category SET articles_count = articles_count + 1 WHERE id=?', (category_id,))

    return article_id


@optional_db
def modify_article(article_dir, article_id, mtime, cur):
    try:
        md_path = find_files(article_dir, 'md')[0]
    except IndexError:
        print('Pass empty article directory: %s' % article_dir)
        return

    cur.execute('DELETE FROM images WHERE article_id=?', (article_id,))

    html, images = get_article_text_img(md_path, article_dir)
    for name in images:
        path, data = images[name]
        cur.execute('INSERT INTO images VALUES(NULL,?,?)',
                    (name, article_id))
        open(path, 'wb').write(data)

    cur.execute('UPDATE article SET html=? WHERE id=?', (html, article_id))
    cur.execute('UPDATE article SET modify_time=? WHERE id=?',
                (mtime, article_id))


@optional_db
def delete_comment(id, cur):
    try:
        cur.execute('DELETE FROM comment WHERE id=?', (int(id),))
    except Exception as e:
        print("Error:", e)
        return False
    else:
        return True


@optional_db
def delete_article(id, cur):
    cur.execute('SELECT file_name FROM images WHERE article_id=?', (id,))
    for image in cur.fetchall():
        print('\tDelete image: %s' % image)
        try:
            os.unlink(os.path.join(images_dir, image[0]))
        except FileNotFoundError:
            print("\tNot exist!")

    category_id = cur.execute(
        'SELECT category_id FROM article WHERE id=?', (id,)).fetchone()[0]
    cur.execute('DELETE FROM images WHERE article_id=?', (id,))
    cur.execute('DELETE FROM comment WHERE article_id=?', (id,))
    cur.execute('DELETE FROM article WHERE id=?', (id,))

    cur.execute(
        'UPDATE category SET articles_count = articles_count - 1 WHERE id=?', (category_id,))


@optional_db
def update_category(delete=False, cur=None):
    if delete == "delete":
        delete = True
    else:
        delete = False

    db_category_records = cur.execute('SELECT * FROM category').fetchall()
    db_categories = [rec[1] for rec in db_category_records]

    docs_categories = get_subdirs(docs_dir)

    for docs_category in docs_categories:
        if docs_category not in db_categories:
            print('Add new category: %s' % docs_category)
            add_category(docs_category, cur=cur)

    if delete:
        for db_category_record in db_category_records:
            if not db_category_record[1] in docs_categories:
                print('Delete category: %s' % db_category_record[1])
                delete_category(db_category_record[0], cur=cur)

@optional_db
def update_article(delete=False, cur=None):
    if delete == "delete":
        delete = True
    else:
        delete = False

    docs_categories = get_subdirs(docs_dir)
    for docs_category in docs_categories:
        docs_category_path = os.path.join(docs_dir, docs_category)
        docs_articles = get_subdirs(docs_category_path)
        docs_article_titles = [get_title_by_file(i) for i in docs_articles]
        db_category_id = cur.execute('SELECT id FROM category WHERE name=?',
                                     (docs_category,)).fetchone()[0]
        db_article_records = cur.execute(
            'SELECT * FROM article WHERE category_id=?',
            (db_category_id,)).fetchall()
        db_articles = [item[1] for item in db_article_records]

        for docs_article in docs_articles:
            article_path = os.path.join(docs_category_path, docs_article)

            if get_title_by_file(docs_article) not in db_articles:
                # print("ADD")
                print('Find new article: %s' % article_path)
                add_article(article_path, db_category_id, cur=cur)
            else:
                the_db_article_record = [
                    i for i in db_article_records if i[1] == get_title_by_file(docs_article)][0]
                the_db_article_mtime = the_db_article_record[4]
                the_docs_article_mtime = int(
                    os.path.getmtime(find_files(article_path, "md")[0]))
                if the_db_article_mtime != the_docs_article_mtime:
                    # print("MODIFY"")
                    print("Update article: %s" % article_path)
                    modify_article(os.path.join(docs_category_path,
                                                docs_article), the_db_article_record[0], the_docs_article_mtime, cur=cur)

        # print("DEL")
        if delete:
            for db_article_record in db_article_records:
                if db_article_record[1] not in docs_article_titles:
                    print('Delete article: %s' %
                          "\t" + os.path.join(docs_category_path,
                                              db_article_record[1]))
                    delete_article(db_article_record[0], cur=cur)

def update_all(delete=False):
    update_category(delete)
    update_article(delete)


def init():
    create_db()
    update_all()

def clean():
    if not input("Are you sure? (y/n)") == 'y':
        return
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        print("%s not exist" %db_path)
    imgs = os.listdir(images_dir)
    for img in imgs:
        if os.path.isfile(os.path.join(images_dir,img)):
            os.unlink(os.path.join(images_dir,img))

    


if __name__ == '__main__':
    try:
        globals()[sys.argv[1]](*sys.argv[2:])
    except KeyError:
        print("python gentool.py init|clean|update_category|update_article|update_all [delete]")
