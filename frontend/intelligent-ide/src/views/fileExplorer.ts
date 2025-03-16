import * as vscode from 'vscode';
import { fileService, FileNode } from '../services/fileService';

export class FileExplorer implements vscode.TreeDataProvider<FileItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<FileItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private context: vscode.ExtensionContext) { }

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: FileItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: FileItem): Promise<FileItem[]> {
    try {
      const nodes = await fileService.getFileStructure(this.context);
      return nodes.map(node => new FileItem(node));
    } catch (error) {
      vscode.window.showErrorMessage(
        error instanceof Error
          ? error.message
          : typeof error === 'string'
            ? error
            : '未知错误'
      );
      return [];
    }
  }
}

class FileItem extends vscode.TreeItem {
  constructor(
    public readonly node: FileNode
  ) {
    super(
      node.name,
      node.type === 'directory'
        ? vscode.TreeItemCollapsibleState.Collapsed
        : vscode.TreeItemCollapsibleState.None
    );

    this.tooltip = node.path;
    this.iconPath = node.type === 'directory'
      ? vscode.ThemeIcon.Folder
      : vscode.ThemeIcon.File;
  }
}