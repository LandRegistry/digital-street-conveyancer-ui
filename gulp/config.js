var path = require('path')

var node_paths = ['node_modules']
if (process.env.NODE_PATH) {
  node_paths.unshift(process.env.NODE_PATH)
}

module.exports = {
  'applicationPath': './conveyancer_ui',
  'sourcePath': './conveyancer_ui/assets/src',
  'destinationPath': './conveyancer_ui/assets/dist',
  'sassPath': 'scss/*.scss',
  'sassIncludePaths': node_paths,
  'localhost': 'localhost:8080'
}
