import * as vscode from 'vscode';

export class MyNotebookSerializer implements vscode.NotebookSerializer {
  async deserializeNotebook(content: Uint8Array, _token: vscode.CancellationToken): Promise<vscode.NotebookData> {
    const rawContent = new TextDecoder().decode(content);
    const parsed = JSON.parse(rawContent);

    // 确保反序列化时正确处理元数据中的语言
    const cells = parsed.cells.map((cell: any) => new vscode.NotebookCellData(
      cell.cell_type === 'code' ? vscode.NotebookCellKind.Code : vscode.NotebookCellKind.Markup,
      cell.source.join(''),
      cell.cell_type === 'code' ? (cell.metadata.language || 'javascript') : 'markdown' // 默认语言为 JavaScript
    ));

    return new vscode.NotebookData(cells);
  }

  async serializeNotebook(data: vscode.NotebookData, _token: vscode.CancellationToken): Promise<Uint8Array> {
    const rawContent = JSON.stringify({
      cells: data.cells.map(cell => ({
        cell_type: cell.kind === vscode.NotebookCellKind.Code ? 'code' : 'markdown',
        source: [cell.value],
        metadata: {
          language: cell.languageId
        }
      })),
      metadata: {
        kernelspec: {
          display_name: 'My Notebook Controller',
          language: 'javascript', // 默认语言
          name: 'my-notebook-controller' // 必须与控制器 ID 匹配
        }
      }
    });

    return new TextEncoder().encode(rawContent);
  }
}