import sys,os,string
from flask import Flask
from flask import render_template, request, flash, redirect, url_for, session
from flask import render_template_string, abort
from pymongo import MongoClient
from decimal import Decimal
from bson.objectid import ObjectId
import json
import datetime
import stripe

stripe.api_key = "sk_test_cKUI2o3y9JtYZ6hxN98PyYIL006PAQy9Rt"

app = Flask(__name__)
app.config["SECRET_KEY"] = "Yixiao_Li_yil210"

conn = MongoClient('127.0.0.1', 27017)
db = conn.book_shop
user_set = db.user
book_set = db.book
cart_set = db.cart
order_set = db.order

@app.route('/', methods=['GET', 'POST'])
def home():
    # check user name in session
    login_name = "log in"
    login = False
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']

    qty = session.get('quantity')
    if qty == None:
        session['quantity'] = 0
        qty = 0
    # search
    if request.method == 'POST':
        notgenre = True
 
        search_item = request.form.get('search_item')
        result = do_search(search_item)
        
        bookChunk = []
        chunkSize = 4
        i = 0
        while i < len(result):
            bookChunk.append(list(result[i:i + chunkSize]))
            i = i + chunkSize

        return render_template('book_search.html',login_name = login_name, search_item = search_item, bookChunk=bookChunk, login=login,qty=qty,notgenre=notgenre)

    # GET method
    elif request.method == 'GET':
        books = list(book_set.find())
        
        bookChunk = []
        chunkSize = 4
        i = 0
        while i < len(books):
            bookChunk.append(list(books[i:i + chunkSize]))
            i = i + chunkSize

        return render_template('index.html',login_name = login_name, bookChunk=bookChunk, login=login, qty=qty)


@app.route('/genre/<string:genre>', methods=['GET', 'POST'])
def genre(genre):
    login_name = "log in"
    login = False
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']

    if request.method == 'GET':
        notgenre = False        
        find_items = []
        # find by category
        search_item = genre
        find_genre = list(book_set.find({"genre":search_item}))
        if find_genre != None:
            i = 0
            while (i < len(find_genre)):
                find_items.append(find_genre[i])
                i = i + 1
            result = list(find_items)
            bookChunk = []
            chunkSize = 4
            i = 0
            while i < len(result):
                bookChunk.append(list(result[i:i + chunkSize]))
                i = i + chunkSize
        return render_template('book_search.html',login=login,login_name = login_name, search_item = search_item, bookChunk=bookChunk, notgenre=notgenre)
    # search on genre page
    elif request.method == 'POST':
        notgenre = True
        search_item = request.form.get('search_item')
        result = do_search(search_item)
        
        bookChunk = []
        chunkSize = 4
        i = 0
        while i < len(result):
            bookChunk.append(list(result[i:i + chunkSize]))
            i = i + chunkSize
        return render_template('book_search.html',login=login,login_name = login_name, search_item = search_item, bookChunk=bookChunk, notgenre=notgenre)
    



@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def do_signup():
    user = request.form.get('user')
    email = request.form.get('email')
    pwd = request.form.get("password")

    if user_set.find_one({"email": email}) != None:
        # print("email exists")
        #flask flash alert
        flash('e-mail exists!', 'error')
        return render_template('signup.html')
    
    flash(u'Sign up success! Now log in.', 'success')    
    mydoc = { "name": user, "email": email, "password": pwd}
    user_set.insert_one(mydoc)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    email = request.form.get('email')
    pwd = request.form.get("password")
    session['email'] = email
    session['passwd'] = pwd
    mydoc = user_set.find_one({"email": email}, {"password": pwd})
    if mydoc != None:
        session['user_name'] = str(mydoc['name'])
        session['user_id'] = str(mydoc['_id'])
        items = cart_set.find_one({"user_id": session.get('user_id')})
        qty = 0
        if items != None:
            cart_info = items['bookid_num']
            for item in cart_info:
                qty += item['quantity']
        
        session['quantity'] = qty
        login_name = str(mydoc['name'])
        flash(u'Welcome! '+ login_name, 'success')
        return redirect(url_for('home'))

    flash('The email and password do not match!', 'error')
    return render_template('login.html')
    

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('user_name', None)
    session.pop('user_id', None)
    session.pop('quantity', None)
    # session.clear()
    return redirect(url_for('home'))

