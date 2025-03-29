import flask
import random
import string
import os
from flexidb import get_database
from flask import g

app = flask.Flask(__name__)

# Function to generate random short URL IDs
def generate_id(length=6):
    """Generate a random string of fixed length"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Get database connection - create new connection per request
def get_db():
    """
    Get the database connection.

    The database connection is stored in the g object for the current request.
    If the database connection does not exist (i.e. the first time this function
    is called), a new connection is created and stored in the g object.

    The database connection is automatically closed when the request ends.

    Uses MongoDB for data storage.
    """
    if 'db' not in g:
        # Read MongoDB URI from environment variable or use default
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
        mongo_db = os.environ.get('MONGO_DB', 'urlsnake')
        
        # Connect to MongoDB
        g.db = get_database("mongodb", uri=mongo_uri, database=mongo_db)
        g.db.connect()
        
        # Create index on iurl field for faster lookups and uniqueness
        try:
            # Ensure index exists for iurl (unique constraint)
            g.db.conn[mongo_db].urls.create_index('iurl', unique=True)
        except Exception as e:
            app.logger.warning(f"Index creation warning: {e}")
    return g.db
# Close database connection when request ends
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.disconnect()
@app.route("/")
def home():
    return flask.redirect("/index")

@app.route("/<Iurl>")
def redirect_url(Iurl):
    db = get_db()
    db_urls = db.select("urls", {"iurl": Iurl})
    if db_urls:
        return flask.redirect(db_urls[0]["url"])
    else:
        return flask.redirect("/index?error=Invalid URL")

@app.route("/index", methods=["GET", "POST"])
def index():
    if flask.request.method == "POST":
        url = flask.request.form["url"]
        custom_id = flask.request.form.get("custom_id", "").strip()
        db = get_db()
        
        # If user provided a custom ID, use it
        if custom_id:
            # Check if it's valid (alphanumeric + dashes only)
            import re
            if not re.match(r'^[a-zA-Z0-9-]+$', custom_id):
                return flask.render_template("index.html", 
                                           error="Custom ID can only contain letters, numbers, and dashes.")
            
            # Check if this custom ID already exists
            existing = db.select("urls", {"iurl": custom_id})
            if existing:
                return flask.render_template("index.html", 
                                           error=f"The custom ID '{custom_id}' is already taken. Please choose another.")
            
            iurl = custom_id
        else:
            # Generate a random ID if no custom ID provided
            iurl = generate_id(6)
            
            # Check if this random ID already exists
            existing = db.select("urls", {"iurl": iurl})
            while existing:
                # Generate a new one if it exists
                iurl = generate_id(6)
                existing = db.select("urls", {"iurl": iurl})
        
        # Insert the new URL
        db.create("urls", {"iurl": iurl, "url": url})
        
        # Generate the full short URL for display
        short_url = flask.request.host_url + iurl
        
        # Show success message with the new URL
        return flask.render_template("index.html", short_url=short_url)
    else:   
        return flask.render_template("index.html", error=flask.request.args.get("error"))

if __name__ == "__main__":
    # Initialize the DB once at startup to ensure connection
    with app.app_context():
        db = get_db()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Run the app
    app.run(host=host, port=port, threaded=True)