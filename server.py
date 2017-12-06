from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from tinydb import TinyDB, Query
from pprint import pprint
import json

db = TinyDB('db.json')
users = db.table('users') #this is users table
restaurants = db.table('restaurants')
dishes = db.table('dishes')

currentUsername = ""

app = Flask(__name__)
CORS(app)
app.debug = True

'''
DB functions

'''
# users functionality
def setCurrentUserName(uname):
    global currentUsername
    currentUsername = uname

def getCurrentUserName():
    return currentUsername

def addUser(uname, pwd, email):
    users.insert({'username' : uname, 'password' : pwd, "email" : email})

def signIn(uname, pwd):
    User_query = Query()
    found_user = users.search(User_query.username == uname)[0]
    if found_user['password'] == pwd:
        print("Correct login!")
        return True
    else:
        print("Incorrect login!")
        return False

def returnAllUsers():
    return users.all()

# dishes functionality
def addDish(dish_name, dish_price, dish_pic, dish_ingredients):
    dishID = dishes.insert({'dish_name': dish_name, 'dish_price': dish_price, 'dish_pic':dish_pic, 'dish_ingredients': dish_ingredients})
    return dishID

def deleteDish(d_name):
    Dish_query = Query()
    dishes.remove(Dish_query.dish_name == d_name)

def editDish(d_name, d_price, d_ingredients):
    Dish_query = Query()
    dishes.update({'dish_price': d_price, 'dish_ingredients': d_ingredients}, Dish_query.dish_name == d_name)

def returnAllDishes():
    return dishes.all()

# restaurants functionality
def makeRestaurant(uname):
    restaurants.insert({'username': uname, 'menu' : []})

def editRestaurant(uname, owner_name, loc, cuisine_types, restaurant_img, r_name):
    # TODO menu or dishes as parameter as well
    Restaurant_query = Query()
    restaurants.update({'owner_name': owner_name, 'location': loc, 'cuisine_types': cuisine_types, 'restaurant_image': restaurant_img, 'restaurant_name': r_name}, Restaurant_query.username == uname)

def returnAllRestaurants():
    return restaurants.all()

def findChefs(cuisine_type, loc):
    Restaurant_query = Query()
    if cuisine_type == "Anything" and loc == "Anywhere":
        return returnAllRestaurants()
    elif cuisine_type == "Anything":
        return restaurants.search(Restaurant_query.location == loc)
    elif loc == "Anywhere":
        return restaurants.search(Restaurant_query.cuisine_types.any([cuisine_type]))
    else:
        return restaurants.search((Restaurant_query.location == loc) & (Restaurant_query.cuisine_types.any([cuisine_type])))

# called inside route_addDish()
def addDishToRestaurant(dishID, uname):
    Restaurant_query = Query()
    found_restaurant = restaurants.search(Restaurant_query.username == uname)[0]
    # print(found_restaurant)
    appended_menu = found_restaurant['menu']
    appended_menu.append(dishID)
    restaurants.update({'menu': appended_menu}, Restaurant_query.username == uname)


def returnRestaurantDishes(uname):
    Restaurant_query = Query()
    found_restaurant = restaurants.search(Restaurant_query.username == uname)[0]
    restaurant_menu = found_restaurant['menu']
    print(restaurant_menu)
    dishes_list = []
    for dish_number in restaurant_menu:
        dish = dishes.get(doc_id=dish_number)
        dishes_list.append(dish)
    return dishes_list

def fetchRestaurantProfile(uname):
    Restaurant_query = Query()
    found_restaurant = restaurants.search(Restaurant_query.username == uname)[0]
    dishes_list = returnRestaurantDishes(uname)
    found_restaurant['dishes'] = dishes_list
    return found_restaurant


'''
Actual Endpoints
'''

'''
expects an input of the form -
{ "current_user": "John" }
used to store which seller was clicked
on the home page from the results obtained
upon clicking the 'Find Chefs' button
'''
@app.route('/api/setCurrentUser', methods=['POST'])
def route_setCurrentUser():
    body = request.get_json(force=True)
    print(body)
    currentUser = body['current_user']
    setCurrentUserName(currentUser)
    return "Current user set!"


@app.route('/api/getCurrentUser', methods=['GET'])
def route_getCurrentUser():
    json_result = json.dumps({'result': getCurrentUserName()})
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp



'''
expects an input of the form -
{
	"cuisine_type": "Italian",
	"location": "Anywhere"
}
'''
@app.route('/api/findChefs', methods=['POST'])
def route_findChefs():
    body = request.get_json(force=True)
    print(body)
    cuisine_type = body['cuisine_type']
    location = body['location']
    # return jsonify({'result': findChefs(cuisine_type, location)})
    json_result = json.dumps({'result': findChefs(cuisine_type, location)})
    print(json_result)
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
    # return "Found chefs!"