@app.route('/add_to_cart/<string:id>', methods=['GET', 'POST'])
def add_to_cart(id):
    book_id = id
    # check log in status to load cart page
    if session == None or session.get('user_id') == None:
        #flask flash alert
        flash(u'Please log in to add books to your cart!', 'error')
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    curr_qty = 0

    qty = session.get('quantity')
    if qty == None:
        qty = 0
    qty += 1
    curr_qty += 1
    session['quantity'] = qty
    curr_user = session.get('user_id')
    if session and curr_user != None:
        mydoc = cart_set.find_one({"user_id": user_id})
        book_info = book_set.find_one({"_id": ObjectId(id)})

        # curr_item = cart_set.find_one({"user_id": user_id, "bookid_num.book_id": book_id})

        # print(type(curr_item))
        # print(curr_item)
        # curr_arr = curr_item['bookid_num']
        # curr_qty = 0
        # if len(curr_arr) > 0:
        #     curr_qty = curr_item['bookid_num'][0]['quantity']

        if (book_info != None):
            title = book_info['title']
            author = book_info['author']
            price = book_info['price']
            image_path = book_info['imagePath']
            stock = book_info['stock']

            # if stock < curr_qty:
            #     qty -= 1
            #     session['quantity'] = qty
            #     flash('out of stock', 'error')
            #     return redirect(url_for('home'))

        if mydoc != None:
            # current user cart data exists in cart_set, check whether current book id exists, update quantity or add an element to bookid_num array
            cart_set.update({"user_id": curr_user, "bookid_num.book_id": id}, {"$inc":{"bookid_num.$.quantity": 1} }) 
            cart_set.update({"user_id": curr_user, "bookid_num.book_id": {'$ne': id}}, {"$addToSet":{"bookid_num" :{'book_id':id ,'title':title,'author':author,'price':price,'imagePath':image_path, 'quantity': 1}} })
        else:
            cart_set.insert_one({"user_id": curr_user, "bookid_num": [{'book_id': id,'title':title,'author':author,'price':price,'imagePath':image_path, 'quantity': 1}]}) 
            
    return redirect(url_for('home'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    # check log in status to load cart page
    if session == None or session.get('user_id') == None:
        # print("please log in to view cart")
        #flask flash alert
        flash(u'Please log in to view your cart!', 'error')
        return redirect(url_for('home'))

    login = True
    login_name = session['user_name']
    user_id = session.get('user_id')

    ones_cart = cart_set.find_one({"user_id": user_id})
    if ones_cart == None:
        flash(u'Your cart is empty now.', 'error')
        return redirect(url_for('home'))

    elif ones_cart != None:
        items = list(ones_cart['bookid_num'])

        session['items'] = items

        i = 0
        sub_total = 0
        while i < len(items):
            # print(items[i]['price'])
            sub_total += items[i]['price'] * items[i]['quantity']
            i = i + 1
        sub_total = round(sub_total, 2)
        tax = round(sub_total * 0.07, 2)
        total = round(sub_total + tax, 2)

        session['total'] = total

    if request.method == 'GET':
        # print('cart get')
        qty = session.get('quantity')
        return render_template('cart.html', qty=qty,login=login,login_name = login_name,items = items, sub_total = sub_total, tax = tax, total = total)

    elif request.method == 'POST':
        # print('cart post')
        curr_time = datetime.datetime.now()
        qty = session.get('quantity')
        while i < len(items):
            # print(items[i]['price'])
            if items[i]['stock'] < items[i]['quantity']:
                flash(u'Sorry, '+items[i]['title']+u' is currently understock, please check again', 'error')
                return redirect(url_for('cart'))
            i = i + 1      

        return redirect(url_for('to_checkout'))



@app.route('/view_details/<string:id>', methods=['GET', 'POST'])
def view_details(id):
    # top right info 
    login_name = "log in"
    login = False
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']
    
    book_id = id
    book_info = book_set.find_one({"_id": ObjectId(id)})
    # print('book info ', book_info)
    title = book_info['title']
    author = book_info['author']
    genre = book_info['genre']
    price = book_info['price']
    stock = book_info['stock']
    image_path = book_info['imagePath']
    description = book_info['description']

    qty = session.get('quantity')


    availability = "In Stock"
    if stock <= 0:
        availability = "Coming Back Soon"
    elif stock > 0 and stock <= 3:
        availability = "Low in Stock"
    

    return render_template('book_details.html',qty=qty,login_name=login_name,login=login,book_id =book_id,title=title,author=author,genre=genre,price=price,availability=availability,image_path=image_path,description=description)
            

@app.route('/add_from_detail', methods=['GET', 'POST'])
def add_from_detail():
    # check quantity input and place alert
    # print(request.form.get('quantity_input'))
    # print(type(request.form.get('quantity_input')))
    if request.form.get('quantity_input')==None or request.form.get('quantity_input')=="":
        flash(u'Please input valid quantity to add to cart!', 'error')
        return redirect(url_for('home'))

    quantity_to_add = int(request.form.get('quantity_input'))
    if quantity_to_add < 1:
         flash(u'Please input valid quantity to add to cart!', 'error')
         return redirect(url_for('home'))

    # print(type(quantity_to_add))
    book_id = request.form.get('book_id')
    # print(type(book_id))
    
    if session == None or session.get('user_id') == None:
        # print("please log in to view cart")
        #flask flash alert
        flash(u'Please log in to add book to your cart!', 'error')
        return redirect(url_for('home'))

    qty = session.get('quantity')
    if qty == None:
        qty = 0
    qty += quantity_to_add
    session['quantity'] = qty

    
    curr_user = session.get('user_id')

    if session and curr_user != None:
        mydoc = cart_set.find_one({"user_id": session.get('user_id')})
        book_info = book_set.find_one({"_id": ObjectId(book_id)})

        if (book_info != None):
            title = book_info['title']
            author = book_info['author']
            price = book_info['price']
            image_path = book_info['imagePath']
            stock = book_info['stock']

            if stock < quantity_to_add:
                qty -= quantity_to_add
                session['quantity'] = qty
                flash('Sorry, the item you just added is under stock.', 'error')
                return redirect(url_for('home'))

        if mydoc != None:
            # current user cart data exists in cart_set, check whether current book id exists, update quantity or add an element to bookid_num array
            cart_set.update({"user_id": curr_user, "bookid_num.book_id": book_id}, {"$inc":{"bookid_num.$.quantity": quantity_to_add} }) 
            cart_set.update({"user_id": curr_user, "bookid_num.book_id": {'$ne': book_id}}, {"$addToSet":{"bookid_num" :{'book_id':book_id ,'title':title,'author':author,'price':price,'imagePath':image_path, 'quantity': quantity_to_add}} })
        else:
            cart_set.insert_one({"user_id": curr_user, "bookid_num": [{'book_id': book_id,'title':title,'author':author,'price':price,'imagePath':image_path, 'quantity': quantity_to_add}]}) 
            
    return redirect(url_for('home'))
     


@app.route('/remove_from_cart/<string:id>', methods=['GET', 'POST'])
def remove_from_cart(id):
    qty = session.get('quantity')
    items = cart_set.find_one({"user_id": session.get('user_id'), "bookid_num.book_id":id})
    
    items = items["bookid_num"]
    for item in items:
        if id == item['book_id']:
            qty -= item['quantity']

    session['quantity'] = qty


    cart_set.update({"user_id": session.get('user_id'), "bookid_num.book_id":id},{"$pull":{"bookid_num" :{'book_id':id }} })
    return redirect(url_for('cart'))


@app.route('/to_checkout', methods=['GET', 'POST'])
def to_checkout():
    login_name = "log in"
    login = False
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']

    if request.method == 'GET':
        total = session.get('total')
        #return render_template('checkout.html', total=total * 100)
        return render_template('checkout.html', login=login, login_name=login_name)

    elif request.method == 'POST':
        user_id = session.get('user_id')
        time = datetime.datetime.now()

        items = session.get('items')
        total = session.get('total')

        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        mobile = request.form.get('mobile')

        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        pcode = request.form.get('pcode')

        # if fname or lname or email or mobile or address or city or state or pcode:
        #     flash('Please check the input form', 'error')
        #     return redirect(url_for('to_checkout'))

        try:

            token = request.form.get('stripeToken')

            customer = stripe.Customer.create(
                email=request.form.get('stripeEmail'),
                source=request.form.get('stripeToken')
            )

            charge = stripe.Charge.create(
                customer=customer.id,
                amount=round(total * 100),
                currency='usd',
                description='Flask Charge',
            )
            pass
        except stripe.error.InvalidRequestError as e:
            return redirect(url_for('to_checkout'))
        

        session['quantity'] = 0

        # update book_set stock according to user's order
        i = 0
        while i < len(items):
            book_id = items[i]['book_id']
            quantity_to_minus = items[i]['quantity']
            curr = book_set.find_one({"_id": ObjectId(book_id)})
            curr_stock = curr['stock']
            book_set.update({"_id": ObjectId(book_id)}, {'$set': {'stock': curr_stock - quantity_to_minus} }) 
            i = i + 1


        # insert to order set
        order_set.insert_one({"user_id":user_id,"order_time":time, "total":total, "items_info":items,"personal_info":[{'first_name':fname,'last_name':lname,'email':email,'mobile':mobile}],"shipping_info":[{'address':address,'city':city,'state':state,'pcode':pcode}]})     
        # clear user's cart, remove current user in cart set
        cart_set.remove({"user_id": user_id})

        return redirect(url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']
    qty = session.get('quantity')
    if qty == None:
        session['quantity'] = 0
        qty = 0

    if request.method == 'GET':
        user_name = session['user_name']
        user_id = session['user_id']
        email = session['email']
        passwd = session['passwd']

        orders = list(order_set.find({"user_id": user_id}))
        print(orders)
        
        if orders == None:
            orders = []
            
        return render_template('profile.html',login=login,login_name=login_name,qty=qty,user_name=user_name, email=email, passwd=str(passwd), orders=orders)

    elif request.method == 'POST':
        user_id = session['user_id']
        new_passwd = request.form.get('passwd')
        user_set.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": new_passwd}})
        flash('Password changed', 'success')

        return redirect(url_for('profile'))


@app.route('/order_details/<string:id>', methods=['GET'])
def order_details(id): 
    if session != None:
        if 'user_name' in session:
            login = True
            login_name = session['user_name']
    qty = session.get('quantity')
    if qty == None:
        session['quantity'] = 0
        qty = 0

    order_id = ObjectId(id)

    order = order_set.find_one({"_id": order_id})

    items = list(order['items_info'])
    person_info = order['personal_info'][0]
    last_name = person_info['last_name']
    first_name = person_info['first_name']
    email = person_info['email']
    mobile = person_info['mobile']

    shipping = order['shipping_info'][0]
    address = shipping['address']
    city = shipping['city']
    state = shipping['state']
    pcode = shipping['pcode']

    total = order['total']
    time = order['order_time']

    return render_template('order_details.html',qty=qty,login=login,login_name=login_name,items=items, person_info=person_info, last_name=last_name, first_name=first_name, email=email, mobile=mobile, address=address, city=city, state=state, pcode=pcode, total=total, time=time)


def do_search(search_item):
    find_items = []     
    # find by title
    find_title = list(book_set.find({"title":{"$regex": search_item}}))
    if find_title != None:
        i = 0
        while (i < len(find_title)):
            find_items.append(find_title[i])
            i = i + 1
    # find by author
    find_author = list(book_set.find({"author":{"$regex": search_item}}))
    if find_author != None:
        i = 0
        while (i < len(find_author)):
            find_items.append(find_author[i])
            i = i + 1
    # find by description
    find_description = list(book_set.find({"description":{"$regex": search_item}}))
    if find_description != None:
        i = 0
        while (i < len(find_description)):
            find_items.append(find_description[i])
            i = i + 1
    
    # find by category
    find_genre = list(book_set.find({"genre":{"$regex": search_item}}))
    if find_genre != None:
        i = 0
        while (i < len(find_genre)):
            find_items.append(find_genre[i])
            i = i + 1
    
    # remove duplicates, get result list of unique dictionaries
    print(find_items)
    result = list({v['_id']:v for v in find_items}.values())
    return result


if __name__ == '__main__':
    app.run(port = 8888)
