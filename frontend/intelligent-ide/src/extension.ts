// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { registerLoginCommand } from './commands/loginCommand';
import { registerRegisterCommand } from './commands/registerCommand';
import { registerUpdateCommand } from './commands/updateCommand';
import { FileExplorer } from './views/fileExplorer';
import { displayUserView } from './views/userView'; // Import the user view logic
import { registerLogoutCommand } from './commands/logoutCommand';

// This method is called when your extension is activated
// Your extension is activated along the vscode
export function activate(context: vscode.ExtensionContext) {
  // Display the user view
  displayUserView(context);

  //register all commands
  registerLoginCommand(context);
  registerRegisterCommand(context);
  registerUpdateCommand(context);
  registerLogoutCommand(context);

  const fileExplorer = new FileExplorer(context);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('intelligent-ide-fileView', fileExplorer)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('intelligent-ide.refreshFiles',
      () => fileExplorer.refresh()
    )
  );

  // Use the console to output diagnostic information (console.log) and errors (console.error)
  console.log('Congratulations, your extension "intelligent-ide" is now active!');
}

// This method is called when your extension is deactivated
export function deactivate() { }
