"use client";
import { useRef, useCallback } from "react";
import {
  Action,
  FileInfo,
  PromptRequest,
  ResponseInfo,
  StreamResponse,
  EventTypes,
} from "./types";

interface UseSSEPromptProps {
  dispatch: React.Dispatch<Action>;
  setResponseInfo: React.Dispatch<React.SetStateAction<ResponseInfo[]>>;
}

type DonePayload = Extract<StreamResponse, { event: "done" }>["payload"];

export const useSSEPrompt = ({
  dispatch,
  setResponseInfo,
}: UseSSEPromptProps) => {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
  const esRef = useRef<EventSource | null>(null);

  // setEvent
  const setEvent = useCallback(
    (sres: StreamResponse, index: number) => {
      console.log("setEvent called");
      setResponseInfo((prev) => {
        const updated = [...prev];
        const prevEvents = updated[index]?.r_event ?? [];
        updated[index] = {
          r_event: [...prevEvents, { s_res: sres, r_time: new Date() }],
        };
        return updated;
      });
    },
    [setResponseInfo],
  );

  // handleGenericEvent
  const handleGenericEvent = useCallback(
    (
      type: (typeof EventTypes)[keyof typeof EventTypes],
      e: Event,
      index: number,
    ) => {
      console.log(`- ${type} event -`);
      const data = JSON.parse((e as MessageEvent).data);
      console.log(`data: ${JSON.stringify(data, null, 2)}`);
      const sres: StreamResponse = {
        event: type as StreamResponse["event"],
        payload: data,
      };
      setEvent(sres, index);
    },
    [setEvent],
  );

  // sendPrompt
  const sendPrompt = useCallback(
    async (fileInfo: FileInfo, index: number) => {
      console.log("sendPrompt called");
      if (!API_BASE) {
        return Promise.reject(new Error("NEXT_PUBLIC_API_BASE_URL is not set"));
      }
      if (esRef.current) {
        // Prevent duplicate
        console.log("prevent duplicate");
        esRef.current.close();
        esRef.current = null;
      }

      try {
        // Create Session
        const requestBody: PromptRequest = { prompt: fileInfo.content };
        const res = await fetch(`${API_BASE}/main`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        });
        if (!res.ok) throw new Error(`create session failed: ${res.status}`);

        const { session_id } = await res.json();
        if (!session_id) throw new Error("no session_id");
        console.log(`session_id: ${session_id}`);

        // Starting subscribing to SSE
        const url = `${API_BASE}/main/stream/${session_id}`;
        console.log("new EventSource");
        const es = new EventSource(url, { withCredentials: false });
        console.log(`es : ${es}`);
        esRef.current = es;

        // Returns a Promise that resolves when the "done" event is received
        return await new Promise<DonePayload>((resolve, reject) => {
          let settled = false;

          const safeResolve = (payload: DonePayload) => {
            if (settled) return;
            settled = true;
            es.close();
            esRef.current = null;
            resolve(payload);
          };
          const safeReject = (err: Error) => {
            if (settled) return;
            settled = true;
            es.close();
            esRef.current = null;
            reject(err);
          };

          // Listen "started" (special handling)
          es.addEventListener(EventTypes.STARTED, (e) => {
            try {
              console.log("- started event -");
              const data = JSON.parse((e as MessageEvent).data);
              console.log(`data: ${JSON.stringify(data, null, 2)}`);
              console.log("dispatch send_prompt");
              dispatch({ type: "SEND_PROMPT", index });
              const sres: StreamResponse = {
                event: EventTypes.STARTED,
                payload: data,
              };
              setResponseInfo((prev) => {
                const updated = [...prev];
                updated[index] = {
                  r_event: [{ s_res: sres, r_time: new Date() }],
                };
                return updated;
              });
            } catch (err) {
              safeReject(err instanceof Error ? err : new Error(String(err)));
            }
          });

          // Listen "done" (special handling)
          es.addEventListener(EventTypes.DONE, (e) => {
            try {
              console.log("- done event -");
              const data = JSON.parse((e as MessageEvent).data);
              console.log(`data: ${JSON.stringify(data, null, 2)}`);
              const sres: StreamResponse = {
                event: EventTypes.DONE,
                payload: data,
              };
              setEvent(sres, index);
              dispatch({ type: "DONE", index });
              safeResolve(data);
            } catch (err) {
              safeReject(err instanceof Error ? err : new Error(String(err)));
            }
          });

          // Other events (common handling)
          const commonEventTypes = Object.values(EventTypes).filter(
            (type) => type !== EventTypes.STARTED && type !== EventTypes.DONE,
          );
          commonEventTypes.forEach((type) => {
            es.addEventListener(type, (e) => {
              try {
                handleGenericEvent(type, e, index);
              } catch (err) {
                safeReject(err instanceof Error ? err : new Error(String(err)));
              }
            });
          });

          // SSE connection error
          es.onerror = () => {
            safeReject(new Error("SSE connection error"));
          };
        });
      } catch (error) {
        console.log("Error sending: ", error);
        let message = "Failed to connect to server";
        if (error instanceof TypeError && error.message === "Failed to fetch") {
          message = "Could not connect to backend server";
        } else if (error instanceof Error) {
          message = error.message;
        }
        return Promise.reject(new Error(message));
      }
    },
    [API_BASE, dispatch, handleGenericEvent, setEvent, setResponseInfo],
  );

  return { sendPrompt };
};
