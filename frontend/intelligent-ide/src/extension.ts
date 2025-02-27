// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import { register } from 'module';
import * as vscode from 'vscode';
import { registerLoginCommand } from './commands/loginCommand';
import { registerRegisterCommand } from './commands/registerCommand';
import { registerUpdateCommand } from './commands/updateComman';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {


	//register all commands
	registerLoginCommand(context);
	registerRegisterCommand(context);
	registerUpdateCommand(context);
	
	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "intelligent-ide" is now active!');

}

// This method is called when your extension is deactivated
export function deactivate() {}
