#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 定义前端项目路径
const frontendPath = path.join(__dirname, 'frontend', 'intelligent-ide');

/**
 * 执行命令并打印输出
 * @param {string} command 要执行的命令
 * @param {string} cwd 工作目录
 */
function runCommand(command, cwd) {
  console.log(`运行命令: ${command}`);
  try {
    execSync(command, { 
      cwd: cwd || process.cwd(), 
      stdio: 'inherit' 
    });
    return 0;
  } catch (error) {
    console.error(`命令执行失败: ${error.message}`);
    return 1;
  }
}

/**
 * 安装前端依赖
 */
function installDependencies() {
  console.log('安装前端依赖...');
  return runCommand('npm install', frontendPath);
}

/**
 * 运行代码检查
 */
function runLinters() {
  console.log('运行代码检查...');
  return runCommand('npm run lint', frontendPath);
}

/**
 * 运行单元测试
 */
function runTests() {
  console.log('运行单元测试...');
  return runCommand('npm run test', frontendPath);
}

/**
 * 构建前端项目
 */
function buildPackage() {
  console.log('构建前端项目...');
  return runCommand('npm run package', frontendPath);
}

/**
 * 生成测试覆盖率报告
 */
function generateCoverageReport() {
  console.log('生成测试覆盖率报告...');
  return runCommand('npm run test', frontendPath);
}

/**
 * 主函数
 */
function main() {
  const args = process.argv.slice(2);
  if (args.length > 0 && args[0] === 'clean') {
    process.exit(cleanBuildArtifacts());
    return;
  }

  console.log('开始构建和测试前端项目...');
  
  if (installDependencies() !== 0) {
    console.error('依赖安装失败');
    process.exit(1);
  }
  
  // 一般不进行代码检查
  // if (runLinters() !== 0) {
  //   console.log('代码检查失败，但继续执行其他任务');
  // }
  
  if (runTests() !== 0) {
    console.log('测试失败，但继续执行其他任务');
  }
  
  try {
    generateCoverageReport();
  } catch (error) {
    console.log('生成覆盖率报告失败，但继续执行其他任务');
  }
  
  if (buildPackage() !== 0) {
    console.error('构建失败');
    process.exit(1);
  }
  
  console.log('前端构建完成！');
}


function cleanBuildArtifacts() {
  console.log('清理前端构建文件...');
  
  // 需要清理的目录
  const pathsToClean = [
    path.join(frontendPath, 'node_modules'),
    path.join(frontendPath, 'out'),
    path.join(frontendPath, 'dist'),
    path.join(frontendPath, '.nyc_output'),
    path.join(frontendPath, 'coverage'),
    path.join(frontendPath, '*.vsix')  // VSCode 扩展包
  ];
  
  for (const pathToClean of pathsToClean) {
    console.log(`删除: ${pathToClean}`);
    try {
      if (fs.existsSync(pathToClean)) {
        // 如果是目录
        if (fs.lstatSync(pathToClean).isDirectory()) {
          fs.rmSync(pathToClean, { recursive: true, force: true });
        } 
        // 如果是通配符模式
        else if (pathToClean.includes('*')) {
          const dir = path.dirname(pathToClean);
          const pattern = path.basename(pathToClean);
          fs.readdirSync(dir)
            .filter(file => new RegExp(`^${pattern.replace('*', '.*')}$`).test(file))
            .forEach(file => {
              fs.rmSync(path.join(dir, file), { force: true });
            });
        }
        // 如果是文件
        else {
          fs.rmSync(pathToClean, { force: true });
        }
      }
    } catch (error) {
      console.error(`删除 ${pathToClean} 失败: ${error.message}`);
    }
  }
  
  console.log('清理完成');
  return 0;
}


// 执行主函数
main(); 