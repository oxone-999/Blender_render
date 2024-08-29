from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import subprocess
import re
import os
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
running_process = None
crash_count = 0
crash_reasons = []
last_frame = 1  # Keep track of the last completed frame
blend_file_path = ""
start_frame = 1
end_frame = 300

BLEND_FILES_DIRECTORY = r"D:\f\Clients\Balanc8"
BLENDER_EXECUTABLE = r"C:\Program Files\Blender Foundation\Blender 3.6\blender"

def parse_frame_and_time(log_line):
    """
    Parse the log line to extract frame number and time.
    """
    match = re.search(r'Fra:(\d+) .*?Time:(\d{2}:\d{2}\.\d{2})', log_line)
    if match:
        frame_number = int(match.group(1))
        time_taken = match.group(2)
        return frame_number, time_taken
    return None, None

def generate_logs():
    """
    Generator function to stream logs from the command execution.
    """
    global running_process, crash_count, crash_reasons, last_frame

    try:
        # Stream output and error in real-time
        while True:
            output = running_process.stdout.readline()
            if output:
                frame_number, time_taken = parse_frame_and_time(output)
                if frame_number is not None:
                    last_frame = frame_number
                    # Send the latest frame and time to the client
                    yield f"data: {{\"frame\": {last_frame}, \"time\": \"{time_taken}\"}}\n\n"
                else:
                    # Send regular log data
                    yield f"data: {output}\n\n"
            elif running_process.poll() is not None:
                break

        # Check if Blender crashed
        if running_process.returncode != 0:
            crash_reason = running_process.stderr.read()
            crash_reasons.append(crash_reason)
            crash_count += 1
            # Restart script if crash is detected
            yield f"data: {{\"error\": \"Blender crashed. Reason: {crash_reason}\"}}\n\n"
            restart_script()

    except Exception as e:
        yield f"data: An error occurred: {str(e)}\n\n"

def start_blender_script(blend_file_path, start_frame, end_frame):
    """
    Function to start Blender script with specified parameters.
    """
    global running_process
    command = f'"{BLENDER_EXECUTABLE}" -b "{blend_file_path}" -s {start_frame} -e {end_frame} -a'
    print(f"Starting Blender with command: {command}")

    running_process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

@app.route('/', methods=['POST'])
def Home():
    return "Hi";

@app.route('/start-script', methods=['POST'])
def start_script_route():
    global running_process, crash_count, crash_reasons, last_frame, blend_file_path, start_frame, end_frame

    # Reset crash data
    crash_count = 0
    crash_reasons = []

    # Get parameters from the request
    file = request.json.get('blend_file_path')
    blend_file_path = os.path.join(BLEND_FILES_DIRECTORY, file)
    start_frame = request.json.get('start_frame', 1)
    end_frame = request.json.get('end_frame', 300)

    if not os.path.exists(blend_file_path):
        return jsonify({"error": "Blend file does not exist"}), 400

    last_frame = start_frame  # Reset last frame to start frame

    # Start the Blender script
    start_blender_script(blend_file_path, start_frame, end_frame)

    return jsonify({"status": "Script started"}), 200

@app.route('/stream-logs', methods=['GET'])
def stream_logs_route():
    global running_process

    if not running_process:
        return jsonify({"error": "No script is currently running"}), 400

    return Response(generate_logs(), mimetype='text/event-stream')

@app.route('/stop-script', methods=['GET'])
def stop_script_route():
    global running_process
    if running_process and running_process.poll() is None:
        running_process.terminate()
        return jsonify({"status": "Process terminated"})
    return jsonify({"status": "No process running or already terminated"})

@app.route('/script-status', methods=['GET'])
def script_status():
    global running_process
    if running_process and running_process.poll() is None:
        return jsonify({"status": "running"}), 200
    else:
        return jsonify({"status": "stopped"}), 200

@app.route('/crash-info', methods=['GET'])
def crash_info():
    return jsonify({"crash_count": crash_count, "crash_reasons": crash_reasons}), 200

def restart_script():
    """
    Function to restart the script in case of a crash.
    """
    global running_process, last_frame, blend_file_path, start_frame, end_frame

    if running_process:
        running_process.terminate()
        time.sleep(2)  # Short delay before restarting

    # Restart from the last completed frame
    print(f"Restarting Blender script from frame {last_frame}")
    start_blender_script(blend_file_path, last_frame, end_frame)
    
@app.route('/list_blend_files', methods=['GET'])
def list_blend_files():
    try:
        # Ensure the directory exists
        if not os.path.isdir(BLEND_FILES_DIRECTORY):
            return jsonify({"error": "Directory does not exist"}), 404

        # List all files in the directory ending with .blend
        blend_files = [f for f in os.listdir(BLEND_FILES_DIRECTORY) if f.endswith('.blend')]
        return jsonify(blend_files), 200

    except Exception as e:
        # Return error details as JSON
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True, threaded=True)



