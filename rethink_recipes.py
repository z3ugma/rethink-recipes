from collections import namedtuple
from math import sqrt
import random
try:
    import Image
except ImportError:
    from PIL import Image
import json
import colorsys
import colorific
import urllib2
import urllib, cStringIO
import re
import translitcodec



def get_gimages(query):
    answer = []
    for i in range(0,8,4):
        url = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&start=%d&imgsz=large&imgtype=photo' % (query,i)
        r = urllib2.urlopen(url)
        for k in json.loads(r.read())['responseData']['results']:
             answer.append(k['tbUrl'])
    return answer

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

## Slug functions ##

_punct_re = re.compile(r'[\t !"#$%&\()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = word.replace('\'', '') #Don't replace apostrophes with a dash, just strip them
        word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))

def gettitle(recipe):
    return recipe['title']

from flask.ext.wtf import Form
from wtforms.fields import TextField
from wtforms.validators import Required
from wtforms.fields import StringField
from wtforms.fields import BooleanField
from wtforms.widgets import TextArea

class RecipeForm(Form):
    title = TextField('title', validators = [Required()])
    ingredients = StringField(u'Ingredients', widget=TextArea(),validators = [Required()])
    directions = StringField(u'directions', widget=TextArea(), validators = [Required()])

class DeleteForm(Form):
    deleterecipe = BooleanField('deleterecipe')



from flask import *
app = Flask(__name__)
app.secret_key = 'correcthorsebatterystaples'

# rethink imports
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

# rethink config
RDB_HOST =  'localhost'
RDB_PORT = 28015
TODO_DB = 'recipes'

# db setup; only run once
def dbSetup():
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    try:
        r.db_create(TODO_DB).run(connection)
        r.db(TODO_DB).table_create('recipes').run(connection)
        print 'Database setup completed'
    except RqlRuntimeError:
        print 'Database already exists.'
    finally:
        connection.close()
dbSetup()

# open connection before each request
@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=TODO_DB)
    except RqlDriverError:
        abort(503, "Database connection could be established.")

# close the connection after each request
@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


@app.route('/')
def index():
    allrecipes = list(r.table('recipes').run(g.rdb_conn))
    allrecipes.sort(key=gettitle)
    return render_template("index.html", allrecipes=allrecipes)

@app.route('/favicon.ico')
def favicon():
    abort(404)

@app.route('/add', methods = ['GET', 'POST'])
def add():
    form = RecipeForm()
    #form.ingredients.data = "1c ingredient\nenter ingredients here  "

    if request.method == 'POST' and form.validate():

        lightness = []
        rainbow = []
        resp=[]
        urls = get_gimages("+".join(form.title.data.split()))
        for url in urls:
            i = cStringIO.StringIO(urllib.urlopen(url).read())
            quiche = colorific.extract_colors(i, max_colors=5)
            resp.extend([each.value for each in quiche.colors])
        resp = [(m,sqrt(0.299 * m[0]**2 + 0.587 * m[1]**2 + 0.114 * m[2]**2)) for m in resp]
        lightness = sorted(resp,key=lambda x: x[1])
        lightness = [i[0] for i in lightness]
        lightness.sort(key=lambda tup: colorsys.rgb_to_hsv(tup[0],tup[1],tup[2])[2])
        for each in chunks(lightness,10):
            avg = tuple(map(lambda y: sum(y) / len(y), zip(*each)))
            rainbow.append(avg)

        slug = slugify(form.title.data)

        recipe = { 'title': form.title.data.title(), 'ingredients': [{'amount': " ".join(ingredient.split()[0:2]), 'what': " ".join(ingredient.split()[2:])} for ingredient in form.ingredients.data.split('\r\n')], 'directions': form.directions.data.split('\r\n'), 'urls': urls, 'slug': slug, 'avgcolors': [list(i) for i in rainbow]}


       
        recipe['ingredients'] = [i for i in recipe['ingredients'] if not i['what']=='']
        recipe['directions'] = [i for i in recipe['directions'] if not i=='']

        r.table('recipes').insert(recipe).run(g.rdb_conn)

        return redirect(url_for('recipe', query=slug))

    
         #r.table('recipes').get('de670bed-791d-41d0-97cb-1ceaf9ba54ac').update({'time_updated': r.now(), 'slug': "broccoli-cheese-soup", 'urls': urls, 'avgcolors': [list(i) for i in rainbow]}).run(g.rdb_conn)

    return render_template("add.html", form=form)


