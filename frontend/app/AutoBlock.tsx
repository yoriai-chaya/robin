"use client";
import AutoRunLoader from "./AutoRunLoader";
import { TreeNode, Action, FileInfo, ResponseInfo } from "./types";

interface AutoBlockProps {
  tree: TreeNode[];
  setTree: React.Dispatch<React.SetStateAction<TreeNode[]>>;
  dispatch: React.Dispatch<Action>;
  setFileInfo: React.Dispatch<React.SetStateAction<FileInfo[]>>;
  setResponseInfo: React.Dispatch<React.SetStateAction<ResponseInfo[]>>;
  nextStepIndex: number;
  setNextStepIndex: React.Dispatch<React.SetStateAction<number>>;
}
const AutoBlock: React.FC<AutoBlockProps> = ({
  tree,
  setTree,
  dispatch,
  setFileInfo,
  setResponseInfo,
  nextStepIndex,
  setNextStepIndex,
}) => {
  return (
    <div className="mx-4">
      <AutoRunLoader
        tree={tree}
        setTree={setTree}
        dispatch={dispatch}
        setFileInfo={setFileInfo}
        setResponseInfo={setResponseInfo}
        nextStepIndex={nextStepIndex}
        setNextStepIndex={setNextStepIndex}
      />
    </div>
  );
};

export default AutoBlock;