'''
expects an input of the form -
{
	"dish_name": "Macaroons",
	"dish_price": 9.80,
	"dish_ingredients": ["Sweet paste", "Cake dough"],
	"dish_pic": "../pics/macaroon.jpeg",
	"username": "Gohan"
}
supply the username to which a dish is being added
'''
@app.route('/api/addDish', methods=['POST'])
def route_addDish():
    body = request.get_json(force=True)
    d_name = body['dish_name']
    d_price = body['dish_price']
    d_pic = body['dish_pic']
    d_ingredients = body['dish_ingredients']
    uname = body['username']

    dishID = addDish(d_name, d_price, d_pic, d_ingredients)
    print(dishID)
    addDishToRestaurant(dishID, uname)
    return "Successfully added dish"



'''
expects an input of the form -
{
	"dish_name": "Idli",
	"dish_price": 4.15,
	"dish_ingredients": ["Basmati Rice", "Ghee"]
}
supply the name of the dish(which doesn't change)
and reassign values to price and ingredients
'''
@app.route('/api/editDish', methods=['POST'])
def route_editDish():
    body = request.get_json(force=True)
    d_name = body['dish_name']
    d_price = body['dish_price']
    d_ingredients = body['dish_ingredients']

    editDish(d_name, d_price, d_ingredients)
    return "Successfully edited dish"



'''
expects an input of the form -
{
	"dish_name": "Dosa"
}
'''
@app.route('/api/deleteDish', methods=['POST'])
def route_deleteDish():
    body = request.get_json(force=True)
    d_name = body['dish_name']

    deleteDish(d_name)
    return "Successfully deleted dish"



'''
expects an input of the form -
{
	"username": "Grey",
	"password": "46trafsdfsdbf",
	"email": "grey@fairytail.com"
}
'''
@app.route('/api/addUser', methods=['POST'])
def route_addUser():
    body = request.get_json(force=True)
    # the request object here is the request that this
    # endpoint recieves (something that someone sent to this)
    print(body)
    uname = body['username']
    pwd = body['password']
    email = body['email']

    addUser(uname, pwd, email)
    makeRestaurant(uname)
    return "Successfully added user"



'''
expects an input of the form -
{
	"username": "Natsu",
	"owner_name": "Natsu, Fire Dragon Slayer",
	"location": "Iceland",
	"cuisine_types": ["Chinese", "African", "Mexican", "Japanese"],
	"restaurant_image": "natsu_restaurant.jpeg",
	"restaurant_name": "Fire Ball"
}
supply the username whose restaurant details you
want to change and give new values for the fields
'''
@app.route('/api/editRestaurant', methods=['POST'])
def route_editRestaurant():
    body = request.get_json(force=True)
    uname = body['username']
    owner_name = body['owner_name']
    loc = body['location']
    cuisine_types = body['cuisine_types']
    r_img = body['restaurant_image']
    r_name = body['restaurant_name']

    editRestaurant(uname, owner_name, loc, cuisine_types, r_img, r_name)
    return "Successfully edited restaurant"



'''
expects an input of the form -
{
	"username": "Kuroko"
}
supply the username to get that user's
restaurant's dishes
'''
@app.route('/api/getRestaurantDishes', methods=['POST'])
def route_getRestaurantDishes():
    body = request.get_json(force=True)
    uname = body['username']
    dishes_list = returnRestaurantDishes(uname)
    # return jsonify({'result': dishes_list})
    json_result = json.dumps({'result': dishes_list})
    print(json_result)
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
    # return "Got dishes!"



'''
expects an input of the form -
{
	"username": "Natsu",
	"password": "fire_dragon"
}
supply username and password and this will
return true/false if details are right/wrong
'''
@app.route('/api/signIn', methods=['POST'])
def route_signIn():
    body = request.get_json(force=True)
    uname = body['username']
    pwd = body['password']
    # return jsonify({'result': signIn(uname, pwd)})
    json_result = json.dumps({'result': signIn(uname, pwd)})
    print(json_result)
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp



'''
expects an input of the form -
{
	"username": "Gohan"
}
supply the username to get all the
details of the restaurant
'''
@app.route('/api/fetchRestaurantProfile', methods=['POST'])
def route_fetchProfile():
    body = request.get_json(force=True)
    uname = body['username']
    # return jsonify({'result': fetchRestaurantProfile(uname)})
    json_result = json.dumps({'result': fetchRestaurantProfile(uname)})
    print(json_result)
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp



'''
Test Endpoints
'''

@app.route('/test/returnHello', methods=['GET'])
def test_returnHello():
    resp = Response("Hello")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/test/returnAllUsers', methods=['GET'])
def test_returnAllUsers():
    json_result = json.dumps({'result': returnAllUsers()})
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/test/returnAllDishes', methods=['GET'])
def test_returnAllDishes():
    # return jsonify({'result': returnAllDishes()})
    json_result = json.dumps({'result': returnAllDishes()})
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/test/returnAllRestaurants', methods=['GET'])
def test_returnAllRestaurants():
    # return jsonify({'result': returnAllRestaurants()})
    json_result = json.dumps({'result': returnAllRestaurants()})
    resp = Response(response=json_result, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == "__main__":
    app.run(debug=True)


