from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        database='bookstore_db'
    )

@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['user_id']
            session['user_type'] = user['user_type']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            
            if user['user_type'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Geçersiz email veya şifre!')
        
        cursor.close()
        conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/customer')
def customer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM books_in_stock")
    books = cursor.fetchall()
    
    cursor.execute("""
        SELECT o.*, 
               COALESCE(GROUP_CONCAT(CONCAT(b.title, ' (', od.quantity, ')') SEPARATOR ', '), 'Ürün detayı yok') as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.order_id = od.order_id
        LEFT JOIN books b ON od.book_id = b.book_id
        WHERE o.user_id = %s
        GROUP BY o.order_id
        ORDER BY o.order_date DESC
    """, (session['user_id'],))
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('customer_dashboard.html', books=books, orders=orders)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    book_id = request.form['book_id']
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        book = cursor.fetchone()
        
        if book and book['stock_quantity'] >= quantity:
            cursor.execute("""
                INSERT INTO orders (user_id, status, total_amount) 
                VALUES (%s, 'pending', 0)
            """, (session['user_id'],))
            order_id = cursor.lastrowid
            
            subtotal = book['price'] * quantity
            cursor.execute("""
                INSERT INTO order_details (order_id, book_id, quantity, unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, book_id, quantity, book['price'], subtotal))
            
            conn.commit()
            flash('Sipariş başarıyla oluşturuldu!')
        else:
            flash('Yeterli stok yok!')
            
    except Exception as e:
        conn.rollback()
        flash(f'Hata: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('customer_dashboard'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM books")
    total_books = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE user_type = 'customer'")
    total_customers = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM orders")
    total_orders = cursor.fetchone()['total']
    
    cursor.execute("SELECT SUM(total_amount) as revenue FROM orders WHERE status = 'completed'")
    total_revenue = cursor.fetchone()['revenue'] or 0
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_books=total_books, 
                         total_customers=total_customers,
                         total_orders=total_orders,
                         total_revenue=total_revenue)

@app.route('/admin/books')
def admin_books():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT b.*, c.category_name,
               GROUP_CONCAT(CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') as authors
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        GROUP BY b.book_id
    """)
    books = cursor.fetchall()
    
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM authors")
    authors = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_books.html', books=books, categories=categories, authors=authors)

@app.route('/admin/er_diagram')
def er_diagram():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    return render_template('er_diagram.html')

@app.route('/admin/add_book', methods=['POST'])
def add_book():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    title = request.form['title']
    isbn = request.form['isbn']
    publication_year = request.form['publication_year']
    price = request.form['price']
    stock_quantity = request.form['stock_quantity']
    category_id = request.form['category_id']
    author_id = request.form['author_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO books (title, isbn, publication_year, price, stock_quantity, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, isbn, publication_year, price, stock_quantity, category_id))
        
        book_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)
        """, (book_id, author_id))
        
        conn.commit()
        flash('Kitap başarıyla eklendi!')
        
    except Exception as e:
        conn.rollback()
        flash(f'Hata: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_books'))

@app.route('/admin/update_stock', methods=['POST'])
def update_stock():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    book_id = request.form['book_id']
    new_stock = request.form['new_stock']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE books SET stock_quantity = %s WHERE book_id = %s
        """, (new_stock, book_id))
        
        conn.commit()
        flash('Stok başarıyla güncellendi!')
        
    except Exception as e:
        conn.rollback()
        flash(f'Hata: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_books'))

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    email = request.form['email']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    user_type = request.form['user_type']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password, first_name, last_name, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (email, password, first_name, last_name, user_type))
        
        conn.commit()
        flash('Kullanıcı başarıyla eklendi!')
        
    except Exception as e:
        conn.rollback()
        flash(f'Hata: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/orders')
def admin_orders():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.*, CONCAT(u.first_name, ' ', u.last_name) as customer_name,
               COALESCE(GROUP_CONCAT(CONCAT(b.title, ' (', od.quantity, ')') SEPARATOR ', '), 'Ürün detayı yok') as order_items
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        LEFT JOIN order_details od ON o.order_id = od.order_id
        LEFT JOIN books b ON od.book_id = b.book_id
        GROUP BY o.order_id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/update_order_status', methods=['POST'])
