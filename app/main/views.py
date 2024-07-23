# app/main/views.py
from app import mongo, limiter, flask_uuid
from flask import jsonify, request, abort
from flask import current_app as app
from app.main import bp
from app.assertions import assert_valid_schema
from app.decorators import require_access_level
from app.services import get_s3_urls
from jsonschema.exceptions import ValidationError as JsonValidationError
from pymongo import ASCENDING, DESCENDING
import uuid
import datetime
import re
from bson.binary import Binary, UuidRepresentation

# --------------------------------------------------------------------------- #

# reject any non-json requests
@bp.before_request
def only_json():
    if not request.is_json:
        abort(400)

# --------------------------------------------------------------------------- #

@bp.route('/items', methods=['POST'])
@require_access_level(10, request)
def create_item(public_id, request):
   
    #TODO: items can have many fields - hence the choice of a nosql datastore
    # need to lock this down a bit more - at the mo we only insist on item_id
    # and description
    # check input is valid json
    try:
        data = request.get_json()
    except:
        return jsonify({ 'message': 'Check ya inputs mate. Yer not valid, Jason'}), 400

    # validate input against json schemas
    try:
        assert_valid_schema(data, 'item')
    except JsonValidationError as err:
        return jsonify({ 'message': 'Check ya inputs mate.', 'error': err.message }), 400    

    # we put every thing in a single collection of items and will index on _id and public_id
    item_id = str(uuid.uuid4())
    data['public_id'] = public_id
    data['created'] = datetime.datetime.utcnow()
    data['modified'] = datetime.datetime.utcnow()
    result = mongo.db.items.insert_one({"_id" : item_id, "details": data})
    #app.logger.info(result)

    token = request.headers.get('x-access-token')

    # need to generate a list of foto ids 
    # that we can pass to aws microservice
    foto_ids = [] 
    for i in range(int(app.config['FOTO_LIMIT'])):
        foto_ids.append(str(uuid.uuid4()))

    r = get_s3_urls(foto_ids, token)
    s3_urls = []
    collection_name = 'z'+public_id.replace('-','')
    bucket_url = "https://"+collection_name.lower()+".s3.amazonaws.com/"

    if r.status_code == 201:
        aws_data = r.json()
        s3_urls = aws_data.get('aws_urls')

    return jsonify({ 'item_id': item_id,
                     'bucket_url': bucket_url,
                     's3_urls': s3_urls }), 201

# --------------------------------------------------------------------------- #

@bp.route('/items/bulk/fetch', methods=['POST'])
def fetch_items():

    try:
        data = request.get_json()
    except:
        return jsonify({ 'message': 'Check ya inputs mate. Yer not valid, Jason'}), 400

    # validate input against json schemas
    try:
        assert_valid_schema(data,'bulk_items')
    except JsonValidationError as err:
        return jsonify({ 'message': 'Check ya inputs mate.', 'error': err.message }), 400

    try:
        results = mongo.db.items.find({ '_id': { '$in': data['item_ids'] }});
    except Exception as e:
        app.logger.warning("Error fetching doc [%s]", str(e))
        return jsonify({ 'message': 'something went bang, sorry' }), 500

    output = []

    for item in results:
        item['item_id'] = str(item['_id'])
        del item['_id']
        details = item['details']
        del item['details'] 
        item.update(details)
        output.append(item)

    return jsonify({ 'items': output }), 200

# --------------------------------------------------------------------------- #

@bp.route('/items/<uuid:item_id>', methods=['GET'])
#@require_access_level(10, request)
#def get_item(public_id, request, item_id):
def get_item(item_id):

    # every user has their own collection
    item_id = str(item_id)

    record = _return_document(item_id)

    if isinstance(record, dict):
        return jsonify(record), 200

    mess = {'message': 'Could not find the item ['+item_id+']'}

    return jsonify(mess), 404

# --------------------------------------------------------------------------- #

