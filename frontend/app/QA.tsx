"use client";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { SendHorizontal } from "lucide-react";
import StreamEvent from "./StreamEvent";
import { Action, FileInfo } from "./types";
import { ResponseInfo } from "./types";
import { formatDateTime } from "./util";
import { useState } from "react";
import { useSSEPrompt } from "./useSSEPrompt";

interface QAProps {
  status: string;
  index: number;
  dispatch: React.Dispatch<Action>;
  fileInfo: FileInfo;
  setResponseInfo: React.Dispatch<React.SetStateAction<ResponseInfo[]>>;
  responseInfo: ResponseInfo;
}

const QA = ({
  status,
  index,
  dispatch,
  fileInfo,
  setResponseInfo,
  responseInfo,
}: QAProps) => {
  const [errorMessage, setErrorMessage] = useState<string>("");
  const { sendPrompt } = useSSEPrompt({ dispatch, setResponseInfo });

  const handleSend = async () => {
    try {
      setErrorMessage("");
      const donePayload = await sendPrompt(fileInfo, index);
      console.log('"done": ', donePayload.status, donePayload.message);
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(String(err));
      }
    }
  };

  return (
    <div className="space-y-2 mb-4">
      {(status === "Loaded" || status === "Sended" || status === "Done") && (
        <div className="grid grid-cols-6 items-center">
          {/* --- filename row --- */}
          {/* column-A */}
          <div></div>
          {/* column-B */}
          <div className="text-muted-foreground text-app-label">fname:</div>
          {/* column-C,D,E */}
          <div className="col-span-3 text-app-info">{fileInfo.filename}</div>
          {/* column-F */}
          <div className="col-span-1 row-span-2">
            <Button
              onClick={handleSend}
              disabled={status === "Sended" || status === "Done"}
              variant="ghost"
            >
              <SendHorizontal className="w-4 h-4 mr-2 text-ctm-blue-500" />
            </Button>
          </div>
          {/* --- mtime row --- */}
          {/* column-A */}
          <div></div>
          {/* column-B */}
          <div className="text-muted-foreground text-app-label">mtime:</div>
          {/* column-C,D,E */}
          <div className="col-span-3 text-app-time text-muted-foreground">
            {formatDateTime(fileInfo.mtime)}
          </div>
          {/* column-F */}
          <div></div>

          {/* --- error message row --- */}
          {/* column-A */}
          <div></div>
          {/* column-B,C,D,E */}
          <div className="col-span-4 text-app-info">
            {errorMessage && (
              <div className="text-ctm-orange-400 mt-2">{errorMessage}</div>
            )}
          </div>
          {/* column-F */}
          <div></div>
        </div>
      )}
      {(status === "Sended" || status === "Done") && (
        <div className="grid grid-cols-6 items-center">
          {/* --- avatar row --- */}
          {/* column-A */}
          <div>
            <Avatar className="bg-yellow-100">
              <AvatarImage src="/assistant.png" />
              <AvatarFallback>As</AvatarFallback>
            </Avatar>
          </div>
          {/* column-B */}
          <span className="text-app-avatar">Assistant</span>
          {/* column-C,D,E,F */}
          <div className="col-span-4"></div>

          {/* --- StreamEvent rows --- */}
          <div className="col-span-6">
            <StreamEvent status={status} responseInfo={responseInfo} />
          </div>
        </div>
      )}
    </div>
  );
};

export default QA;
