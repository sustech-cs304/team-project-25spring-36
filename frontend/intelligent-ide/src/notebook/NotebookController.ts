import * as vscode from 'vscode';

export class MyNotebookController {
  private readonly controller: vscode.NotebookController;

  constructor() {
    this.controller = vscode.notebooks.createNotebookController(
      'my-notebook-controller',
      'my-notebook',
      'My Notebook Controller'
    );

    this.controller.supportedLanguages = ['javascript', 'python', 'markdown'];
    this.controller.executeHandler = this.execute.bind(this);
  }

  private async execute(cells: vscode.NotebookCell[], notebook: vscode.NotebookDocument, controller: vscode.NotebookController) {
    for (const cell of cells) {
      const execution = controller.createNotebookCellExecution(cell);
      execution.start(Date.now());
      try {
        if (cell.kind === vscode.NotebookCellKind.Code) {
          const result = await this.runCode(cell.document.getText(), cell.document.languageId);
          execution.replaceOutput([new vscode.NotebookCellOutput([
            vscode.NotebookCellOutputItem.text(result)
          ])]);
        } else {
          execution.replaceOutput([new vscode.NotebookCellOutput([
            vscode.NotebookCellOutputItem.text('Markdown rendered')
          ])]);
        }
        execution.end(true);
      } catch (error) {
        execution.replaceOutput([new vscode.NotebookCellOutput([
          vscode.NotebookCellOutputItem.error(error as Error)
        ])]);
        execution.end(false);
      }
    }
  }

  private async runCode(code: string, language: string): Promise<string> {
    if (language === 'javascript') {
      return eval(code); // For simplicity, use eval for JavaScript
    } else if (language === 'python') {
      // Call a Python execution service (e.g., via REST API)
      return 'Python execution not implemented';
    }
    return 'Unsupported language';
  }
}