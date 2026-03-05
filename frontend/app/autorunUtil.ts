import { TreeNode } from "./types";

export type AutoFileItem = {
  key: string;
  name: string;
  content: string;
  mtime: Date;
};

export function flattenTree(
  nodes: TreeNode[],
  parentPath = ""
): AutoFileItem[] {
  const out: AutoFileItem[] = [];

  for (const node of nodes) {
    if (node.type === "directory") {
      const nextParent = `${parentPath}${node.name}`;
      out.push(...flattenTree(node.children, nextParent));
      continue;
    }
    // file
    const key = `${parentPath}${node.name}`;
    out.push({
      key,
      name: node.name,
      content: node.data.content,
      mtime: new Date(node.data.mtime),
    });
  }
  return out;
}
