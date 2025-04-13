import * as vscode from 'vscode';

export class MyNotebookSerializer implements vscode.NotebookSerializer {
  async deserializeNotebook(content: Uint8Array, _token: vscode.CancellationToken): Promise<vscode.NotebookData> {
    const rawContent = new TextDecoder().decode(content);
    const cells = JSON.parse(rawContent).cells.map((cell: any) => new vscode.NotebookCellData(
      cell.kind === 'code' ? vscode.NotebookCellKind.Code : vscode.NotebookCellKind.Markup,
      cell.value,
      cell.language
    ));
    return new vscode.NotebookData(cells);
  }

  async serializeNotebook(data: vscode.NotebookData, _token: vscode.CancellationToken): Promise<Uint8Array> {
    const rawContent = JSON.stringify({
      cells: data.cells.map(cell => ({
        kind: cell.kind === vscode.NotebookCellKind.Code ? 'code' : 'markup',
        value: cell.value,
        language: cell.languageId
      }))
    });
    return new TextEncoder().encode(rawContent);
  }
}