@app.route('/<query>')
def recipe(query):
    recipe = list(r.table('recipes').filter({'slug': query}).run(g.rdb_conn))

    if recipe:
        recipe = recipe[0]
    else:
        abort(404)

    steps = []
    for i in recipe['directions']:
        for j in [k['what'].split(",")[0] for k in recipe['ingredients']]:
            i = i.replace(j, ("<kbd>" + j + "</kbd>"))
        steps.append(Markup(i))

    rainbow = [tuple(l) for l in recipe['avgcolors']]

    return render_template("recipes.html", urls = recipe['urls'], avg=rainbow, ingredients = recipe['ingredients'], steps = steps, title=recipe['title'], query=query)


@app.route('/<query>/edit', methods = ['GET', 'POST'])
def edit(query):


    form = RecipeForm()
    recipe = list(r.table('recipes').filter({'slug': query}).run(g.rdb_conn))

    if recipe:
        recipe = recipe[0]
    else:
        abort(404)

    if request.method == 'GET':

        form.ingredients.data = "\r\n".join([(i['amount'] + " " + i['what']) for i in recipe['ingredients']])
        form.directions.data = "\r\n".join(i for i in recipe['directions'])
        form.title.data = recipe['title']

        return render_template("edit.html", form=form, recipe=recipe)

    if request.method == 'POST' and form.validate():

        lightness = []
        rainbow = []
        resp=[]
        urls = get_gimages("+".join(form.title.data.split()))
        for url in urls:
            i = cStringIO.StringIO(urllib.urlopen(url).read())
            quiche = colorific.extract_colors(i, max_colors=5)
            resp.extend([each.value for each in quiche.colors])
        resp = [(m,sqrt(0.299 * m[0]**2 + 0.587 * m[1]**2 + 0.114 * m[2]**2)) for m in resp]
        lightness = sorted(resp,key=lambda x: x[1])
        lightness = [i[0] for i in lightness]
        lightness.sort(key=lambda tup: colorsys.rgb_to_hsv(tup[0],tup[1],tup[2])[2])
        for each in chunks(lightness,10):
            avg = tuple(map(lambda y: sum(y) / len(y), zip(*each)))
            rainbow.append(avg)

        slug = slugify(form.title.data)

        id = recipe['id']

        recipe = { 'title': form.title.data.title(), 'ingredients': [{'amount': " ".join(ingredient.split()[0:2]), 'what': " ".join(ingredient.split()[2:])} for ingredient in form.ingredients.data.split('\r\n')], 'directions': form.directions.data.split('\r\n'), 'urls': urls, 'slug': slug, 'avgcolors': [list(i) for i in rainbow]}

        recipe['ingredients'] = [i for i in recipe['ingredients'] if not i['what']=='']
        recipe['directions'] = [i for i in recipe['directions'] if not i=='']

        r.table('recipes').get(id).update(recipe).run(g.rdb_conn)

        return redirect(url_for('recipe', query=slug))

@app.route('/<query>/delete', methods = ['GET', 'POST'])
def delete(query):
    form = DeleteForm()
    recipe = list(r.table('recipes').filter({'slug': query}).run(g.rdb_conn))
    if recipe:
        recipe = recipe[0]
    else:
        abort(404)

    if request.method == 'GET':

        return render_template("delete.html", query=query, recipe=recipe, form=form)

    if request.method == 'POST':
        if 'deleterecipe' in request.form:

            id = recipe['id']

            r.table('recipes').get(id).delete().run(g.rdb_conn)
            return redirect(url_for('index'))
        else:
            flash("Are you sure? Check the box")
            return render_template("delete.html", query=query, recipe=recipe, form=form)


if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')
