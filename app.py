from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_HOST = "db-maftuna.clyucs4e44b4.ap-northeast-2.rds.amazonaws.com"
DB_NAME = "db_maftuna"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_PORT = "5432"

# Connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/api/market/transactions', methods=['GET'])
def get_transactions():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Get query parameters for pagination
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        # Get filter parameters
        category = request.args.get('category', default=None)
        payment = request.args.get('payment', default=None)

        # Calculate offset
        offset = (page - 1) * per_page

        # Prepare the base query
        base_query = 'FROM tbl_maftuna_supermarket_sales WHERE 1=1'
        params = []

        # Apply filters if provided
        if category:
            base_query += ' AND "Product Category" = %s'
            params.append(category)

        if payment:
            base_query += ' AND "Payment Method" = %s'
            params.append(payment)

        # Get total count for pagination info
        cursor.execute(f'SELECT COUNT(*) {base_query}', params)
        total_records = cursor.fetchone()[0]

        # Get records with pagination
        query = f'SELECT * {base_query} ORDER BY "Date" DESC LIMIT %s OFFSET %s'
        params.extend([per_page, offset])
        cursor.execute(query, params)

        records = cursor.fetchall()

        # Convert records to list of dictionaries
        transactions = []
        for record in records:
            transactions.append(dict(record))

        cursor.close()
        conn.close()

        return jsonify({
            "transactions": transactions,
            "pagination": {
                "total": total_records,
                "current_page": page,
                "items_per_page": per_page,
                "total_pages": (total_records + per_page - 1) // per_page
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market/inventory/add', methods=['POST'])
def add_inventory():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["Invoice ID", "Date", "Customer Type", "gender",
                           "Product Category", "Unit Price", "quantity",
                           "Total Sales", "Payment Method"]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Generate timestamp for logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if the invoice ID already exists
        cursor.execute('SELECT 1 FROM tbl_maftuna_supermarket_sales WHERE "Invoice ID" = %s',
                     (data["Invoice ID"],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Duplicate invoice ID detected", "status": "error"}), 409

        # Insert new record
        cursor.execute('''
            INSERT INTO tbl_maftuna_supermarket_sales
            ("Invoice ID", "Date", "Customer Type", "gender", "Product Category",
             "Unit Price", "quantity", "Total Sales", "Payment Method")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data["Invoice ID"],
            data["Date"],
            data["Customer Type"],
            data["gender"],
            data["Product Category"],
            float(data["Unit Price"]),
            int(data["quantity"]),
            float(data["Total Sales"]),
            data["Payment Method"]
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Inventory item added successfully",
            "timestamp": timestamp,
            "item_data": data
        }), 201

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/market/inventory/remove/<invoice_id>', methods=['DELETE'])
def remove_inventory(invoice_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed", "status": "error"}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # Use DictCursor

        # Generate timestamp for logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if the record exists before attempting to delete
        cursor.execute('SELECT * FROM tbl_maftuna_supermarket_sales WHERE "Invoice ID" = %s', (invoice_id,))
        record = cursor.fetchone()
        if not record:
            cursor.close()
            conn.close()
            return jsonify({"error": "Record not found", "status": "error"}), 404

        # Record is already a DictRow, no need for dict() conversion

        # Delete the record
        cursor.execute('DELETE FROM tbl_maftuna_supermarket_sales WHERE "Invoice ID" = %s', (invoice_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": f"Inventory item removed successfully",
            "timestamp": timestamp,
            "removed_item": {
                "invoice_id": invoice_id,
                "product": record["Product Category"], # Access directly from record
                "date": record["Date"] # Access directly from record
            }
        })

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

# Additional endpoints for statistics and reporting
@app.route('/api/market/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Get total sales amount
        cursor.execute('SELECT SUM("Total Sales") FROM tbl_maftuna_supermarket_sales')
        total_sales_amount = cursor.fetchone()[0]

        # Get total number of transactions
        cursor.execute('SELECT COUNT(*) FROM tbl_maftuna_supermarket_sales')
        total_transactions = cursor.fetchone()[0]

        # Get sales by category
        cursor.execute('SELECT "Product Category", SUM("Total Sales") as total FROM tbl_maftuna_supermarket_sales GROUP BY "Product Category" ORDER BY total DESC')
        sales_by_category = [dict(row) for row in cursor.fetchall()]

        # Get sales by payment method
        cursor.execute('SELECT "Payment Method", COUNT(*) as count FROM tbl_maftuna_supermarket_sales GROUP BY "Payment Method" ORDER BY count DESC')
        payment_methods = [dict(row) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            "total_sales_amount": float(total_sales_amount) if total_sales_amount else 0,
            "total_transactions": total_transactions,
            "sales_by_category": sales_by_category,
            "payment_methods": payment_methods
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
