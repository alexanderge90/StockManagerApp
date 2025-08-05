from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import io
import csv

app = Flask(__name__)
DATABASE = 'DRS25.db'
app.secret_key = 'your_secret_key_here' # You need to set a secret key for flash messages

# Define the list of categories here
CATEGORIES = ['All', 'Food', 'Soda', 'Liquor', 'Wine', 'Beer']

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the inventory table with a new 'category' column."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Create the database table when the app starts
create_table()

@app.route('/')
def index():
    """Main page: Displays the current inventory."""
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return render_template('index.html', items=items, categories=CATEGORIES, current_category='All')

@app.route('/category/<string:category_name>')
def category_view(category_name):
    """Displays inventory filtered by category."""
    conn = get_db_connection()
    if category_name == 'All':
        items = conn.execute('SELECT * FROM items').fetchall()
    else:
        items = conn.execute('SELECT * FROM items WHERE category = ?', (category_name,)).fetchall()
    conn.close()
    return render_template('index.html', items=items, categories=CATEGORIES, current_category=category_name)

@app.route('/add_item', methods=['POST'])
def add_item():
    """Adds a new item to the inventory."""
    name = request.form['name']
    quantity = request.form['quantity']
    unit = request.form['unit']
    category = request.form['category']
    location = request.form['location']
    conn = get_db_connection()
    conn.execute('INSERT INTO items (name, quantity, unit, category,location) VALUES (?, ?, ?, ?, ?)', (name, quantity, unit, category, location))
    conn.commit()
    conn.close()
    flash(f"Item '{name}' added successfully.", 'success')
    return redirect(url_for('index'))

@app.route('/edit_item/<int:item_id>')
def edit_item(item_id):
    """Displays a form to edit an item."""
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    return render_template('edit.html', item=item, categories=CATEGORIES)

@app.route('/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    """Updates an existing item in the inventory."""
    name = request.form['name']
    quantity = request.form['quantity']
    unit = request.form['unit']
    category = request.form['category']
    location = request.form['location']
    conn = get_db_connection()
    conn.execute('UPDATE items SET name = ?, quantity = ?, unit = ?, category = ?, location = ? WHERE id = ?', (name, quantity, unit, category, location, item_id))
    conn.commit()
    conn.close()
    flash(f"Item '{name}' updated successfully.", 'success')
    return redirect(url_for('index'))

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    """Deletes an item from the inventory."""
    conn = get_db_connection()
    item = conn.execute('SELECT name FROM items WHERE id = ?', (item_id,)).fetchone()
    if item:
        item_name = item['name']
        conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
        flash(f"Item '{item_name}' deleted successfully.", 'success')
    conn.close()
    return redirect(url_for('index'))

@app.route('/visualize_data')
def visualize_data():
    """Generates a CSV string and renders a page to visualize it."""
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()

    # csv_buffer = io.StringIO()
    # writer = csv.writer(csv_buffer)
    # writer.writerow(['ID', 'Name', 'Quantity', 'Unit', 'Category'])
    # for item in items:
    #     writer.writerow([item['id'], item['name'], item['quantity'], item['unit'], item['category']])

    # csv_data = csv_buffer.getvalue()
    
    return render_template('visualize.html', items=items)

@app.route('/download_csv')
def download_csv():
    """Generates a CSV file for download."""
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['ID', 'Name', 'Quantity', 'Unit', 'Category', 'Location'])
    for item in items:
        writer.writerow([item['id'], item['name'], item['quantity'], item['unit'], item['category'], item['location']])
    
    csv_buffer.seek(0)
    
    return send_file(io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='inventory_report.csv')

@app.route('/info')
def info():
    """Renders the information page."""
    return render_template('info.html')

@app.route('/order_list')
def order_list():
    """Renders the order list page with all inventory items.
    
    The filtering and download logic for the order list is now handled 
    by JavaScript on the client side in order.html.
    """
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return render_template('order.html', items=items, categories=CATEGORIES)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    """Handles the submitted order form."""
    ordered_items = {}
    for key, value in request.form.items():
        if key.startswith('order_') and value and int(value) > 0:
            item_id = key.split('_')[1]
            ordered_items[item_id] = value
    
    if ordered_items:
        message = "Order submitted for the following items: "
        for item_id, quantity in ordered_items.items():
            conn = get_db_connection()
            item = conn.execute('SELECT name, unit FROM items WHERE id = ?', (item_id,)).fetchone()
            conn.close()
            message += f"{item['name']} ({quantity} {item['unit']}), "
        flash(message.rstrip(', '), 'success')
    else:
        flash("No items were ordered.", 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
