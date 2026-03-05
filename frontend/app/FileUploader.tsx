"use client";
import { ChangeEvent, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Action, FileInfo } from "./types";

interface FileUploaderProps {
  status: string;
  index: number;
  dispatch: React.Dispatch<Action>;
  setFileInfo: React.Dispatch<React.SetStateAction<FileInfo[]>>;
}

const FileUploader = ({
  status,
  index,
  dispatch,
  setFileInfo,
}: FileUploaderProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    console.log(`Selected file: ${file.name}`);
    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      const filename = file.name;
      const mtime = new Date(file.lastModified);

      setFileInfo((prev) => {
        const updated = [...prev];
        updated[index] = { filename, content, mtime };
        return updated;
      });
      dispatch({ type: "LOAD_FILE", index });
    };
    reader.readAsText(file);
  };

  const handleSelectClick = () => {
    fileInputRef.current?.click();
  };
  return (
    <>
      {/* column-C,D,E */}
      {(status === "Unloaded" || status === "Loaded") && (
        <div className="col-span-3">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            className="bg-ctm-blue-500 hover:bg-ctm-blue-600"
            type="button"
            onClick={handleSelectClick}
          >
            Prompt File
          </Button>
        </div>
      )}
      {/* column-F */}
      <div></div>
    </>
  );
};

export default FileUploader;
