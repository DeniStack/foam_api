from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS from flask_cors
import pyodbc
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Replace these with your actual SQL Server credentials
server = "10.3.28.68"
port = 1433 # Default port for SQL Server is sometimes 3306
database = 'Foam_tools'
username = 'bde'
password = '!bde1234'
driver = 'ODBC Driver 18 for SQL Server'

# Update connection string to use the correct port
conn_str = f'DRIVER={driver};SERVER={server},{port};DATABASE={database};UID={username};PWD={password};Encrypt=no'


def get_db_connection():
    return pyodbc.connect(conn_str)



def execute_with_retry(cursor, sql, params=None, max_attempts=3, delay=1):
    for attempt in range(max_attempts):
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        except pyodbc.OperationalError as e:
            if attempt == max_attempts - 1:
                raise
            print(f"Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)


@app.route("/api/active", methods=["GET", "POST", "DELETE"])
def handle_active():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1000) [Alat] FROM [Foam_tools].[dbo].[Active]"
            active_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(active_data)
        
        elif request.method == "POST":
            data = request.get_json()
            tool_name = data.get('tool')
            insert_query = "INSERT INTO [Foam_tools].[dbo].[Active] ([Alat]) VALUES (?)"
            try:
                execute_with_retry(cursor, insert_query, (tool_name,))
                conn.commit()
                return jsonify({"message": "Tool added successfully"}), 201
            except Exception as e:
                conn.rollback()
                return jsonify({"error": str(e)}), 500
        
        elif request.method == "DELETE":
            data = request.get_json()
            tool_name = data.get('tool')
            delete_query = "DELETE FROM [Foam_tools].[dbo].[Active] WHERE [Alat] = ?"
            try:
                execute_with_retry(cursor, delete_query, (tool_name,))
                conn.commit()
                return jsonify({"message": "Tool deleted successfully"}), 200
            except Exception as e:
                conn.rollback()
                return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route("/api/karijers", methods=["GET", "POST", "DELETE"])
def handle_carrier():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1000) [Serijski_broj] FROM [Foam_tools].[dbo].[Karijers]"
            cursor.execute(query)  # Execute the query before fetching
            karijeri_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            return jsonify(karijeri_data)

        elif request.method == "POST":
            data = request.get_json()
            carrier_name = data.get('Serijski_broj')
            insert_query = "INSERT INTO [Foam_tools].[dbo].[Karijers] ([Serijski_broj]) VALUES (?)"
            try:
                execute_with_retry(cursor, insert_query, (carrier_name,))
                conn.commit()
                print(f"Carrier '{carrier_name}' added to the database.")
                return jsonify({"message": "Carrier added successfully"})
            except Exception as e:
                conn.rollback()
                print(f"Error adding carrier '{carrier_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500

        elif request.method == "DELETE":
            data = request.get_json()
            carrier_name = data.get('Serijski_broj')
            delete_query = "DELETE FROM [Foam_tools].[dbo].[Karijers] WHERE [Serijski_broj] = ?"
            try:
                execute_with_retry(cursor, delete_query, (carrier_name,))
                conn.commit()
                print(f"Carrier '{carrier_name}' deleted from the database.")
                return jsonify({"message": "Carrier deleted successfully"})
            except Exception as e:
                conn.rollback()
                print(f"Error deleting carrier '{carrier_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
def handle_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == 'GET':
            query = 'SELECT id, username, email, permissions FROM dbo.Users'
            users_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(users_data)
        
        elif request.method == 'POST':
            data = request.json
            username = data.get('username')
            email = data.get('email')
            permissions = data.get('permissions')

            if username and email and permissions:
                insert_query = 'INSERT INTO dbo.Users (username, email, permissions) VALUES (?, ?, ?)'
                try:
                    execute_with_retry(cursor, insert_query, (username, email, permissions))
                    conn.commit()
                    return jsonify({'message': 'User added successfully'}), 201
                except Exception as e:
                    conn.rollback()
                    return jsonify({'error': str(e)}), 500

        elif request.method == 'DELETE':
            user_id = request.args.get('id')
            if user_id:
                delete_query = 'DELETE FROM dbo.Users WHERE id = ?'
                try:
                    execute_with_retry(cursor, delete_query, (user_id,))
                    conn.commit()
                    return jsonify({'message': f'User with id {user_id} deleted successfully'}), 200
                except Exception as e:
                    conn.rollback()
                    return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Route for /api/oficijalno
@app.route("/api/oficijalno", methods=["GET"])
def handle_oficijalno():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = """
                SELECT TOP (1000) [Interni_broj], [Kupac], [Projekat], [Vrsta_alata], [Broj_proizvoda], [Kavitet] 
                FROM [Foam_tools].[dbo].[Oficijalno]
            """
            oficijalno_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(oficijalno_data)
    finally:
        cursor.close()
        conn.close()


# Route for /api/rezerva
@app.route("/api/rezerva", methods=["GET"])
def handle_rezerva():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = """
                SELECT TOP (1000) [RB], [Pozicija], [Alat], [Lokacija]
                FROM [Foam_tools].[dbo].[Rezerva]
            """
            rezerva_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(rezerva_data)
    finally:
        cursor.close()
        conn.close()


# Route for /api/trenutno_stanje
@app.route("/api/trenutno_stanje", methods=["GET"])
def handle_trenutno_stanje():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = """
                SELECT TOP (1000) [Kerijer]
                FROM [Foam_tools].[dbo].[Trenutno_stanje]
            """
            trenutno_stanje_data = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(trenutno_stanje_data)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/table_name_carriers", methods=["GET", "POST"])
def handle_table_name_carriers():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1) [id], [name] FROM [Foam_tools].[dbo].[table_name_carriers]"
            names = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in execute_with_retry(cursor, query)
            ]
            return jsonify(names)
        
        elif request.method == "POST":
            data = request.get_json()
            table_name = data.get('name')
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("DELETE FROM [Foam_tools].[dbo].[table_name_carriers] WHERE id = 0")
                insert_query = "INSERT INTO [Foam_tools].[dbo].[table_name_carriers] ([id], [name]) VALUES (?, ?)"
                cursor.execute(insert_query, (0, table_name))
                cursor.execute("COMMIT")
                return jsonify({"message": "Data updated successfully"}), 200
            except Exception as e:
                cursor.execute("ROLLBACK")
                return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/table_name_tools", methods=["GET", "POST"])
