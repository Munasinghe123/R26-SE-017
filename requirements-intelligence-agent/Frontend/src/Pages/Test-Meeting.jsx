import {
  LiveKitRoom,
  VideoConference,
  RoomAudioRenderer,
} from "@livekit/components-react";

import "@livekit/components-styles";

import { useEffect, useState } from "react";

export default function TestMeeting() {
  const [connection, setConnection] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function getToken() {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/test/livekit-token"
        );

        if (!response.ok) {
          throw new Error("Failed to get LiveKit token");
        }

        const data = await response.json();

        setConnection(data);
      } catch (err) {
        setError(err.message);
      }
    }

    getToken();
  }, []);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!connection) {
    return <div>Connecting...</div>;
  }

  return (
    <div
      data-lk-theme="default"
      style={{
        height: "100vh",
      }}
    >
      <LiveKitRoom
        token={connection.token}
        serverUrl={connection.server_url}
        connect={true}
        audio={true}
        video={true}
      >
        <VideoConference />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}