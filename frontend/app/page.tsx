"use client";
import { useEffect, useReducer, useState, useRef } from "react";
import { Separator } from "@/components/ui/separator";
import FileUploader from "./FileUploader";
import { ScrollArea } from "@/components/ui/scroll-area";
import UserAvatar from "./UserAvatar";
import QA from "./QA";
import ShowPrompt from "./ShowPrompt";
import StreamDetail from "./StreamDetail";
import Header from "./Header";
import { FileInfo, ResponseInfo, Mode, TreeNode } from "./types";
import { reducer } from "./reducer";
import AutoBlock from "./AutoBlock";
import { initialState } from "./state";

const initialFileInfo: FileInfo[] = [
  { filename: "", content: "", mtime: new Date(0) },
];
const initialResponseInfo: ResponseInfo[] = [];

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [nextStepIndex, setNextStepIndex] = useState(0);
  const [fileInfo, setFileInfo] = useState<FileInfo[]>(initialFileInfo);
  const [responseInfo, setResponseInfo] =
    useState<ResponseInfo[]>(initialResponseInfo);
  const [mode, setMode] = useState<Mode>("Manual");
  const [tree, setTree] = useState<TreeNode[]>([]);
  useEffect(() => {
    console.log("fileInfo updated: ", fileInfo);
    scrollRightPanel();
  }, [fileInfo]);
  useEffect(() => {
    console.log("state updated: ", state);
    scrollLeftPanel();
  }, [state]);
  useEffect(() => {
    console.log("responseInfo updated: ", responseInfo);
    scrollLeftPanel();
    scrollRightPanel();
  }, [responseInfo]);
  useEffect(() => {
    setFileInfo((prev) => {
      if (prev.length >= state.steps.length) return prev;
      return [...prev, { filename: "", content: "", mtime: new Date(0) }];
    });
  }, [state.steps.length]);
  useEffect(() => {
    const next = Math.max(0, state.steps.length - 1);
    setNextStepIndex(next);
  }, [state.steps.length]);

  const rightPanel = useRef<HTMLDivElement>(null);
  const leftPanel = useRef<HTMLDivElement>(null);

  const scrollRightPanel = () => {
    if (rightPanel.current) {
      rightPanel.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  };
  const scrollLeftPanel = () => {
    if (leftPanel.current) {
      leftPanel.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <Header mode={mode} setMode={setMode} />

      {/* Main Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Side-Panel */}
        <div className="w-3/15 p-4 border-r space-y-4">
          {mode === "Auto" && (
            <div>
              <AutoBlock
                tree={tree}
                setTree={setTree}
                dispatch={dispatch}
                setFileInfo={setFileInfo}
                setResponseInfo={setResponseInfo}
                nextStepIndex={nextStepIndex}
                setNextStepIndex={setNextStepIndex}
              />
            </div>
          )}
        </div>
        {/* Left-Panel */}
        <ScrollArea className="w-6/15 p-4 border-r space-y-4">
          <div ref={leftPanel}>
            {state.steps.map((step, index) => (
              <div key={index}>
                <p className="text-app-step my-2">
                  Step {index + 1} - Status: {step.status}
                </p>
                <div className="grid grid-cols-6 items-center gap-2 mb-2">
                  {/* column-A,B */}
                  <UserAvatar />
                  {/* column-C,D,E,F */}
                  {mode === "Manual" && (
                    <FileUploader
                      index={index}
                      status={step.status}
                      dispatch={dispatch}
                      setFileInfo={setFileInfo}
                    />
                  )}
                </div>
                <QA
                  index={index}
                  status={step.status}
                  dispatch={dispatch}
                  fileInfo={fileInfo[index]}
                  setResponseInfo={setResponseInfo}
                  responseInfo={responseInfo[index]}
                />
                <Separator />
              </div>
            ))}
          </div>
        </ScrollArea>
        {/* Right-Panel */}
        <ScrollArea className="w-6/15 p-4 border-r space-y-4">
          <div ref={rightPanel}>
            {state.steps.map((step, index) => (
              <div key={index}>
                <p className="text-app-step my-2">
                  Step {index + 1} - Status: {step.status}
                </p>
                <ShowPrompt
                  index={index}
                  status={step.status}
                  fileInfo={fileInfo}
                />
                <StreamDetail
                  status={step.status}
                  responseInfo={responseInfo[index]}
                />
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