def update_order_status():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    order_id = request.form['order_id']
    new_status = request.form['new_status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE orders SET status = %s WHERE order_id = %s
        """, (new_status, order_id))
        
        conn.commit()
        flash('Sipariş durumu güncellendi!')
        
    except Exception as e:
        conn.rollback()
        flash(f'Hata: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/views')
def admin_views():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    views_data = {}
    
    cursor.execute("SELECT * FROM books_in_stock LIMIT 10")
    views_data['books_in_stock'] = cursor.fetchall()
    
    cursor.execute("SELECT * FROM customer_orders_summary")
    views_data['customer_orders_summary'] = cursor.fetchall()
    
    cursor.execute("SELECT * FROM author_books LIMIT 10")
    views_data['author_books'] = cursor.fetchall()
    
    cursor.execute("SELECT * FROM high_value_orders")
    views_data['high_value_orders'] = cursor.fetchall()
    
    cursor.execute("SELECT * FROM low_stock_books")
    views_data['low_stock_books'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_views.html', views_data=views_data)

@app.route('/admin/functions')
def admin_functions():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    functions_data = {}
    
    try:
        cursor.execute("SELECT get_book_stock(1) as result")
        functions_data['book_stock'] = cursor.fetchone()['result']
        
        cursor.execute("SELECT calculate_order_total(1) as result")
        functions_data['order_total'] = cursor.fetchone()['result']
        
        cursor.execute("SELECT get_books_by_category('Roman') as result")
        functions_data['books_by_category'] = cursor.fetchone()['result']
        
        cursor.execute("SELECT get_author_book_count(1) as result")
        functions_data['author_book_count'] = cursor.fetchone()['result']
        
        cursor.execute("SELECT get_average_completed_order_value() as result")
        functions_data['avg_order_value'] = cursor.fetchone()['result']
        
    except Exception as e:
        flash(f'Function test error: {str(e)}')
        functions_data = {}
    
    cursor.close()
    conn.close()
    
    return render_template('admin_functions.html', functions_data=functions_data)

@app.route('/admin/triggers')
def admin_triggers():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM system_logs 
        ORDER BY timestamp DESC 
        LIMIT 50
    """)
    logs = cursor.fetchall()
    
    triggers_data = {
        'book_logs': [],
        'user_logs': [],
        'order_logs': [],
        'stock_logs': []
    }
    
    for log in logs:
        if log['table_name'] == 'books':
            triggers_data['book_logs'].append(log)
        elif log['table_name'] == 'users':
            triggers_data['user_logs'].append(log)
        elif log['table_name'] == 'order_details' and 'STOCK_UPDATE' in log['operation']:
            triggers_data['stock_logs'].append(log)
        elif log['table_name'] == 'order_details':
            triggers_data['order_logs'].append(log)
    
    cursor.close()
    conn.close()
    
    return render_template('admin_triggers.html', triggers_data=triggers_data)

@app.route('/admin/queries')
def admin_queries():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    queries_data = {}
    
    try:
        cursor.execute("""
            SELECT b.title, b.price, b.stock_quantity, 
                   COALESCE(SUM(od.quantity), 0) as total_sold
            FROM books b
            LEFT JOIN order_details od ON b.book_id = od.book_id
            GROUP BY b.book_id, b.title, b.price, b.stock_quantity
            LIMIT 10
        """)
        queries_data['left_join'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT o.order_id, o.order_date, COALESCE(o.total_amount, 0) as total_amount, 
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
            LIMIT 10
        """)
        queries_data['right_join'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT b.title, 'Book' as type, b.price as amount, NULL as order_date
            FROM books b
            UNION
            SELECT CONCAT('Order #', o.order_id), 'Order' as type, 
                   o.total_amount as amount, o.order_date
            FROM orders o
            LIMIT 15
        """)
        queries_data['full_outer_join'] = cursor.fetchall()
        
    except Exception as e:
        flash(f'Query error: {str(e)}')
        queries_data = {'left_join': [], 'right_join': [], 'full_outer_join': []}
    
    custom_result = session.pop('custom_query_result', None)
    
    cursor.close()
    conn.close()
    
    return render_template('admin_queries.html', 
                         queries_data=queries_data, 
                         custom_result=custom_result)

