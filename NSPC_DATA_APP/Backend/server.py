from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

# MySQL database connection details
db_config = {
    'host': '127.0.0.1',  # Replace with your MySQL host
    'user': 'NSPC_Admin',    # Replace with your MySQL username
    'password': 'NSPC@2024_admin!',  # Replace with your MySQL password
    'database': 'NSPC_DATA_APP'  # Your database name
}

# Route to accept master data and insert into the database
@app.route('/insert_master_data', methods=['POST'])
def insert_master_data():
    try:
        # Get JSON data from the client
        data = request.json

        # Extract data fields
        s_no = data.get('s_no')
        v_id = data.get('v_id')
        v_name = data.get('v_name')
        relation_name = data.get('relation_name')
        relation_type = data.get('relation_type')
        address = data.get('address')
        age = data.get('age')
        gender = data.get('gender')
        v_status = data.get('v_status')
        contact = data.get('contact')

        # Create a database connection
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Insert data into the Master_data table
        insert_query = """
        INSERT INTO Master_data (s_no, v_id, v_name, relation_name, relation_type, address, age, gender, v_status, contact)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (s_no, v_id, v_name, relation_name, relation_type, address, age, gender, v_status, contact))

        # Commit the transaction
        connection.commit()

        # Close the connection
        cursor.close()
        connection.close()

        # Return success response
        return jsonify({'status': 'success', 'message': 'Data inserted successfully'}), 201

    except Exception as e:
        # Handle exceptions and return error response
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route to fetch master data by v_id, v_name, or contact
@app.route('/get_master_data', methods=['GET'])
def get_master_data():
    try:
        # Get query parameters from the client
        v_id = request.args.get('v_id')
        v_name = request.args.get('v_name')
        contact = request.args.get('contact')

        # Create a database connection
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)  # Use DictCursor for dictionary-style output

        # Build the quer`y dynamically based on the input
        if v_id:
            query = "SELECT * FROM Master_data WHERE v_id = %s"
            cursor.execute(query, (v_id,))
        elif v_name:
            query = "SELECT * FROM Master_data WHERE v_name = %s"
            cursor.execute(query, (v_name,))
        elif contact:
            query = "SELECT * FROM Master_data WHERE contact = %s"
            cursor.execute(query, (contact,))
        else:
            # Return error if no parameters are provided
            return jsonify({'status': 'error', 'message': 'Please provide v_id, v_name, or contact'}), 400

        # Fetch the result
        result = cursor.fetchall()

        # Close the connection
        cursor.close()
        connection.close()

        # Return the fetched data or an empty result if not found
        if result:
            return jsonify({'status': 'success', 'data': result}), 200
        else:
            return jsonify({'status': 'success', 'message': 'No matching records found'}), 404

    except Exception as e:
        # Handle exceptions and return error response
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
