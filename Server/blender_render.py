# import subprocess

# def run_command(command, cwd=None):
#     try:
#         # Execute the command and capture output and error
#         result = subprocess.run(
#             command,
#             shell=True,
#             check=True,
#             cwd=cwd,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )
        
#         # Print the standard output and standard error
#         print("Standard Output:\n", result.stdout)
#         print("Standard Error:\n", result.stderr)
        
#         # Return the command's return code
#         return result.returncode
#     except subprocess.CalledProcessError as e:
#         print("An error occurred:", e)
#         print("Standard Output:\n", e.stdout)
#         print("Standard Error:\n", e.stderr)
#         return e.returncode

# if __name__ == "__main__":
#     # Define the directory and command
#     directory = r"C:\Program Files\Blender Foundation\Blender 3.6"
#     command = r'blender -b D:\f\Clients\Balanc8\Scene_3_sunset_3.6.blend -s 1 -e 300 -a'
    
#     # Run the command in the specified directory
#     return_code = run_command(command, cwd=directory)
    
#     print(f"Command exited with return code {return_code}")

import subprocess

def run_command(command, cwd=None):
    try:
        # Execute the command and directly display output and error in real-time
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Continuously read and print the output and error streams
        for stdout_line in process.stdout:
            print("Standard Output:", stdout_line, end='')  # `end=''` to avoid double newlines
        for stderr_line in process.stderr:
            print("Standard Error:", stderr_line, end='')  # `end=''` to avoid double newlines
        
        # Wait for the process to complete and get the return code
        return_code = process.wait()
        
        return return_code
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1  # Indicate failure

def run():
    # Define the directory and command
    directory = r"C:\Program Files\Blender Foundation\Blender 3.6"
    command = r'blender -b D:\f\Clients\Balanc8\Scene_3_sunset_3.6.blend -s 1 -e 300 -a'
    
    # Run the command in the specified directory
    return_code = run_command(command, cwd=directory)
    
    print(f"Command exited with return code {return_code}")