@app.route('/admin/test_query', methods=['POST'])
def test_query():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    query_type = request.form['query_type']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if query_type == 'custom_left':
            cursor.execute("""
                SELECT c.category_name, COUNT(b.book_id) as book_count,
                       COALESCE(SUM(b.stock_quantity), 0) as total_stock
                FROM categories c
                LEFT JOIN books b ON c.category_id = b.category_id
                GROUP BY c.category_id, c.category_name
            """)
            result = cursor.fetchall()
            session['custom_query_result'] = {
                'type': 'Categories with Book Count (LEFT JOIN)',
                'description': 'Shows all categories including those with no books',
                'data': result,
                'columns': ['Category Name', 'Book Count', 'Total Stock']
            }
            
        elif query_type == 'custom_right':
            cursor.execute("""
                SELECT u.first_name, u.last_name, 
                       COALESCE(COUNT(o.order_id), 0) as order_count,
                       COALESCE(SUM(o.total_amount), 0) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                WHERE u.user_type = 'customer'
                GROUP BY u.user_id, u.first_name, u.last_name
            """)
            result = cursor.fetchall()
            session['custom_query_result'] = {
                'type': 'Customers with Order Stats (LEFT JOIN)',
                'description': 'Shows all customers including those with no orders',
                'data': result,
                'columns': ['First Name', 'Last Name', 'Order Count', 'Total Spent']
            }
            
        elif query_type == 'custom_full':
            cursor.execute("""
                SELECT 'Author' as entity_type, CONCAT(first_name, ' ', last_name) as name, 
                       birth_year as year_info, nationality as extra_info
                FROM authors
                UNION
                SELECT 'Book' as entity_type, title as name, 
                       publication_year as year_info, 'Literature' as extra_info
                FROM books
                ORDER BY entity_type, name
            """)
            result = cursor.fetchall()
            session['custom_query_result'] = {
                'type': 'Authors and Books Combined (UNION)',
                'description': 'Combines authors and books with publication years',
                'data': result,
                'columns': ['Entity Type', 'Name/Title', 'Year', 'Extra Info']
            }
        
        flash(f'Custom query executed successfully! {len(result)} rows returned.')
        
    except Exception as e:
        flash(f'Query error: {str(e)}')
        session['custom_query_result'] = None
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_queries') + '#custom-queries')

