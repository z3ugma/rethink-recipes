rethink-recipes
===============================
A lightweight, quick and no-frills recipe application.
It calculates a color palette dynamically based on the title of the recipe, and includes image search results matching the title
Ingredients are automatically highlighted in the directions as well.

Tornado webserver wrapping Flask application with a RethinkDB backend

1. Install Vagrant (www.vagrantup.com)
2. Clone this repository. Navigate to its directory
3. Run 'vagrant up'
4. Navigate to http://localhost:5025 in your browser to view the tornado app
5. Navigate to http://localhost:8025 to interact with RethinkDB web admin interface

Dependencies
------------
 - flask
 - rethinkdb
 - Python Image Library
 - colorific (for color palette generation)
 - translitcodec (for generating slugs)
 - flask-wtf
 - tornado (for deployment)

![Screenshot1](https://raw.githubusercontent.com/z3ugma/rethink-recipes/master/screenshot1.png)
![Screenshot2](https://raw.githubusercontent.com/z3ugma/rethink-recipes/master/screenshot2.png)
![Screenshot3](https://raw.githubusercontent.com/z3ugma/rethink-recipes/master/screenshot3.png)
![Screenshot4](https://raw.githubusercontent.com/z3ugma/rethink-recipes/master/screenshot4.png)


