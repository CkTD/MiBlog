import os
base = os.path.join(os.environ['HOME'], "MicroBlog")

db_path = os.path.join(base, 'site.db')
docs_dir = os.path.join(base, 'docs')
static_dir = os.path.join(base, 'static')
images_dir = os.path.join(static_dir, 'images')
views_dir = os.path.join(base, 'views')
