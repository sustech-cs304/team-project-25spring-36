// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { initializeViewManager, disposeViews } from './views/viewManager';
import { CommandManager } from './commands/CommandManager';

// This method is called when your extension is activated
// Your extension is activated along the vscode 
export function activate(context: vscode.ExtensionContext) {

  // Initialize view manager first - this registers all views
  const courseTreeDataProvider = initializeViewManager(context);

  // Initialize command manager - this registers all commands
  const commandManager = new CommandManager(context, courseTreeDataProvider);
  commandManager.registerAllCommands();

  console.log(`Intelligent IDE extension is now active!`);
}

// This method is called when your extension is deactivated
export function deactivate() {
  // Any cleanup code would go here
  disposeViews();
}
