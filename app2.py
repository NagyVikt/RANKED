import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Dictionary to hold thread status
thread_manager = {}
thread_manager_lock = threading.Lock()

def thread_function(name):
    print(f"Thread {name} starting")
    for i in range(5):
        print(f"Thread {name} is running iteration {i}")
        time.sleep(2)
    print(f"Thread {name} finishing")
    # Notify clients that the thread has finished
    with thread_manager_lock:
        thread_manager[name]['status'] = 'offline'
    socketio.emit('update_status', {name: 'offline'}, namespace='/', broadcast=True)

def create_thread(name):
    thread = threading.Thread(target=thread_function, args=(name,))
    thread.start()
    with thread_manager_lock:
        thread_manager[name] = {'status': 'online'}
    socketio.emit('update_status', {name: 'online'}, namespace='/', broadcast=True)

@app.route('/')
def index():
    return render_template('index.html', thread_manager=thread_manager)

@socketio.on('connect')
def handle_connect():
    # Send the current status of all threads on new connection
    with thread_manager_lock:
        for name, details in thread_manager.items():
            emit('update_status', {name: details['status']}, namespace='/')


if __name__ == "__main__":
    socketio.start_background_task(create_thread, "Thread-1")
    socketio.start_background_task(create_thread, "Thread-2")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=True)