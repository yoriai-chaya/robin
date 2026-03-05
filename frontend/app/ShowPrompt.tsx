import { Card } from "@/components/ui/card";
import { FileInfo } from "./types";
import Markdown from "./Markdown";

interface ShowPromptProps {
  status: string;
  index: number;
  fileInfo: FileInfo[];
}

const ShowPrompt = ({ status, index, fileInfo }: ShowPromptProps) => {
  return (
    <div>
      {(status === "Loaded" || status === "Sended" || status === "Done") && (
        <div>
          <p className="text-app-info font-semibold my-1">Request</p>
          <Card className="p-4 bg-slate-100 rounded-md">
            <div className="flex flex-wrap">
              <Markdown markdown={fileInfo[index].content} />
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ShowPrompt;
