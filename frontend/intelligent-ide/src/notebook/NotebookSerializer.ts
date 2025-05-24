import * as vscode from 'vscode';

export class MyNotebookSerializer implements vscode.NotebookSerializer {
  async deserializeNotebook(content: Uint8Array, _token: vscode.CancellationToken): Promise<vscode.NotebookData> {
    const rawContent = new TextDecoder().decode(content);
    const parsed = JSON.parse(rawContent);

    const cells = parsed.cells.map((cell: any) => new vscode.NotebookCellData(
      cell.cell_type === 'code' ? vscode.NotebookCellKind.Code : vscode.NotebookCellKind.Markup,
      cell.source.join(''),
      cell.cell_type === 'code' ? cell.metadata.language : 'markdown'
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
      }))
    });

    return new TextEncoder().encode(rawContent);
  }
}