@app.route('/admin/test_function', methods=['POST'])
def test_function():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    function_name = request.form['function_name']
    param = request.form.get('param', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if function_name == 'get_book_stock':
            cursor.execute(f"SELECT get_book_stock({param}) as result")
        elif function_name == 'calculate_order_total':
            cursor.execute(f"SELECT calculate_order_total({param}) as result")
        elif function_name == 'get_books_by_category':
            cursor.execute(f"SELECT get_books_by_category('{param}') as result")
        elif function_name == 'get_author_book_count':
            cursor.execute(f"SELECT get_author_book_count({param}) as result")
        elif function_name == 'get_average_completed_order_value':
            cursor.execute("SELECT get_average_completed_order_value() as result")
        
        result = cursor.fetchone()
        flash(f'Function Result: {result["result"]}')
        
    except Exception as e:
        flash(f'Error: {str(e)}')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_functions'))

@app.route('/admin/transactions')
def admin_transactions():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    transaction_history = session.get('transaction_history', [])
    
    return render_template('admin_transactions.html', transaction_history=transaction_history)

@app.route('/admin/test_transaction1', methods=['POST'])
def test_transaction1():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    customer_id = request.form.get('customer_id', 2)
    book_id = request.form.get('book_id', 1)
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    transaction_log = {
        'type': 'Complete Order Processing',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'FAILED',
        'details': [],
        'error': None
    }
    
    try:
        cursor.execute("START TRANSACTION")
        transaction_log['details'].append("✅ Transaction started")
        
        cursor.execute("SELECT title, stock_quantity, price FROM books WHERE book_id = %s FOR UPDATE", (book_id,))
        book = cursor.fetchone()
        
        if not book:
            raise Exception(f"Book with ID {book_id} not found")
        
        if book['stock_quantity'] < quantity:
            raise Exception(f"Insufficient stock: Available {book['stock_quantity']}, Requested {quantity}")
        
        transaction_log['details'].append(f"✅ Stock check passed: {book['title']} ({book['stock_quantity']} available)")
        
        cursor.execute("""
            INSERT INTO orders (user_id, status, total_amount) 
            VALUES (%s, 'pending', 0)
        """, (customer_id,))
        order_id = cursor.lastrowid
        transaction_log['details'].append(f"✅ Order created: ID #{order_id}")
        
        subtotal = book['price'] * quantity
        cursor.execute("""
            INSERT INTO order_details (order_id, book_id, quantity, unit_price, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, book_id, quantity, book['price'], subtotal))
        transaction_log['details'].append(f"✅ Order details added: {quantity}x {book['title']} = {subtotal} TL")
        
        cursor.execute("SELECT stock_quantity FROM books WHERE book_id = %s", (book_id,))
        new_stock = cursor.fetchone()['stock_quantity']
        
        cursor.execute("SELECT total_amount FROM orders WHERE order_id = %s", (order_id,))
        order_total = cursor.fetchone()['total_amount']
        
        transaction_log['details'].append(f"✅ Stock updated: {book['stock_quantity']} → {new_stock}")
        transaction_log['details'].append(f"✅ Order total calculated: {order_total} TL")
        
        conn.commit()
        transaction_log['status'] = 'SUCCESS'
        transaction_log['details'].append("✅ Transaction committed successfully")
        
        flash(f'Transaction 1 completed successfully! Order #{order_id} created.')
        
    except Exception as e:
        conn.rollback()
        transaction_log['status'] = 'ROLLBACK'
        transaction_log['error'] = str(e)
        transaction_log['details'].append(f"❌ Error: {str(e)}")
        transaction_log['details'].append("🔄 Transaction rolled back")
        flash(f'Transaction 1 failed: {str(e)}')
    
    finally:
        cursor.close()
        conn.close()
        
        if 'transaction_history' not in session:
            session['transaction_history'] = []
        session['transaction_history'].insert(0, transaction_log)
        if len(session['transaction_history']) > 10:
            session['transaction_history'] = session['transaction_history'][:10]
    
    return redirect(url_for('admin_transactions'))

@app.route('/admin/test_transaction2', methods=['POST'])
def test_transaction2():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    stock_adjustment = int(request.form.get('stock_adjustment', 5))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    transaction_log = {
        'type': 'Bulk Stock Update',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'FAILED',
        'details': [],
        'error': None
    }
    
    try:
        cursor.execute("START TRANSACTION")
        transaction_log['details'].append("✅ Transaction started")
        
        cursor.execute("SELECT book_id, title, stock_quantity FROM books WHERE stock_quantity < 10 FOR UPDATE")
        low_stock_books = cursor.fetchall()
        
        if not low_stock_books:
            raise Exception("No books with low stock found")
        
        transaction_log['details'].append(f"✅ Found {len(low_stock_books)} books with low stock")
        
        updated_count = 0
        for book in low_stock_books:
            old_stock = book['stock_quantity']
            new_stock = old_stock + stock_adjustment
            
            cursor.execute("""
                UPDATE books 
                SET stock_quantity = %s 
                WHERE book_id = %s
            """, (new_stock, book['book_id']))
            
            if cursor.rowcount > 0:
                updated_count += 1
                transaction_log['details'].append(f"✅ {book['title']}: {old_stock} → {new_stock}")
        
        if updated_count == 0:
            raise Exception("No books were updated")
        
        cursor.execute("""
            INSERT INTO system_logs (table_name, operation, record_id, new_values)
            VALUES ('books', 'BULK_UPDATE', 0, %s)
        """, (f"Bulk stock update: {updated_count} books increased by {stock_adjustment}",))
        
        conn.commit()
        transaction_log['status'] = 'SUCCESS'
        transaction_log['details'].append(f"✅ Transaction committed: {updated_count} books updated")
        
        flash(f'Transaction 2 completed successfully! {updated_count} books updated.')
        
    except Exception as e:
        conn.rollback()
        transaction_log['status'] = 'ROLLBACK'
        transaction_log['error'] = str(e)
        transaction_log['details'].append(f"❌ Error: {str(e)}")
        transaction_log['details'].append("🔄 Transaction rolled back")
        flash(f'Transaction 2 failed: {str(e)}')
    
    finally:
        cursor.close()
        conn.close()
        
        if 'transaction_history' not in session:
            session['transaction_history'] = []
        session['transaction_history'].insert(0, transaction_log)
        if len(session['transaction_history']) > 10:
            session['transaction_history'] = session['transaction_history'][:10]
    
    return redirect(url_for('admin_transactions'))


@app.route('/admin/test_transaction3', methods=['POST'])
def test_transaction3():
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    from_user = int(request.form.get('from_user', 2))
    to_user = int(request.form.get('to_user', 3))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    transaction_log = {
        'type': 'Order Transfer Simulation',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'FAILED',
        'details': [],
        'error': None
    }
    
    try:
        cursor.execute("START TRANSACTION")
        transaction_log['details'].append("✅ Transaction started")
        
    
        cursor.execute("SELECT user_id, first_name, last_name FROM users WHERE user_id IN (%s, %s)", (from_user, to_user))
        users = {user['user_id']: f"{user['first_name']} {user['last_name']}" for user in cursor.fetchall()}
        
        if len(users) != 2:
            raise Exception("One or both users not found")
        
        
        cursor.execute("""
            SELECT order_id, total_amount 
            FROM orders 
            WHERE user_id = %s AND status = 'pending' 
            FOR UPDATE
        """, (from_user,))
        orders = cursor.fetchall()
        
        if not orders:
            raise Exception(f"No pending orders found for user {users[from_user]}")
        
        transaction_log['details'].append(f"✅ Found {len(orders)} pending orders from {users[from_user]}")
        
        
        total_transferred = 0
        for order in orders:
            cursor.execute("""
                UPDATE orders 
                SET user_id = %s 
                WHERE order_id = %s
            """, (to_user, order['order_id']))
            
            total_transferred += order['total_amount']
            transaction_log['details'].append(f"✅ Order #{order['order_id']} ({order['total_amount']} TL) transferred")
        
   
        cursor.execute("""
            INSERT INTO system_logs (table_name, operation, record_id, new_values)
            VALUES ('orders', 'TRANSFER', %s, %s)
        """, (from_user, f"Transferred {len(orders)} orders to user {to_user}, Total: {total_transferred} TL"))
        
        conn.commit()
        transaction_log['status'] = 'SUCCESS'
        transaction_log['details'].append(f"✅ Transaction committed: {len(orders)} orders transferred from {users[from_user]} to {users[to_user]}")
        
        flash(f'Transaction 3 completed successfully! {len(orders)} orders transferred.')
        
    except Exception as e:
        conn.rollback()
        transaction_log['status'] = 'ROLLBACK'
        transaction_log['error'] = str(e)
        transaction_log['details'].append(f"❌ Error: {str(e)}")
        transaction_log['details'].append("🔄 Transaction rolled back")
        flash(f'Transaction 3 failed: {str(e)}')
    
    finally:
        cursor.close()
        conn.close()
        
        if 'transaction_history' not in session:
            session['transaction_history'] = []
        session['transaction_history'].insert(0, transaction_log)
        if len(session['transaction_history']) > 10:
            session['transaction_history'] = session['transaction_history'][:10]
    
    return redirect(url_for('admin_transactions'))


if __name__ == '__main__':
    app.run(debug=True)