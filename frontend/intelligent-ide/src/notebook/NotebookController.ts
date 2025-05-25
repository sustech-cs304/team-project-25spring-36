import * as vscode from 'vscode';
import { exec } from 'child_process';

export class MyNotebookController {
  private readonly controller: vscode.NotebookController;

  constructor() {
    this.controller = vscode.notebooks.createNotebookController(
      'my-notebook-controller', // Controller ID
      'my-notebook', // Notebook type
      'My Notebook Controller'
    );

    this.controller.supportedLanguages = ['javascript', 'python', 'java', 'c', 'markdown']; // 确保包含 java 和 c
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
      try {
        const result = new Function(code)(); // 使用 Function 构造函数代替 eval
        return result;
      } catch (error) {
        return `JavaScript Error: ${(error as Error).message}`;
      }
    } else if (language === 'python') {
      return this.runPythonCode(code);
    } else if (language === 'java') {
      return this.runJavaCode(code); // 确保调用正确的方法
    } else if (language === 'c') {
      return this.runCCode(code); // 确保调用正确的方法
    }
    return 'Unsupported language';
  }

  private runPythonCode(code: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const process = exec('python', (error, stdout, stderr) => {
        if (error) {
          reject(`Python Error: ${stderr || error.message}`);
        } else {
          resolve(stdout.trim());
        }
      });

      if (process.stdin) {
        process.stdin.write(code);
        process.stdin.end();
      }
    });
  }

  private runJavaCode(code: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const tempFile = `${__dirname}/Temp.java`;
      const fs = require('fs');
      fs.writeFileSync(tempFile, code);

      exec(`javac ${tempFile} && java -cp ${__dirname} Temp`, (error, stdout, stderr) => {
        fs.unlinkSync(tempFile); // Clean up the temp file
        const classFile = `${__dirname}/Temp.class`;
        if (fs.existsSync(classFile)) {
          fs.unlinkSync(classFile); // Clean up the compiled class file
        }
        if (error) {
          reject(`Java Error: ${stderr || error.message}`);
        } else {
          resolve(stdout.trim());
        }
      });
    });
  }

  private runCCode(code: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const tempFile = `${__dirname}/temp.c`;
      const outputFile = `${__dirname}/temp.exe`;
      const fs = require('fs');
      fs.writeFileSync(tempFile, code);

      exec(`gcc ${tempFile} -o ${outputFile} && ${outputFile}`, (error, stdout, stderr) => {
        fs.unlinkSync(tempFile); // Clean up the temp file
        if (fs.existsSync(outputFile)) {
          fs.unlinkSync(outputFile); // Clean up the compiled file
        }
        if (error) {
          reject(`C Error: ${stderr || error.message}`);
        } else {
          resolve(stdout.trim());
        }
      });
    });
  }
}