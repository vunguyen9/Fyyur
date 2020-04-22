#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from models import Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://vunguyen@localhost:5432/project1'

migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  now = datetime.now()
  dat=[]
  cities = Venue.query.with_entities(Venue.city, Venue.state, db.func.count(Venue.city)).group_by(Venue.city, Venue.state).all()
  for c in cities:
    venues = Venue.query.filter(Venue.city==c.city and Venue.state==c.state).all()
    v = []
    for venue in venues:
      num_upcoming_shows = 0
      for show in venue.shows:
        if show.start_time > now:
          num_upcoming_shows += 1
      v.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': num_upcoming_shows
      })
      
    dat.append({
      'city': c.city,
      'state': c.state,
      'venues': v
    })

  return render_template('pages/venues.html', areas=dat)
  

@app.route('/venues/search', methods=['POST'])
def search_venues():
  now = datetime.now()
  response={}
  venue_search = Venue.query.filter(Venue.name.ilike('%'+request.form['search_term']+'%')).all()
  response['count'] = len(venue_search)
  response['data'] = []

  for venue in venue_search:
    num_upcoming_shows = 0
    for show in venue.shows:
      if show.start_time > now:
        num_upcoming_shows += 1

    response['data'].append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    })
    
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue_query = Venue.query.get(venue_id)
  now = datetime.now()

  upcoming_shows_query = Show.query.options(db.joinedload(Show.venue, innerjoin=True)).filter(Show.venue_id == venue_id).filter(Show.start_time > now).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
      'artist_id': show.artist_id,
      'artist_name': Artist.query.get(show.artist_id).name,
      'artist_image_link': Artist.query.get(show.artist_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  past_shows_query = Show.query.options(db.joinedload(Show.venue, innerjoin=True)).filter(Show.venue_id == venue_id).filter(Show.start_time <= now).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      'artist_id': show.artist_id,
      'artist_name': Artist.query.get(show.artist_id).name,
      'artist_image_link': Artist.query.get(show.artist_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  venue = {}
  if venue_query is not None:
    venue['id'] = venue_query.id
    venue['name'] = venue_query.name
    venue['genres'] = venue_query.genres
    venue['address'] = venue_query.address
    venue['city'] = venue_query.city
    venue['state'] = venue_query.state
    venue['phone'] = venue_query.phone
    venue['website'] = venue_query.website
    venue['facebook_link'] = venue_query.facebook_link
    venue['seeking_talent'] = venue_query.seeking_talent
    venue['seeking_description'] = venue_query.description
    venue['image_link'] = venue_query.image_link
    venue['past_shows'] = past_shows
    venue['upcoming_shows'] = upcoming_shows
    venue['past_shows_count'] = len(past_shows)
    venue['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try: 
    seeking_talent = False
    description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
    if 'description' in request.form:
      description = request.form['description']
    new_venue = Venue(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      description=description,
      seeking_talent= seeking_talent,
      website=request.form['website'],
      genres=request.form.getlist('genres'),
    )
    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash(e)
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  result = []
  artists = Artist.query.order_by('name').all()
  for artist in artists:
    result.append({
      'id': artist.id,
      'name': artist.name
    })
  return render_template('pages/artists.html', artists=result)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  now = datetime.now()
  artist_search = Artist.query.filter(Artist.name.ilike('%'+request.form['search_term']+'%')).all()
  response = {}
  response['count'] = len(artist_search)
  response['data'] = []
  for artist in artist_search:
    num_upcoming_shows = 0
    for show in artist.shows:
      if show.start_time > now:
        num_upcoming_shows += 1
    response['data'].append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': num_upcoming_shows
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artist_query = Artist.query.get(artist_id)
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  upcoming_shows_query = Show.query.options(db.joinedload(Show.artist, innerjoin=True)).filter(Show.artist_id == artist_id).filter(Show.start_time > now).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
      'venue_id': show.venue_id,
      'venue_name': Venue.query.get(show.venue_id).name,
      'venue_image_link': Venue.query.get(show.venue_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  past_shows_query = Show.query.options(db.joinedload(Show.artist, innerjoin=True)).filter(Show.artist_id == artist_id).filter(Show.start_time <= now).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      'venue_id': show.venue_id,
      'venue_name': Venue.query.get(show.venue_id).name,
      'venue_image_link': Venue.query.get(show.venue_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  artist = {}
  if artist_query is not None:
    artist['id'] = artist_query.id
    artist['name'] = artist_query.name
    artist['genres'] = artist_query.genres
    artist['city'] = artist_query.city
    artist['state'] = artist_query.state
    artist['phone'] = artist_query.phone
    artist['website'] = artist_query.website
    artist['facebook_link'] = artist_query.facebook_link
    artist['seeking_venue'] = artist_query.seeking_venue
    artist['seeking_description'] = artist_query.seeking_description
    artist['image_link'] = artist_query.image_link
    artist['past_shows'] = past_shows
    artist['upcoming_shows'] = upcoming_shows
    artist['past_shows_count'] = len(past_shows)
    artist['upcoming_shows_count'] = len(upcoming_shows)
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist_query = Artist.query.get(artist_id)
  artist = {
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": artist_query.genres,
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link
  }

  form.name.data = artist['name']
  form.city.data = artist['city']
  form.state.data = artist['state']
  form.phone.data = artist['phone']
  form.genres.data = artist['genres']
  form.facebook_link.data = artist['facebook_link']
  form.image_link.data = artist['image_link']
  form.website.data = artist['website']
  form.seeking_venue.data = artist['seeking_venue']
  form.description.data = artist['seeking_description']

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)

  if artist:
    try:
      seeking_venue = False
      description = ''
      if 'seeking_venue' in request.form:
        seeking_venue = request.form['seeking_venue'] == 'y'
      if 'description' in request.form:
        description = request.form['description']
      
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form['genres']
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.website = request.form['website']
      artist.seeking_venue = seeking_venue
      artist.seeking_description = description
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_query = Venue.query.get(venue_id)

  venue = {
    'id': venue_query.id,
    'name': venue_query.name,
    'genres': venue_query.genres,
    'address': venue_query.address,
    'city': venue_query.city,
    'state': venue_query.state,
    'phone': venue_query.phone,
    'website': venue_query.website,
    'facebook_link': venue_query.facebook_link,
    'seeking_talent': venue_query.seeking_talent,
    'description': venue_query.description,
    'image_link': venue_query.image_link
  }

  form.name.data = venue['name']
  form.city.data = venue['city']
  form.state.data = venue['state']
  form.address.data = venue['address']
  form.phone.data = venue['phone']
  form.genres.data = venue['genres']
  form.facebook_link.data = venue['facebook_link']
  form.image_link.data = venue['image_link']
  form.website.data = venue['website']
  form.seeking_talent.data = venue['seeking_talent']
  form.description.data = venue['description']

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)

  if venue:
    try:
      seeking_talent = False
      description = ''
      if 'seeking_talent' in request.form:
        seeking_talent = request.form['seeking_talent'] == 'y'
      if 'description' in request.form:
        description = request.form['description']

      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form['genres']
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.website = request.form['website']
      venue.seeking_talent = seeking_talent
      venue.description = description
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  try:
    seeking_venue = False
    description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    if 'description' in request.form:
      description = request.form['description']
    
    new_artist = Artist(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      genres=request.form['genres'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      website=request.form['website'],
      seeking_venue=seeking_venue,
      seeking_description=description
    )
    db.session.add(new_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash(e)
  finally:
    db.session.close()
    flash('An error occurred. Artist could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = Show.query.all()

  data = []
  for show in shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    venue_id=request.form['venue_id']
    artist_id=request.form['artist_id']
    start_time=request.form['start_time']

    venue = Venue.query.filter_by(id=venue_id)[0]
    artist = Artist.query.filter_by(id=artist_id)[0]
    show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)

    show.venue = venue
    show.artist = artist

    db.session.add(venue)
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash(e)
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
