// import * as vscode from 'vscode';
// import * as fs from 'fs';
// import * as path from 'path';
// import { MyNotebookController } from '../notebook/NotebookController';
// import { MyNotebookSerializer } from '../notebook/NotebookSerializer';

// const showdown = require('showdown');
// const converter = new showdown.Converter();
// const PDFDocument = require('pdfkit');

// export class NotebookView {
//   private readonly notebookType = 'my-notebook';
//   private readonly notebookFiles: vscode.Uri[] = []; // Stores the URIs of notebook files
//   private readonly treeDataProvider: NotebookExplorer;

//   // Default path for notebooks
//   private readonly defaultNotebookPath = "C:\\Users\\Lenovo\\Desktop";

//   constructor(context: vscode.ExtensionContext) {
//     this.treeDataProvider = this.registerNotebookExplorer(context);
//     this.registerNotebookSerializer(context);
//     this.registerNotebookController();
//     this.registerCommands(context);
//     this.enableAutoSave(context);
//     this.loadNotebooksFromDefaultPath();
//   }

//   private registerNotebookSerializer(context: vscode.ExtensionContext) {
//     context.subscriptions.push(
//       vscode.workspace.registerNotebookSerializer(
//         this.notebookType,
//         new MyNotebookSerializer()
//       )
//     );
//     console.log('Notebook serializer registered.');
//   }

//   private registerNotebookController() {
//     new MyNotebookController();
//     console.log('Notebook controller registered.');
//   }

//   private registerNotebookExplorer(context: vscode.ExtensionContext): NotebookExplorer {
//     const treeDataProvider = new NotebookExplorer(this.notebookFiles);
//     vscode.window.registerTreeDataProvider('notebookExplorer', treeDataProvider);
//     return treeDataProvider;
//   }

//   private registerCommands(context: vscode.ExtensionContext) {
//     // Register "New Notebook" command
//     const newNotebookCommand = vscode.commands.registerCommand('intelligent-ide.notebook.new', async () => {
//       const uri = await vscode.window.showSaveDialog({
//         filters: { 'My Notebook': ['ipynb'] },
//         saveLabel: 'Create Notebook',
//         defaultUri: vscode.Uri.file(path.join(this.defaultNotebookPath, 'Untitled.ipynb'))
//       });

//       if (!uri) {
//         vscode.window.showInformationMessage('Notebook creation cancelled.');
//         return;
//       }

//       const initialContent = JSON.stringify({ cells: [] }, null, 2);
//       await vscode.workspace.fs.writeFile(uri, Buffer.from(initialContent, 'utf8'));

//       // Add the new notebook to the Notebook Explorer
//       this.notebookFiles.push(uri);
//       this.treeDataProvider.refresh();

//       vscode.window.showInformationMessage(`Notebook created: ${uri.fsPath}`);
//     });

//     // Register "Delete Notebook" command
//     const deleteNotebookCommand = vscode.commands.registerCommand('intelligent-ide.notebook.delete', async (item: vscode.TreeItem) => {
//       const uri = item.resourceUri; // Extract resourceUri from TreeItem

//       if (!uri || !uri.fsPath) {
//         vscode.window.showErrorMessage('Invalid notebook file.');
//         console.log('Invalid notebook file:', item);
//         return;
//       }

//       const confirmed = await vscode.window.showWarningMessage(
//         `Are you sure you want to delete ${path.basename(uri.fsPath)}?`,
//         { modal: true },
//         'Yes'
//       );

//       if (confirmed === 'Yes') {
//         try {
//           fs.unlinkSync(uri.fsPath); // Delete the file
//           const index = this.notebookFiles.findIndex(file => file.fsPath === uri.fsPath);
//           if (index !== -1) {
//             this.notebookFiles.splice(index, 1); // Remove from the list
//             this.treeDataProvider.refresh();
//           }
//           vscode.window.showInformationMessage(`Notebook deleted: ${uri.fsPath}`);
//         } catch (error) {
//           vscode.window.showErrorMessage(`Failed to delete notebook: ${(error as Error).message}`);
//         }
//       }
//     });

//     // Register "Refresh Notebook Explorer" command
//     const refreshNotebookCommand = vscode.commands.registerCommand('intelligent-ide.notebook.refresh', () => {
//       this.notebookFiles.length = 0; // Clear the current file list
//       this.loadNotebooksFromDefaultPath(); // Reload files from the default path
//       this.treeDataProvider.refresh();
//       vscode.window.showInformationMessage('Notebook Explorer refreshed.');
//     });

//     const exportToPdfCommand = vscode.commands.registerCommand('intelligent-ide.notebook.exportToPdf', async (item: vscode.TreeItem) => {
//       const uri = item.resourceUri;
//       if (!uri || !uri.fsPath) {
//         vscode.window.showErrorMessage('Invalid notebook file.');
//         return;
//       }

