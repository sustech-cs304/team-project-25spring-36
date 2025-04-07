// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { registerUserView } from './views/userView'; // Import the user view logic
import { registerUserCommands } from './commands/UserCommands'; // Import all commands
import { registerCourseCommands } from './commands/CourseCommands';
import { registerCourseView } from './views/CourseView'; // Import the course view logic

// This method is called when your extension is activated
// Your extension is activated along the vscode 
export function activate(context: vscode.ExtensionContext) {
  // Display the user view
  registerUserView(context);
  registerCourseView(context);
  registerUserCommands(context);
  registerCourseCommands(context);
  console.log(`Congratulations, your extension "intelligent-ide" is now active! Activation time: ${new Date().toLocaleTimeString()} `);
}

// This method is called when your extension is deactivated
export function deactivate() { }
