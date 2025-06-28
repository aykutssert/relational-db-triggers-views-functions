# Bookstore Database Management System

A comprehensive web-based database management system for bookstore operations, featuring advanced SQL techniques including views, functions, triggers, transactions, and complex JOIN operations with an intuitive Flask web interface.

## 🎯 Project Overview

This project demonstrates practical database design and implementation skills through a complete bookstore management system. The application showcases advanced database concepts including transaction management, stored procedures, database triggers, and complex query optimization.

### Key Features
- **User Management**: Customer and admin authentication with role-based access
- **Inventory Control**: Book stock management with automated tracking
- **Order Processing**: Complete order lifecycle with real-time updates
- **Advanced SQL**: Views, functions, triggers, and transaction demonstrations
- **Analytics Dashboard**: Business intelligence with custom database views

## 🏗️ Database Architecture

### Core Tables
- **Users**: Customer and admin account management
- **Books**: Product catalog with stock tracking
- **Categories**: Book classification system
- **Authors**: Author information and relationships
- **Orders**: Transaction records with status tracking
- **Order Details**: Line-item specifics with automated calculations

### Advanced Database Features

#### Views Implementation
- **books_in_stock**: Available inventory with detailed information
- **customer_orders_summary**: Customer purchase analytics
- **author_books**: Author-book relationship aggregation
- **high_value_orders**: Premium transaction analysis
- **low_stock_books**: Inventory management alerts

#### Custom Functions
- **get_book_stock()**: Real-time stock level queries
- **calculate_order_total()**: Dynamic order value calculation
- **get_books_by_category()**: Category-based book counting
- **get_author_book_count()**: Author productivity metrics
- **get_average_completed_order_value()**: Revenue analytics

#### Database Triggers
- **book_insert_log**: Automatic logging of new book additions
- **book_update_log**: Stock change tracking and auditing
- **user_insert_log**: User registration monitoring
- **stock_update_trigger**: Automated inventory updates on orders

## 🚀 Technology Stack

### Backend
- **Python Flask**: Web framework with session management
- **MySQL**: Relational database with advanced SQL features
- **mysql-connector-python**: Database connectivity and query execution

### Frontend
- **HTML/CSS**: Responsive user interface design
- **Bootstrap**: Professional styling and layout
- **JavaScript**: Interactive dashboard elements

### Database Features
- **Transaction Management**: ACID compliance with rollback mechanisms
- **Stored Procedures**: Reusable database logic
- **Foreign Key Constraints**: Data integrity enforcement
- **Indexing**: Optimized query performance

## 📊 Application Features

### Customer Interface
- **Browse Catalog**: Search and filter available books
- **Place Orders**: Add items to cart with stock validation
- **Order History**: Track purchase history and status
- **Account Management**: Profile and authentication

### Admin Dashboard
- **Inventory Management**: Add books, update stock levels
- **User Administration**: Customer account management
- **Order Processing**: Status updates and fulfillment tracking
- **Database Analytics**: View performance and transaction logs

### Advanced Admin Tools
- **View Testing**: Interactive database view exploration
- **Function Execution**: Custom function testing with parameters
- **Trigger Monitoring**: Real-time database trigger activity logs
- **Query Analysis**: JOIN operation demonstrations and performance testing
- **Transaction Testing**: Multi-step transaction scenarios with rollback handling

## 🔧 Technical Implementation

### Database Design Patterns
```sql
-- Example trigger for stock management
CREATE TRIGGER stock_update_trigger
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    UPDATE books 
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE book_id = NEW.book_id;
END;
```

### Transaction Management
- **Complete Order Processing**: Multi-table updates with rollback safety
- **Bulk Stock Updates**: Batch operations with consistency checks
- **Order Transfer Simulation**: Complex business logic transactions

### Query Optimization
- **LEFT JOIN**: Comprehensive data retrieval with optional relationships
- **INNER JOIN**: Efficient data correlation and filtering
- **UNION Operations**: Complex data aggregation and reporting
- **Subqueries**: Advanced filtering and conditional logic

## 🎮 Getting Started

### Prerequisites
```bash
pip install flask mysql-connector-python
```

### Database Setup
1. Create MySQL database: `bookstore_db`
2. Import schema and sample data
3. Configure database connection in `app.py`

### Running the Application
```bash
python app.py
```

Access the application at `http://localhost:5000`

### Default Login Credentials
- **Admin**: admin@bookstore.com / password
- **Customer**: customer@bookstore.com / password

## 📈 Database Demonstrations

### Advanced SQL Features
- **Complex JOIN Operations**: Multi-table data correlation
- **Aggregate Functions**: Business metrics and analytics
- **Conditional Logic**: Dynamic query generation
- **Performance Optimization**: Efficient query execution

### Business Intelligence
- **Sales Analytics**: Revenue tracking and customer insights
- **Inventory Reports**: Stock level monitoring and alerts
- **Order Analytics**: Purchase pattern analysis
- **Customer Segmentation**: Behavioral data analysis

## 🏆 Learning Outcomes

This project demonstrates expertise in:
- **Database Design**: Normalized schema with referential integrity
- **Advanced SQL**: Complex queries, procedures, and optimization
- **Web Development**: Full-stack application with database integration
- **Transaction Management**: ACID properties and concurrency control
- **System Architecture**: Scalable design patterns and best practices

## 📁 Project Structure

```
bookstore-database-management-system/
├── app.py                    # Main Flask application
├── templates/
│   ├── login.html           # Authentication interface
│   ├── customer_dashboard.html
│   ├── admin_dashboard.html
│   ├── admin_books.html     # Inventory management
│   ├── admin_users.html     # User administration
│   ├── admin_orders.html    # Order processing
│   ├── admin_views.html     # Database views demonstration
│   ├── admin_functions.html # Custom functions testing
│   ├── admin_triggers.html  # Trigger monitoring
│   ├── admin_queries.html   # JOIN operations demo
│   └── admin_transactions.html # Transaction testing
├── static/
│   └── style.css           # Application styling
├── database/
│   ├── schema.sql          # Database structure
│   └── sample_data.sql     # Test data
└── README.md               # This documentation
```

## 🎯 Technical Highlights

- **Production-Ready Database**: Comprehensive schema with advanced features
- **Real-time Analytics**: Live dashboard with database-driven insights
- **Transaction Safety**: Robust error handling and rollback mechanisms
- **Scalable Architecture**: Modular design supporting future enhancements
- **Security Implementation**: Role-based access control and data validation

---

**Skills Demonstrated**: Database Design, Advanced SQL, Web Development, Transaction Management, System Architecture