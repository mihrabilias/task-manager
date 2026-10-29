import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_NAME = "database.db"

# Initialize Database
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Create tasks table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Offen'
            )
        ''')
        conn.commit()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Enables dict-like access to rows
    return conn

# ----------------- ROUTES -----------------

@app.route('/')
def index():
    """Serve the main HTML application."""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Read: Get all tasks, with optional search and status filtering."""
    search = request.args.get('search', '').lower()
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    
    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id DESC"
    
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(task) for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create: Add a new task."""
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    priority = data.get('priority', 'Mittel')
    status = data.get('status', 'Offen')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, priority, status) VALUES (?, ?, ?, ?)",
        (title, description, priority, status)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': new_id, 'message': 'Task created successfully'}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update: Modify an existing task."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if task exists
    task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
        
    title = data.get('title', task['title'])
    description = data.get('description', task['description'])
    priority = data.get('priority', task['priority'])
    status = data.get('status', task['status'])
    
    cursor.execute(
        "UPDATE tasks SET title = ?, description = ?, priority = ?, status = ? WHERE id = ?",
        (title, description, priority, status, task_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task updated successfully'})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete: Remove a task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted == 0:
        return jsonify({'error': 'Task not found'}), 404
        
    return jsonify({'message': 'Task deleted successfully'})

if __name__ == '__main__':
    # Run the application on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
