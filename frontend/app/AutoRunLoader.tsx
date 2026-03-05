"use client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Checkbox } from "@/components/ui/checkbox";
import {
  TreeNode,
  Action,
  FileInfo,
  ResponseInfo,
  AutoRunFileStatusMap,
  ResponseStatus,
  AutoRunState,
  StreamResponse,
} from "./types";
import { useState, useMemo, useRef, useEffect } from "react";
import { flattenTree } from "./autorunUtil";
import TreeView from "./TreeView";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useSSEPrompt } from "./useSSEPrompt";

interface AutoRunLoaderProps {
  tree: TreeNode[];
  setTree: React.Dispatch<React.SetStateAction<TreeNode[]>>;
  dispatch: React.Dispatch<Action>;
  setFileInfo: React.Dispatch<React.SetStateAction<FileInfo[]>>;
  setResponseInfo: React.Dispatch<React.SetStateAction<ResponseInfo[]>>;
  nextStepIndex: number;
  setNextStepIndex: React.Dispatch<React.SetStateAction<number>>;
}

const AutoRunLoader: React.FC<AutoRunLoaderProps> = ({
  tree,
  setTree,
  dispatch,
  setFileInfo,
  setResponseInfo,
  nextStepIndex,
  setNextStepIndex,
}) => {
  const [autorunId, setAutorunId] = useState("");
  const [inputAutorunId, setInputAutorunId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // file status (tree view)
  const [fileStatusByKey, setFileStatusKey] = useState<AutoRunFileStatusMap>(
    {},
  );
  // auto-run status
  const [autoRunState, setAutoRunState] = useState<AutoRunState>("idle");
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [skipOnCont, setSkipOnCont] = useState(false);
  const [stopRequested, setStopRequested] = useState(false);
  // for future : currentStepIndex
  const [, setCurrentStepIndex] = useState<number>(-1);

  const pauseRequestRef = useRef(false);

  const { sendPrompt } = useSSEPrompt({ dispatch, setResponseInfo });
  const files = useMemo(() => flattenTree(tree), [tree]);
  const autoRunStateTextClass = useMemo(() => {
    switch (autoRunState) {
      case "pause":
        return "text-ctm-yellow-200";
      case "finished":
        return "text-ctm-blue-500";
      case "failed":
        return "text-ctm-orange-400";
      default:
        return "";
    }
  }, [autoRunState]);

  const initialFileInfo: FileInfo[] = [
    { filename: "", content: "", mtime: new Date(0) },
  ];
  const initialResponseInfo: ResponseInfo[] = [];

  // for "Skip" Checkbox control
  useEffect(() => {
    if (
      autoRunState === "idle" ||
      autoRunState === "running" ||
      autoRunState === "finished"
    ) {
      setSkipOnCont(false);
    }
  }, [autoRunState]);

  const buildUserMessage = (status: number): string => {
    switch (status) {
      case 404:
        return "AutoRunID not found";
      case 422:
        return "Directory structure is too deep";
      case 500:
        return "Internal Error";
      default:
        return "Failed to load file list";
    }
  };

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    setErrorDetail(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
      const params = new URLSearchParams({ autorun_id: inputAutorunId });
      const res = await fetch(
        `${API_BASE}/autorun/filelist?${params.toString()}`,
        {
          method: "GET",
        },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(buildUserMessage(res.status));
        setErrorDetail(body?.detail ?? null);
        return;
      }
      const data: TreeNode[] = await res.json();
      console.log("TreeNode data: ", data);
      setTree(data);
      setAutorunId(inputAutorunId);

      const f = flattenTree(data);
      const initMap: AutoRunFileStatusMap = {};
      for (const item of f) initMap[item.key] = "pending";
      setFileStatusKey(initMap);

      // Left/Right Panel initialize
      dispatch({ type: "RESET" });
      setFileInfo(initialFileInfo);
      setResponseInfo(initialResponseInfo);
      setNextStepIndex(0);

      // auto-run internal state reset
      setAutoRunState("idle");
      setCurrentIndex(-1);
      pauseRequestRef.current = false;
      setStopRequested(false);
    } catch (e) {
      setError("Network Error");
      setErrorDetail(String(e));
    } finally {
      setStopRequested(false);
      setLoading(false);
    }
  };

  const ensureFileInfoSlot = (i: number) => {
    setFileInfo((prev) => {
      const next = [...prev];
      while (next.length <= i) {
        next.push({ filename: "", content: "", mtime: new Date(0) });
      }
      return next;
    });
  };
  const ensureResponseInfoSlot = (i: number) => {
    setResponseInfo((prev) => {
      const next = [...prev];
      while (next.length <= i) {
        next.push({ r_event: [] });
      }
      return next;
    });
  };

  // for error (sendPrompt catch) : pseudo system_error event
  const appendSystemErrorEvent = (
    i: number,
    message: string,
    detail: string,
  ) => {
    const sres: StreamResponse = {
      event: "system_error",
      payload: { error: message, detail },
    };
    setResponseInfo((prev) => {
      const updated = [...prev];
      const prevEvents = updated[i]?.r_event ?? [];
      updated[i] = {
        r_event: [...prevEvents, { s_res: sres, r_time: new Date() }],
      };
      return updated;
    });
  };

  const runFrom = async (startFileIndex: number) => {
    if (files.length === 0) {
      setError("No files");
      setErrorDetail("Tree has no files");
      return;
    }
    if (startFileIndex >= files.length) {
      setAutoRunState("finished");
      return;
    }
    setAutoRunState("running");
    pauseRequestRef.current = false;
    setStopRequested(false);

    let stepIndex = nextStepIndex;
    for (
      let fileIndex = startFileIndex;
      fileIndex < files.length;
      fileIndex++
    ) {
      const f = files[fileIndex];
      setCurrentIndex(fileIndex);
      setCurrentStepIndex(stepIndex);

      setFileStatusKey((prev) => ({ ...prev, [f.key]: "running" }));

      ensureFileInfoSlot(stepIndex);
      ensureResponseInfoSlot(stepIndex);

      setFileInfo((prev) => {
        const next = [...prev];
        next[stepIndex] = {
          filename: f.name,
          content: f.content,
          mtime: f.mtime,
        };
        return next;
      });
      dispatch({ type: "LOAD_FILE", index: stepIndex });

      try {
        const done = await sendPrompt(
          { filename: f.name, content: f.content, mtime: f.mtime },
          stepIndex,
        );
        stepIndex++;
        setNextStepIndex(stepIndex);

        if (done.status === ResponseStatus.COMPLETED) {
          setFileStatusKey((prev) => ({ ...prev, [f.key]: "success" }));
        } else {
          setFileStatusKey((prev) => ({ ...prev, [f.key]: "failed" }));
          setAutoRunState("failed");
          setStopRequested(false);
          return;
        }
        // If "Stop" button is pressed, pause after receiving "done" event
        if (pauseRequestRef.current) {
          setAutoRunState("pause");
          setStopRequested(false);
          return;
        }
      } catch (e) {
        // Force "done" and proceed to the next step
        const msg = e instanceof Error ? e.message : String(e);
        appendSystemErrorEvent(stepIndex, "Client error", msg);
        dispatch({ type: "DONE", index: stepIndex });
        stepIndex++;
        setNextStepIndex(stepIndex);

        setFileStatusKey((prev) => ({ ...prev, [f.key]: "failed" }));
        setAutoRunState("failed");
        setStopRequested(false);
        setError("Run failed");
        setErrorDetail(msg);
        return;
      }
    }
    setAutoRunState("finished");
    setStopRequested(false);
  };

  const handleRun = async () => {
    setError(null);
    setErrorDetail(null);
    if (autoRunState === "running") return;
    await runFrom(0);
  };

  const handlePause = async () => {
    if (autoRunState !== "running") return;
    pauseRequestRef.current = true;
    setStopRequested(true);
  };

  const handleCont = async () => {
    setError(null);
    setErrorDetail(null);

    if (files.length === 0) return;
    if (!(autoRunState === "pause" || autoRunState === "failed")) return;

    const start = skipOnCont ? currentIndex + 1 : currentIndex;

    if (
      skipOnCont &&
      autoRunState === "failed" &&
      currentIndex >= 0 &&
      currentIndex < files.length
    ) {
      const failedKey = files[currentIndex].key;
      setFileStatusKey((prev) => ({ ...prev, [failedKey]: "skipped" }));
    }

    await runFrom(start);
  };

  // Button condition
  const hasAutorunId = inputAutorunId.trim().length > 0;
  const hasTree = tree.length > 0;
  const canLoad = !loading && hasAutorunId && autoRunState !== "running";
  const canRun = !loading && hasTree && autoRunState === "idle";
  const canPause = autoRunState === "running" && !stopRequested;
  const canCont =
    !loading && (autoRunState === "pause" || autoRunState === "failed");
  const canSkip =
    !loading && (autoRunState === "pause" || autoRunState === "failed");

  return (
    <div>
      <Label className="mt-1 cols-span-2 font-midium">Autorun-ID: </Label>
      <Input
        id="autorun-id"
        placeholder="dir, dir/subdir"
        value={inputAutorunId}
        onChange={(e) => setInputAutorunId(e.target.value)}
        className="border-0 border-b rounded-none focus-visible:ring-0 h-6 mt-1"
      />
      {/* === Controls === */}
      <div className="flex flex-col space-y-0">
        {/* Line-1: Load / Run */}
        <div className="flex items-center">
          <Button
            size="sm"
            onClick={handleLoad}
            disabled={!canLoad}
            variant="ghost"
            className="
          shrink-0
          text-ctm-blue-500
          hover:text-ctm-blue-600
          hover:bg-transparent 
        "
          >
            {loading ? "Loading..." : "Load"}
          </Button>

          <Button
            size="sm"
            onClick={handleRun}
            disabled={!canRun}
            variant="ghost"
            className="ml-2 shrink-0 text-ctm-blue-500 hover:text-ctm-blue-600 hover:bg-transparent"
          >
            Run
          </Button>
        </div>

        {/* Line-2: Pause / Cont / Skip */}
        <div className="flex items-center -mt-2">
          <Button
            size="sm"
            onClick={handlePause}
            disabled={!canPause}
            variant="ghost"
            className="shrink-0 text-ctm-blue-500 hover:text-ctm-blue-600 hover:bg-transparent"
          >
            Pause
          </Button>
          <Button
            size="sm"
            onClick={handleCont}
            disabled={!canCont}
            variant="ghost"
            className="shrink-0 text-ctm-blue-500 hover:text-ctm-blue-600 hover:bg-transparent"
          >
            Cont
          </Button>
          <div className="flex items-center gap-1">
            <Checkbox
              id="skip-on-cont"
              checked={skipOnCont}
              onCheckedChange={(v) => setSkipOnCont(v === true)}
              disabled={!canSkip}
            />
            <Label htmlFor="skip-on-cont" className="text-xs">
              Skip
            </Label>
          </div>
        </div>

        {/* Line-2': When pause clicked, inidcate stopping... */}
        {stopRequested && (
          <div className="flex items-center gap-2 pl-1 text-xs text-muted-foreground">
            <Spinner />
            <span className="text-ctm-yellow-200">Stopping...</span>
          </div>
        )}

        {/* Line-3: state / index*/}
        {tree.length > 0 && (
          <div className="ml-3 text-xs text-muted-foreground">
            <span className={`font-medium ${autoRunStateTextClass}`}>
              {autoRunState}
            </span>
            {files.length > 0 && (
              <span className={`${autoRunStateTextClass}`}>
                ,{" "}
                <span>
                  {currentIndex >= 0
                    ? `${currentIndex + 1}/${files.length}`
                    : "-"}
                </span>
              </span>
            )}
          </div>
        )}

        {/* Line-4: error */}
        {error && (
          <div className="text-xs text-ctm-orange-400">
            <div>{error}</div>
            {errorDetail && (
              <details className="cursor-pointer">
                <summary className="text-xs">detail</summary>
                <p className="text-xs">{errorDetail}</p>
              </details>
            )}
          </div>
        )}
      </div>

      {tree.length > 0 && (
        <div className="mt-4 border-t pt-2">
          <div className="font-semibold mb-1">{autorunId}</div>
          <ScrollArea className="h-[60vh] pr-2">
            <TreeView nodes={tree} fileStatusByKey={fileStatusByKey} />
          </ScrollArea>
        </div>
      )}
    </div>
  );
};

export default AutoRunLoader;
