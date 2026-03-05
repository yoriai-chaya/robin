"use client";
import {
  TreeNode,
  Emoji,
  AutoRunFileStatusMap,
  AutoRunFileStatus,
} from "./types";
import { formatDateTime } from "./util";

interface TreeViewProps {
  nodes: TreeNode[];
  depth?: number;
  pathPrefix?: string;
  fileStatusByKey?: AutoRunFileStatusMap;
}

const statusToEmoji = (st?: AutoRunFileStatus) => {
  switch (st) {
    case "running":
      return Emoji.GREEN_CIRCLE;
    case "success":
      return Emoji.BLUE_CIRCLE;
    case "failed":
      return Emoji.RED_CIRCLE;
    case "skipped":
      return Emoji.YELLOW_CIRCLE;
    default:
      return Emoji.WHITE_CIRCLE;
  }
};

const TreeView: React.FC<TreeViewProps> = ({
  nodes,
  depth = 0,
  pathPrefix = "",
  fileStatusByKey,
}) => {
  const indentStyle = { marginLeft: `${depth * 12}px` };
  return (
    <ul className="text-sm">
      {nodes.map((node, index) => {
        if (node.type === "directory") {
          const nextPrefix = `${pathPrefix}${node.name}`;
          return (
            <li key={`${nextPrefix}-${index}`} style={indentStyle}>
              <div className="font-medium">- {node.name}</div>
              <TreeView
                nodes={node.children}
                depth={depth + 1}
                pathPrefix={nextPrefix}
                fileStatusByKey={fileStatusByKey}
              />
            </li>
          );
        }

        // file
        const fileKey = `${pathPrefix}${node.name}`;
        const emoji = statusToEmoji(fileStatusByKey?.[fileKey]);
        return (
          <li key={`${node.name}-${index}`} style={indentStyle}>
            <div>
              {emoji} {node.name}
            </div>
            <div className="ml-2 text-xs text-muted-foreground">
              {formatDateTime(new Date(node.data.mtime))}
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export default TreeView;