def handle_table_name_tools():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1) [id], [name] FROM [Foam_tools].[dbo].[table_name_tools]"
            cursor.execute(query)
            names = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            return jsonify(names)

        elif request.method == "POST":
            data = request.get_json()
            table_name = data.get('name')
            
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete existing record with id = 0
                cursor.execute("DELETE FROM [Foam_tools].[dbo].[table_name_tools] WHERE id = 0")
            
                # Insert new record
                insert_query = "INSERT INTO [Foam_tools].[dbo].[table_name_tools] ([id], [name]) VALUES (?, ?)"
                cursor.execute(insert_query, (0, table_name))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.commit()
                
                print(f"Tools '{table_name}' added to the database.")
                return jsonify({"message": "Tool added successfully", "id": 0})
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.rollback()
                print(f"Error adding tool '{table_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/carriers_allocation", methods=["GET", "POST", "DELETE"])
def handle_carriers_allocation():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1000) [name], [position] FROM [Foam_tools].[dbo].[carriers_allocation]"
            cursor.execute(query)
            carriers_allocation = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            return jsonify(carriers_allocation)

        elif request.method == "POST":
            data = request.get_json()
            carrier_name = data.get('name')
            carrier_position = data.get('position')
            
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete existing record with the same name
                cursor.execute("DELETE FROM [Foam_tools].[dbo].[carriers_allocation] WHERE name = ?", (carrier_name,))
            
                # Insert new record
                insert_query = "INSERT INTO [Foam_tools].[dbo].[carriers_allocation] ([name], [position]) VALUES (?, ?)"
                cursor.execute(insert_query, (carrier_name, carrier_position))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.commit()
                
                print(f"Carrier '{carrier_name}' added to the database.")
                return jsonify({"message": "Carrier added successfully"})
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.rollback()
                print(f"Error adding carrier '{carrier_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500

        elif request.method == "DELETE":
            data = request.get_json()
            carrier_name = data.get('name')
            
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete record with the specified name
                delete_query = "DELETE FROM [Foam_tools].[dbo].[carriers_allocation] WHERE name = ?"
                cursor.execute(delete_query, (carrier_name,))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.commit()
                
                print(f"Carrier '{carrier_name}' deleted from the database.")
                return jsonify({"message": "Carrier deleted successfully"})
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.rollback()
                print(f"Error deleting carrier '{carrier_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/tools_allocation", methods=["GET", "POST", "DELETE"])
def handle_tools_allocation():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            query = "SELECT TOP (1000) [name], [position] FROM [Foam_tools].[dbo].[tools_allocation]"
            cursor.execute(query)
            tool_allocation = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            return jsonify(tool_allocation)

        elif request.method == "POST":
            data = request.get_json()
            tool_name = data.get('name')
            tool_position = data.get('position')
            
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete existing record with the same name
                cursor.execute("DELETE FROM [Foam_tools].[dbo].[tools_allocation] WHERE name = ?", (tool_name,))
            
                # Insert new record
                insert_query = "INSERT INTO [Foam_tools].[dbo].[tools_allocation] ([name], [position]) VALUES (?, ?)"
                cursor.execute(insert_query, (tool_name, tool_position))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.commit()
                
                print(f"Tool '{tool_name}' added to the database.")
                return jsonify({"message": "Tool added successfully"})
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.rollback()
                print(f"Error adding tool '{tool_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500

        elif request.method == "DELETE":
            data = request.get_json()
            tool_name = data.get('name')
            
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete record with the specified name
                delete_query = "DELETE FROM [Foam_tools].[dbo].[tools_allocation] WHERE name = ?"
                cursor.execute(delete_query, (tool_name,))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.commit()
                
                print(f"Tool '{tool_name}' deleted from the database.")
                return jsonify({"message": "Tool deleted successfully"})
            
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.rollback()
                print(f"Error deleting tool '{tool_name}': {str(e)}")
                return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
