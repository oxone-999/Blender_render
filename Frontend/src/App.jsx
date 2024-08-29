import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const App = () => {
  const [logs, setLogs] = useState("");
  const [frameData, setFrameData] = useState({ frame: null, time: null });
  const [isRunning, setIsRunning] = useState(false);
  const [blendFiles, setBlendFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [startFrame, setStartFrame] = useState(1);
  const [endFrame, setEndFrame] = useState(300);
  const [crashCount, setCrashCount] = useState(0);
  const [crashReasons, setCrashReasons] = useState([]);
  const [lastFrameProcessed, setLastFrameProcessed] = useState(1);
  const [lastFrameTime, setLastFrameTime] = useState(null); // New state for tracking last frame time
  const [estimatedTimeLeft, setEstimatedTimeLeft] = useState(null); // New state for tracking estimated time left

  console.log(lastFrameProcessed);

  useEffect(() => {
    // Fetch the list of .blend files from the backend
    axios
      .get("http://127.0.0.1:5000/list_blend_files")
      .then((response) => {
        setBlendFiles(response.data);
      })
      .catch((error) => {
        console.error("Error fetching blend files:", error);
      });

    // Check if the script is running on mount or refresh
    axios
      .get("http://127.0.0.1:5000/script-status")
      .then((response) => {
        if (response.data.status === "running") {
          setIsRunning(true);
          connectToEventSource(); // Reconnect to the logs stream if running
        }
      })
      .catch((error) => {
        console.error("Error checking script status:", error);
      });

    // Fetch crash info
    fetchCrashInfo();
  }, []);

  const fetchCrashInfo = () => {
    axios
      .get("http://127.0.0.1:5000/crash-info")
      .then((response) => {
        setCrashCount(response.data.crash_count);
        setCrashReasons(response.data.crash_reasons);
        console.log(response.data);
      })
      .catch((error) => {
        console.error("Error fetching crash info:", error);
      });
  };

  const connectToEventSource = () => {
    const eventSource = new EventSource("http://127.0.0.1:5000/stream-logs");

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.frame !== undefined && data.time !== undefined) {
          handleNewFrameData(data);
        } else if (data.error) {
          setLogs((prevLogs) => prevLogs + data.error + "\n");
          fetchCrashInfo(); // Fetch updated crash info on error
        } else {
          setLogs((prevLogs) => prevLogs + event.data + "\n");
        }
      } catch (e) {
        setLogs((prevLogs) => prevLogs + event.data + "\n");
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsRunning(false);
    };
  };

  const runScript = async () => {
    setIsRunning(true);
    try {
      await axios.post("http://127.0.0.1:5000/start-script", {
        blend_file_path: selectedFile,
        start_frame: startFrame,
        end_frame: endFrame,
      });

      connectToEventSource(); // Connect to logs stream after starting the script
    } catch (error) {
      console.error("Error running the script:", error);
      setIsRunning(false);
    }
  };

  const stopScript = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:5000/stop-script");
      setIsRunning(false);
      setLogs((prevLogs) => prevLogs + "Script stopped.\n");
    } catch (error) {
      console.error("Error stopping the script:", error);
    }
  };

  const handleNewFrameData = (data) => {
    // Update frame data and calculate time estimates
    setFrameData(data);
    
    if (data.frame !== null) {
      // Calculate time taken for the last frame
      const timeTakenForLastFrame = convertTimeToSeconds(lastFrameTime);

      // Update last frame time
      setLastFrameTime(data.time);

      // Calculate remaining frames and estimated time left
      const remainingFrames = (endFrame ? endFrame : data.frame) - data.frame;
      const estimatedTime = remainingFrames * timeTakenForLastFrame;

      setEstimatedTimeLeft(estimatedTime);
    } else {
      // If this is the first frame, just set the initial time
      setLastFrameTime(data.time);
    }
  };

  const convertTimeToSeconds = (timeString) => {
    if (!timeString) return 0;
  
    // Example timeString format: "00:08.89"
    const [minutes, seconds] = timeString.split(":");
  
    // Convert to seconds
    const totalSeconds = parseInt(minutes) * 60 + parseFloat(seconds);
    return totalSeconds;
  };

  return (
    <div className="main">
      <h1>Blender Render Manager</h1>
      <div className="file">
        <div>
          <label>Select .blend file:</label>
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
          >
            <option value="">-- Select a file --</option>
            {blendFiles.map((file, index) => (
              <option key={index} value={file}>
                {file}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label>Start Frame:</label>
          <input
            type="number"
            value={startFrame}
            onChange={(e) => setStartFrame(parseInt(e.target.value))}
          />
        </div>
        <div>
          <label>End Frame:</label>
          <input
            type="number"
            value={endFrame}
            onChange={(e) => setEndFrame(parseInt(e.target.value))}
          />
        </div>
      </div>
      <div className="button">
        <button
          className={!isRunning && "Run"}
          onClick={runScript}
          disabled={isRunning}
        >
          Start Render
        </button>
        <button
          className={isRunning && "Stop"}
          onClick={stopScript}
          disabled={!isRunning}
        >
          Stop Render
        </button>
      </div>
      <div className="info">
        <div className="current">
          <h2>Current Frame:</h2>
          <p>Frame: {frameData.frame}</p>
          <p>Time: {frameData.time}</p>
          <h2>Estimated Time Left</h2>
          <p>
            {estimatedTimeLeft !== null
              ? `${estimatedTimeLeft.toFixed(2)} seconds`
              : "Calculating..."}
          </p>
        </div>
        <div className="crash">
          <h2>Crash Information:</h2>
          <p>Crash Count: {crashCount}</p>
          <h3>Crash Reason:</h3>
          {crashReasons != undefined ? (
            <ul>
              {crashReasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          ) : (
            <p>Not Crashed Yet</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