//       // Read and parse the notebook content
//       const rawContent = fs.readFileSync(uri.fsPath, 'utf8');

//       let parsedContent;
//       try {
//         parsedContent = JSON.parse(rawContent); // Parse the JSON content
//       } catch (error) {
//         vscode.window.showErrorMessage('Failed to parse notebook content.');
//         return;
//       }

//       // Extract and format the content from cells
//       const cells = parsedContent.cells || [];
//       const formattedContent = cells
//         .map((cell: any) => cell.value || '') // Extract the "value" field from each cell
//         .join('\n\n'); // Separate cells with double newlines

//       // Prompt user to select the export path
//       const saveUri = await vscode.window.showSaveDialog({
//         filters: { 'PDF Files': ['pdf'] },
//         saveLabel: 'Export as PDF',
//         defaultUri: vscode.Uri.file(uri.fsPath.replace(/\.ipynb$/, '.pdf'))
//       });

//       if (!saveUri) {
//         vscode.window.showInformationMessage('Export cancelled.');
//         return;
//       }

//       const pdfPath = saveUri.fsPath;

//       // Check if the file already exists
//       if (fs.existsSync(pdfPath)) {
//         const overwrite = await vscode.window.showWarningMessage(
//           `The file ${pdfPath} already exists. Do you want to overwrite it?`,
//           { modal: true },
//           'Yes',
//           'No'
//         );

//         if (overwrite !== 'Yes') {
//           vscode.window.showInformationMessage('Export cancelled.');
//           return;
//         }
//       }

//       try {
//         const PDFDocument = require('pdfkit');
//         const doc = new PDFDocument();
//         const writeStream = fs.createWriteStream(pdfPath);

//         doc.pipe(writeStream);

//         doc.font('Times-Roman'); // Use built-in font
//         doc.text(formattedContent, { align: 'left' }); // Write formatted content to PDF

//         doc.end();

//         writeStream.on('finish', () => {
//           vscode.window.showInformationMessage(`Notebook exported successfully to: ${pdfPath}`);
//         });

//         writeStream.on('error', (error) => {
//           vscode.window.showErrorMessage(`Failed to write PDF: ${error.message}`);
//         });
//       } catch (error) {
//         vscode.window.showErrorMessage(`Failed to export notebook as PDF: ${(error as Error).message}`);
//       }
//     });

//     context.subscriptions.push(newNotebookCommand, deleteNotebookCommand, refreshNotebookCommand, exportToPdfCommand);
//   }

//   private loadNotebooksFromDefaultPath() {
//     if (!fs.existsSync(this.defaultNotebookPath)) {
//       console.error(`Default notebook path does not exist: ${this.defaultNotebookPath}`);
//       return;
//     }

//     const files = fs.readdirSync(this.defaultNotebookPath);
//     files.forEach(file => {
//       if (file.endsWith('.ipynb')) {
//         const filePath = path.join(this.defaultNotebookPath, file);
//         this.notebookFiles.push(vscode.Uri.file(filePath));
//       }
//     });

//     this.treeDataProvider.refresh();
//     console.log(`Loaded notebooks from: ${this.defaultNotebookPath}`);
//   }

//   private enableAutoSave(context: vscode.ExtensionContext) {
//     context.subscriptions.push(
//       vscode.workspace.onDidChangeTextDocument(async (event) => {
//         const document = event.document;
//         if (document.languageId === 'markdown' || document.uri.fsPath.endsWith('.ipynb')) {
//           try {
//             await document.save(); // 自动保存文档
//             console.log(`Document auto-saved: ${document.uri.fsPath}`);
//           } catch (error) {
//             console.error(`Failed to auto-save document: ${error}`);
//           }
//         }
//       })
//     );
//   }
// }

// class NotebookExplorer implements vscode.TreeDataProvider<vscode.TreeItem> {
//   private _onDidChangeTreeData: vscode.EventEmitter<vscode.TreeItem | undefined | void> = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
//   readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | void> = this._onDidChangeTreeData.event;

//   constructor(private notebookFiles: vscode.Uri[]) { }

//   refresh(): void {
//     this._onDidChangeTreeData.fire();
//   }

//   getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
//     return element;
//   }

//   getChildren(element?: vscode.TreeItem): vscode.ProviderResult<vscode.TreeItem[]> {
//     if (!element) {
//       return this.notebookFiles.map(uri => {
//         const treeItem = new vscode.TreeItem(path.basename(uri.fsPath), vscode.TreeItemCollapsibleState.None);
//         treeItem.resourceUri = uri;
//         treeItem.command = {
//           command: 'vscode.openWith',
//           title: 'Open Notebook',
//           arguments: [uri, 'my-notebook']
//         };
//         treeItem.contextValue = 'notebookItem'; // Used for menu item conditions
//         return treeItem;
//       });
//     }
//     return [];
//   }
// }