@bp.route('/items', methods=['GET'])
@require_access_level(10, request)
def get_items_by_user(public_id, request):

    offset, sort = 0, 'id_asc'
    limit = int(app.config['PAGE_LIMIT'])

    try:
        if 'offset' in request.args:
            offset = int(request.args['offset'])
        if 'limit' in request.args:
            limit = int(request.args['limit'])
        if 'sort' in request.args:
            sort = request.args['sort']
    except Exception as e:
        app.logger.error("Error: [%s]", e)
        return jsonify({'message': 'Problem with your args'}), 400

    starting_id = None
    results_count = 0
    try:
        starting_id = mongo.db.items.find({ 'details.public_id': public_id }).sort('_id', ASCENDING)
        results_count = mongo.db.items.count_documents({ 'details.public_id': public_id })
    except Exception as e:
        app.logger.error("Error: [%s]", e)
        return jsonify({ 'message': 'There\'s a problem with your arguments or the db or both or something else ;)'}), 400

    if results_count == 0:
        return jsonify({ 'message': 'Nowt ere chap'}), 404

    if results_count <= offset:
        return jsonify({ 'message': 'offset is too big'}), 400

    if offset < 0:
        return jsonify({ 'message': 'offset is negative'}), 400

    last_id = starting_id[offset]['_id']

    items = []
    items_count = 0
    try:
        items = mongo.db.items.find({'$and': [{'_id': { '$gte': last_id}},
                                              {'details.public_id': public_id}]}).sort('_id', ASCENDING).limit(limit)
    except Exception as e:
        app.logger.error("Error [%s]", e)
        return jsonify({ 'message': 'There\'s a problem with your arguments or planets are misaligned. try sacrificing a goat or something...'}), 400

    output = []

    for item in items:
        item['item_id'] = str(item['_id'])
        del item['_id']
        details = item['details']
        del item['details']
        item.update(details)
        output.append(item)
        items_count = items_count + 1

    url_offset_next = offset+limit
    url_offset_prev = offset-limit
    if url_offset_prev < 0:
         url_offset_prev = 0

    if url_offset_next > items_count:
        next_url = None    

    return_data = {'items': output}

    if url_offset_next < results_count:
        next_url = '/items?limit='+str(limit)+'&offset='+str(url_offset_next)+'&sort='+sort
        return_data['next_url'] = next_url

    if offset > 0:
        prev_url = '/items?limit='+str(limit)+'&offset='+str(url_offset_prev)+'&sort='+sort
        return_data['prev_url'] = prev_url

    return jsonify(return_data), 200

#-----------------------------------------------------------------------------#
# brings back a random selection of 20 items by category
@bp.route('/items/cat/<category>', methods=['GET'])
def get_items_by_category(category):

    # basic data sanitation checks for category in format like 'cars:2000'
    if not re.search("^[a-z0-9_-]{1,20}:[0-9]{2,5}$",category):
        return jsonify({'message': 'Invalid category'}), 400
    items = []

    try:
        results = mongo.db.items.aggregate([{ "$match": { "details.category": category } },
                                          { "$sample": { "size": 20 } }])
    except Exception as e:
        app.logger.info(e)
        return jsonify({'message': 'There\'s a problem with your arguments or mongo or both or something else ;)'}), 400

    items = list(results)

    if len(items) == 0:
        return jsonify({'message': 'Nowt in that category lass'}), 404

    output = []
    for item in items:
        item['item_id'] = str(item['_id'])
        del item['_id']
        details = item['details']
        del item['details']
        item.update(details)
        output.append(item)

    return_data = { 'items': output }

    return jsonify(return_data), 200

# -----------------------------------------------------------------------------

@bp.route('/items/<uuid:item_id>', methods=['PUT'])
@require_access_level(10, request)
def edit_item(public_id, request, item_id):

    try:
        data = request.get_json()
    except:
        return jsonify({ 'message': 'Check ya inputs mate. Yer not valid, Jason'}), 400

    # validate input against json schemas
    try:
        assert_valid_schema(data,'item')
    except JsonValidationError as err:
        return jsonify({'message': 'Check ya inputs mate.', 'error': err.message}), 400

    #TODO: pull original data to get create date. all other data will be 'wiped' 
    orig_rec = _return_document(str(item_id))

    if not isinstance(orig_rec, dict):
        return jsonify({'message': 'Item not found'}), 404

    data['created'] = orig_rec['created']
    explicit_binary_public_id = Binary.from_uuid(uuid.UUID(public_id), UuidRepresentation.STANDARD)
    data['public_id'] = explicit_binary_public_id
    data['modified'] = datetime.datetime.utcnow()

    try:
        mongo.db.items.update_one({'_id': item_id},
                                  {'$set': {"details": data}},
                                  upsert=False)
    except Exception as e:
        app.logger.error("Error editing item [%s]", e)
        return jsonify({'message': 'Unable to save item to db'}), 500

    return jsonify(data), 200

# --------------------------------------------------------------------------- #

@bp.route('/items/<uuid:item_id>', methods=['DELETE'])
@require_access_level(10, request)
def delete_item(public_id, request, item_id):

    app.logger.info(public_id)
    app.logger.info(item_id)
    item_id = str(item_id)

    #result = mongo.db[public_id].find_one({ '_id': item_id })
    #app.logger.info(result)
    del_result = mongo.db.items.delete_one({'$and': [{'_id': item_id}, 
                                                     {'public_id': public_id}]})

    app.logger.info(del_result.deleted_count)

    return jsonify({}), 204

# --------------------------------------------------------------------------- #
# system routes
# --------------------------------------------------------------------------- #

@bp.route('/items/status', methods=['GET'])
def system_running():
    return jsonify({ 'message': 'System running...' }), 200

# --------------------------------------------------------------------------- #
# debug and helper functions
# --------------------------------------------------------------------------- #

def _return_document(item_id):

    record = None
    try:
        record = mongo.db.items.find_one({ '_id': item_id })
    except Exception as e:
        app.logger.warning("Error fetching doc [%s]", str(e))
        return False 

    if record is None:
        return False 
    
    del record['_id']
    item_details = record.get("details")
    item_details['item_id'] = item_id
    return(item_details)

# --------------------------------------------------------------------------- #

